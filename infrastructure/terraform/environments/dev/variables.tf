variable "project_name" {
  description = "Project name used for AWS resource naming and tagging."
  type        = string
  default     = "ai-cv-saas"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either dev or prod."
  }
}

variable "aws_region" {
  description = "AWS region used for project resources."
  type        = string
  default     = "me-central-1"
}
