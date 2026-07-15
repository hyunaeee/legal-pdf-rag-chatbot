variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Google Cloud region for regional resources."
  type        = string
  default     = "asia-northeast3"
}

variable "service_name" {
  description = "Cloud Run service name."
  type        = string
  default     = "enterprise-policy-agent"
}

variable "repository_id" {
  description = "Artifact Registry repository ID."
  type        = string
  default     = "enterprise-ai"
}

variable "container_image" {
  description = "Fully qualified container image URI."
  type        = string
}

variable "vertex_model" {
  description = "Vertex AI Gemini model used by the API."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "allow_unauthenticated" {
  description = "Whether to grant allUsers the Cloud Run invoker role."
  type        = bool
  default     = false
}

variable "otel_enabled" {
  description = "Enable OTLP export from the service."
  type        = bool
  default     = false
}

variable "otel_endpoint" {
  description = "OTLP gRPC collector endpoint."
  type        = string
  default     = ""
}

variable "min_instances" {
  description = "Minimum Cloud Run instances."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances."
  type        = number
  default     = 5
}
