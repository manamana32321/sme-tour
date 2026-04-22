terraform {
  required_version = ">= 1.5"

  required_providers {
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }

  # S3 backend — 사용자 개인 homelab tfstate bucket 공유.
  # credentials: AWS_PROFILE=homelab (.envrc)
  backend "s3" {
    bucket = "homelab-tfstate-361769566809"
    key    = "sme-tour/vercel/terraform.tfstate"
    region = "ap-northeast-2"
  }
}

provider "vercel" {
  api_token = var.vercel_api_token
  team      = var.vercel_team_id
}

# SME-Tour Vercel 프로젝트 — 종합설계 팀 프로젝트
#
# scope: Amang team (Hobby 제약으로 personal 이동 불가)
# lifecycle: 학기 종료 후 `terraform destroy` 로 제거 예정
#
# Import 기존 프로젝트 (최초 `terraform apply` 전 1회만):
#   terraform import vercel_project.sme_tour prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq
#   terraform import \
#     vercel_project_environment_variable.api_base \
#     prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq/14squVanlmQYCB2V

resource "vercel_project" "sme_tour" {
  name      = "sme-tour"
  framework = "nextjs"
  team_id   = var.vercel_team_id

  git_repository = {
    type              = "github"
    repo              = "manamana32321/sme-tour"
    production_branch = "main"
  }

  # multi-root 레포: docs/engine/frontend/k8s/infra. Next.js는 frontend/ 에만.
  root_directory = "frontend"
  node_version   = "24.x"

  # Framework default (next build / .next). build/install/dev command 모두 null.
}

resource "vercel_project_environment_variable" "api_base" {
  project_id = vercel_project.sme_tour.id
  team_id    = var.vercel_team_id
  key        = "NEXT_PUBLIC_API_BASE"
  value      = var.api_base
  target     = ["production", "preview"]
  comment    = "K8s ingress에 배포된 sme-tour-engine API base URL"
}
