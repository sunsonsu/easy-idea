# Learning — Deploying easy-idea to GCP (2026-06-17)

Took the app from zero to a **live Cloud Run + Firestore deploy**, provisioned with Terraform.
Project: `get-idea-499708`, region `asia-southeast1`.

End-to-end path:
ChromaDB → Firestore code swap → Terraform-provisioned GCP → image build/push → secrets → working public app.

---

## Terraform

| Concept | Where it bit me |
|---------|------------------|
| **Project must pre-exist** | TF does not create the GCP project → `RESOURCES_NOT_FOUND` until `get-idea-499708` existed |
| **`google_project_service`** | APIs must be enabled before resources that use them → `depends_on` ordering |
| **Resource constraints are real** | Firestore vector index capped at **2048** dims → 3072 rejected |
| **`-target` / split apply** | DB first, then derive embedding dimension, then create the index |
| **`-replace`** | Force a new Cloud Run revision to re-read a `latest` secret |
| **One `depends_on` per resource** | Had to merge two blocks into one |
| **IAM = separate resources** | `google_cloud_run_v2_service_iam_member` ≠ the service; `-replace` dropped the `allUsers` binding → 403 |
| **HCL syntax** | Nested blocks (`replication { auto {} }`) can't be single-line |
| **State holds secrets** | Secret *values* go via gcloud; TF only creates the secret shells |

## gcloud

| Command | What it did |
|---------|-------------|
| `gcloud auth application-default login` | ADC — how Terraform authenticates |
| `gcloud projects create` + billing link | Firestore needs billing even on free tier |
| `gcloud secrets versions add --data-file=-` | Push secret values; `<()` injects a **trailing newline** → token mismatch |
| `gcloud secrets versions access ... \| xxd` | Inspect exact bytes of a secret |
| `gcloud auth configure-docker` | Auth Docker → Artifact Registry |
| `gcloud run services describe --format='value(...)'` | Pull URL / revision / status |
| `gcloud run services add-iam-policy-binding` | The fix — public invoker (`allUsers` + `run.invoker`) |

---

## Biggest lessons (the ones that cost time)

1. **Cloud Run auth ≠ ingress.** `INGRESS_TRAFFIC_ALL` opens the *network*; you still need `roles/run.invoker` for `allUsers` to allow unauthenticated calls.
2. **Newlines in secrets are invisible killers.** Use `printf '%s'`, not `echo` or `<(grep|cut)`, when pushing secret values.
3. **`version="latest"` resolves at container start.** Changing a secret requires a new revision (`terraform apply -replace=...`); the running revision keeps the old value.
4. **Two layers of 403** — platform IAM vs the app's `access_token` auth. `/health` (unauthenticated) isolates which one.
5. **Vector dims must match everywhere** — model output, app config (`EMBEDDING_DIMENSION`), and the Firestore index. The index dimension is permanent; changing it means re-embedding all docs.
6. **MRL embeddings** — Gemini embedding models are Matryoshka: set `output_dimensionality` (1536) to fit Firestore's 2048 cap. COSINE is magnitude-invariant, so no normalization needed.
7. **App auth detail** — header name is `access_token` (not `X-API-Key`), value must equal `APP_API_KEY`; the UI stores it in browser localStorage (`easy_idea_access_token`).

---

## Loose ends

