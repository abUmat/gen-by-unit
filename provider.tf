terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket  = "gen_by_unit-tfstate"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
    profile = "terraform"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "terraform"
  default_tags {
    tags = {
      Env = "prd"
      Prj = "hobby"
    }
  }
}

variable "aws_region" {
  description = "region"
  type        = string
  default     = "us-east-1"
}

variable "python_runtime" {
  description = "python_runtime"
  type        = string
  default     = "python3.10"
}
