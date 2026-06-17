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