- `token.json` (Google Docs OAuth) — inject as a Secret Manager **volume mount** (it's a file, not env). Deferred.
- Use `:v2`+ image tags on rebuilds, not reuse `:v1` (Cloud Run caches by digest).
- Optional: move `embedding_dimension` to a tfvars variable instead of hardcoded 1536.

---

# Learning — Observability Stack (2026-06-17)

Built full observability for the FastAPI app locally:
**OpenTelemetry SDK → OTel Collector → Jaeger (traces) + Prometheus (metrics) → Grafana (RED dashboard)**

---

## The Pipeline

```
App (FastAPI)
  │
  │  OTLP gRPC :4317
  ▼
OTel Collector
  ├── traces → Jaeger :4317 (internal)
  └── metrics → Prometheus scrapes :8889
                    │
                    ▼
                Grafana :3001
```

---

## Setup Order (don't skip steps)

1. Install OTel packages
2. Write `observability.py` + wire into `main.py`
3. Write Collector config (`otel-collector-config.yaml`)
4. Write Prometheus scrape config (`prometheus.yml`)
5. Write Grafana provisioning files (datasources + dashboard JSON)
6. Write `docker-compose.observability.yml`
7. `docker compose up -d` (backends first)
8. Start app with `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317`
9. Send traffic, wait 20–30s, open Grafana

---

## Packages

```
opentelemetry-sdk==1.39.1
opentelemetry-exporter-otlp-proto-grpc==1.39.1
opentelemetry-semantic-conventions==0.60b1
opentelemetry-instrumentation-fastapi==0.60b1   # auto-instruments every route
opentelemetry-instrumentation-httpx==0.60b1     # auto-instruments outbound HTTP calls
```

`instrumentation-*` version must match `semantic-conventions` version — mismatch = wrong metric names = empty Grafana panels.

---

## Key Lessons

| Concept | Detail |
|---------|--------|
| **Fail-soft** | OTel uses async BatchSpanProcessor — Collector down = app still works, data dropped silently |
| **Resource** | `Resource.create({"service.name": "..."})` is how Jaeger knows which service sent the trace |
| **`instrument_app(app)` timing** | Must call after `FastAPI()` is created, before routes are defined |
| **Collector image** | Use `otel/opentelemetry-collector-contrib`, NOT base — base missing Prometheus exporter |
| **Jaeger OTLP** | Must set `COLLECTOR_OTLP_ENABLED=true` — default protocol is old Thrift, not OTLP |
| **Prometheus pulls** | Prometheus scrapes Collector's `:8889` every 10s — it does NOT receive pushed data |
| **`rate()` needs time** | `rate()` calculates from 2+ data points — always zero until 2 scrapes complete (~20s) |
| **`service.pipelines` required** | Without it, Collector receives data but forwards nothing — silent failure |
| **Metric name gotcha** | Verify real names at `http://localhost:8889/metrics` before writing PromQL. This app: `http_server_duration_milliseconds_count` (old semconv), NOT `http_server_request_duration_seconds` (new semconv) |
| **Wrong PromQL** | Empty panel, zero error message — hardest bug to spot |

---

## RED Dashboard Queries (this app)

```promql
# Rate (req/s)
sum(rate(http_server_duration_milliseconds_count[1m])) by (http_target)

# Error rate (5xx)
sum(rate(http_server_duration_milliseconds_count{http_status_code=~"5.."}[1m]))

# Latency p95 (ms)
histogram_quantile(0.95, sum(rate(http_server_duration_milliseconds_bucket[5m])) by (le))
```

Labels on this app's metrics: `http_status_code`, `http_target` (not `http_route`/`http_response_status_code`).

---

## Why "Add Loki Datasource" in Grafana Logs Tab

Grafana handles **three signal types** separately:

| Signal | Backend | Status |
|--------|---------|--------|
| Metrics | Prometheus | ✅ set up |
| Traces | Jaeger | ✅ set up |
| **Logs** | **Loki** | ❌ not set up |

We wired metrics + traces but never added Loki. Grafana's Explore → Logs tab expects a Loki datasource — without it, the tab is empty and says "add Loki datasource."

**To add logs later:**
1. Run Loki container (`grafana/loki:3.0.0`)
2. Run Promtail (reads log files, ships to Loki) OR add `loki` exporter to OTel Collector
3. Add Loki datasource to `datasources.yml` (`url: http://loki:3100`)
4. Grafana Logs tab works

Loki is optional for resume/demo — metrics + traces already cover the RED method. Add Loki when you want log correlation (click a trace → see logs for that request).

---

## Files Created

```
src/app/core/observability.py
observability/
├── otel-collector-config.yaml
├── prometheus.yml
└── grafana/provisioning/
    ├── datasources/datasources.yml
    └── dashboards/
        ├── dashboards.yml
        └── red-dashboard.json
docker-compose.observability.yml
```

## Run Commands

```bash
docker compose -f docker-compose.observability.yml up -d
OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317 python src/app/main.py

# Access
# Grafana:    http://localhost:3001  → easy-idea RED dashboard
# Jaeger:     http://localhost:16686
# Prometheus: http://localhost:9090
```
