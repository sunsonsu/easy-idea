provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs before creating resources that depend on them.
resource "google_project_service" "firestore" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_run_v2_service" "get-idea-run" {
  name                = "get-idea-service"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  scaling {
    max_instance_count = 1
  }

  template {
    service_account = google_service_account.run_sa.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/easy-idea/app:${var.image_tag}"

      ports {
        container_port = 8080
      }

      # --- non-secret config (plain env) ---
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_DRIVE_FOLDER_ID"
        value = var.drive_folder_id
      }

      # --- secrets (pulled from Secret Manager at runtime) ---
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "APP_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.run,
    google_secret_manager_secret_iam_member.run_gemini,
    google_secret_manager_secret_iam_member.run_app_key,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.get-idea-run.name
  location = google_cloud_run_v2_service.get-idea-run.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_firestore_database" "get-idea-db" {
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

resource "google_firestore_index" "kb_embedding" {
  database    = google_firestore_database.get-idea-db.name
  collection  = var.collection_name
  query_scope = "COLLECTION"

  fields {
    field_path = "embedding"

    vector_config {
      dimension = var.embedding_dimension
      flat {}
    }
  }
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "easy-idea"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifactregistry]
}

#Secrets
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "app_api_key" {
  secret_id = "app-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "user_token_json" {
  secret_id = "user-token-json"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

# --- Dedicated runtime identity for Cloud Run ---
resource "google_service_account" "run_sa" {
  account_id   = "easy-idea-run"
  display_name = "easy-idea Cloud Run runtime"
}

# Firestore access (vector store)
resource "google_project_iam_member" "run_datastore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

# Read the three secrets
resource "google_secret_manager_secret_iam_member" "run_gemini" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "run_app_key" {
  secret_id = google_secret_manager_secret.app_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "run_token" {
  secret_id = google_secret_manager_secret.user_token_json.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_sa.email}"
}
