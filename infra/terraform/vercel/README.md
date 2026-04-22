# Vercel — Terraform IaC

sme-tour Vercel 프로젝트의 선언적 관리. amang 레포 `infra/terraform/vercel/` 패턴 동일.

## 구조 원칙

| 리소스 타입 | 위치 | 근거 |
|---|---|---|
| K8s Application CR (ArgoCD) | homelab/k8s/argocd/ | cluster 자원은 homelab cluster 소유 |
| K8s manifest (소스) | 앱 레포/k8s/ | 팀 개발자 PR 접근성 |
| **Vercel Terraform** | **앱 레포/infra/terraform/vercel/** | **lifecycle = 앱 lifecycle, 학기 종료 시 destroy** |

## State Backend

S3 `homelab-tfstate-361769566809`, key `sme-tour/vercel/terraform.tfstate`. Code 위치와 backend 위치 독립 — AWS_PROFILE=homelab 자격증명만 있으면 apply 가능.

## 사전 요구

### 1. Vercel API token

옵션 A — **amang 토큰 재사용** (권장, 간편):
- `~/amang-worktrees/main/infra/terraform/vercel/terraform.tfvars` 에 있는 값 복사
- 사용자 개인 token이라 모든 team scope 접근 (Amang 포함)

옵션 B — **별도 token 발급** (엄격):
- https://vercel.com/account/tokens → Create Token → Amang team scope, 90일 만료

### 2. `terraform.tfvars` 작성 (gitignored)

```bash
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars 편집:
#   vercel_api_token = "vcp_..."
#   vercel_team_id   = "team_aDiKenl6xun665nVWV49POd4"
```

### 3. AWS credentials (state backend)

```bash
# 앱 레포 루트 .envrc 또는 .envrc.local
export AWS_PROFILE="homelab"
export AWS_REGION="ap-northeast-2"
```

`direnv allow`.

## 최초 셋업 (import 1회)

```bash
cd infra/terraform/vercel
terraform init

# 기존 Vercel 리소스를 state로 편입
terraform import vercel_project.sme_tour prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq
terraform import \
  vercel_project_environment_variable.api_base \
  prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq/14squVanlmQYCB2V

# 무변경 확인 — drift 있으면 코드 조정
terraform plan
```

## 일상 운영

```bash
terraform plan   # drift 체크
terraform apply  # 변경 적용 (-auto-approve 금지)
```

## 학기 종료 후 제거

```bash
terraform destroy
```

이후 sme-tour 레포 archive.

## 관리 리소스

| Resource | 설명 |
|---|---|
| `vercel_project.sme_tour` | Next.js · root=frontend · github integration |
| `vercel_project_environment_variable.api_base` | `NEXT_PUBLIC_API_BASE` (production+preview) |

### Custom domain 추가 예시

```hcl
resource "vercel_project_domain" "custom" {
  project_id = vercel_project.sme_tour.id
  team_id    = var.vercel_team_id
  domain     = "tour.example.com"
}
```

### env 추가 예시

env 1개일 땐 `vercel_project_environment_variable` 단일 resource 여러 개. 5+ 개 되면 `vercel_project_environment_variables` 복수 resource로 통합 migrate 고려.
