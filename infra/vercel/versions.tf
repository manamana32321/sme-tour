terraform {
  required_version = ">= 1.5"

  required_providers {
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }

  # State는 사용자 개인 homelab tfstate S3 bucket 공유.
  # code location(앱 레포)과 state backend(homelab bucket)는 독립 — apply 주체가
  # AWS_PROFILE=homelab 자격증명을 가지면 OK.
  backend "s3" {
    bucket = "homelab-tfstate-361769566809"
    key    = "sme-tour/vercel.tfstate"
    region = "ap-northeast-2"
  }
}

provider "vercel" {
  api_token = var.vercel_api_token
  team      = var.amang_team_id
}
