terraform {
  required_version = ">= 1.15.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "ai-cv-saas-terraform-state-874348038937-me-central-1"
    key          = "bootstrap/terraform.tfstate"
    region       = "me-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
