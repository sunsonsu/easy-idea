variable "project_id" {
  description = "GCP project ID (must already exist with billing enabled)"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run + Artifact Registry"
  type        = string
  default     = "asia-southeast1"
}

variable "firestore_location" {
  description = "Firestore location — PERMANENT after first apply, cannot be changed"
  type        = string
  default     = "asia-southeast1"
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "v1"
}

variable "drive_folder_id" {
  description = "Google Drive folder ID for saving generated docs"
  type        = string
  default     = ""
}

variable "embedding_dimension" {
  description = "Embedding vector length — must match settings.EMBEDDING_DIMENSION. Firestore caps at 2048."
  type        = number
  default     = 1536
}

variable "collection_name" {
  description = "Firestore collection holding the vector knowledge base"
  type        = string
  default     = "easy_idea_kb"
}
