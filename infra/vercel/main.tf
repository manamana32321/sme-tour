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
  key        = "NEXT_PUBLIC_API_BASE"
  value      = var.api_base
  target     = ["production", "preview"]
  comment    = "K8s ingress에 배포된 sme-tour-engine API base URL"
}
