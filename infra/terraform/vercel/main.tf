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

  # Framework default (next build / .next). build/install/dev command 모두 null.

  # 실제 Vercel 설정 반영 — drift 방지.
  # deployment_type = "none" 유지해야 preview URL 팀원 공유 가능
  # (provider default가 standard_protection이라 명시 필요).
  vercel_authentication = {
    deployment_type = "none"
  }

  # Vercel Pro 기본 skew protection.
  skew_protection = "12 hours"

  # OIDC: Vercel builds에 발급되는 short-lived token. team-level 기본.
  oidc_token_config = {
    enabled     = true
    issuer_mode = "team"
  }
}

resource "vercel_project_environment_variable" "api_base" {
  project_id = vercel_project.sme_tour.id
  team_id    = var.vercel_team_id
  key        = "NEXT_PUBLIC_API_BASE"
  value      = var.api_base
  target     = ["production"]
  sensitive  = false
}
