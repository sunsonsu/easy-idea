# Firestore Vector Search — Setup

This app's vector store is **Google Cloud Firestore** (Native mode) using the
built-in `find_nearest` vector search. The code (`src/app/services/chroma_service.py`)
**cannot** create the required vector index — you must create it out-of-band
(gcloud or Terraform) before vector queries (`query_knowledge`) will work.

## 1. Authenticate (Application Default Credentials)

The Firestore client uses ADC. For local dev:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

On Cloud Run, ADC is provided automatically by the runtime service account
(grant it the `roles/datastore.user` role). No `token.json` is involved — that
file is only for the Google Docs integration.

Relevant env vars (see `src/app/core/config.py`):

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export FIRESTORE_DATABASE="(default)"          # or a named database
export FIRESTORE_COLLECTION=easy_idea_kb       # defaults to CHROMA_COLLECTION_NAME
```

## 2. Enable the API

```bash
gcloud services enable firestore.googleapis.com --project YOUR_PROJECT_ID
```

## 3. Create the Firestore database (NATIVE mode)

Vector search requires **Native mode** (not Datastore mode):

```bash
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native \
  --project=YOUR_PROJECT_ID
```

(Use `--database=YOUR_DB` and set `FIRESTORE_DATABASE` to match if you don't use
the `(default)` database.)

## 4. Derive the embedding dimension — DO NOT hardcode it

The vector index requires the exact embedding dimension. **Do not guess
768/1536/3072** — it depends on `GEMINI_EMBEDDING_MODEL` (and may be configurable
per request). Derive it empirically from the same code path the app uses:

```bash
# from the repo root, in the project's virtualenv
GEMINI_API_KEY=$YOUR_GEMINI_API_KEY .venv/bin/python -c "\
import sys; sys.path.insert(0,'src'); \
from app.rag.embeddings import embed_query; \
print(len(embed_query('test')))"
```

The printed number is your `--dimension` / `vector_config.dimension`. Plug that
exact value into step 5 below.

## 5. Create the single-field vector index on `embedding`

`find_nearest` will fail with `FAILED_PRECONDITION` until this index exists.
The data model writes one document per chunk with an `embedding` field of type
`Vector` (see `upsert_knowledge`), and queries use `DistanceMeasure.COSINE`.

### Option A — gcloud

Replace `<DIM>` with the number from step 4:

```bash
gcloud firestore indexes composite create \
  --project=YOUR_PROJECT_ID \
  --database="(default)" \
  --collection-group=easy_idea_kb \
  --query-scope=COLLECTION \
  --field-config=field-path=embedding,vector-config='{"dimension":"<DIM>","flat":"{}"}'
```

> The `flat` config selects a brute-force (FLAT) vector index, which is the
> currently supported index type for Firestore `find_nearest`.

### Option B — Terraform (`google_firestore_index`)

For the Cloud Run + Firestore Terraform you're about to practice. Replace
`var.embedding_dimension` with the value from step 4 (or pass it as a variable):

```hcl
variable "embedding_dimension" {
  description = "Embedding dimension from len(embed_query('test')) — see FIRESTORE_SETUP.md step 4"
  type        = number
  # No default on purpose: derive it empirically and set it explicitly.
}

resource "google_firestore_index" "kb_embedding_vector" {
  project     = var.project_id
  database    = "(default)"
  collection  = "easy_idea_kb"
  query_scope = "COLLECTION"

  fields {
    field_path = "embedding"

    vector_config {
      dimension = var.embedding_dimension

      flat {}
    }
  }
}
```

## 6. (Optional) Index for `list_daily_trends`

`list_daily_trends` filters on `metadata.type == "daily_trend"` with a `limit`.
A single-field equality filter is served by Firestore's automatic single-field
indexing, so no extra composite index is normally required. If Firestore returns
a `FAILED_PRECONDITION` with an index-creation link for that query, follow the
link (it pre-fills the exact index definition).

## Notes

- The app boots even if Firestore / ADC is unavailable: `query_knowledge` and
  `list_*` return empty, `get_collection_stats` returns `status: "unavailable"`.
  Vector results only appear once steps 1–5 are complete.
- `delete_collection` batch-deletes every document in the collection (Firestore
  has no server-side collection drop).
