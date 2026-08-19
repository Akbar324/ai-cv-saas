provider "aws" {
  region = "me-central-1"

  default_tags {
    tags = {
      Project   = "ai-cv-saas"
      Purpose   = "terraform-state"
      ManagedBy = "Terraform"
    }
  }
}
