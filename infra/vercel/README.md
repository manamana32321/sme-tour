# Vercel — Terraform IaC

sme-tour Vercel 프로젝트의 선언적 관리. Lifecycle이 sme-tour 앱과 1:1이므로 이 레포에 둠 (amang 레포의 `infra/k8s/` 패턴 동일).

## State Backend

State 파일은 homelab `homelab-tfstate-361769566809` S3 bucket 공유 (`key=sme-tour/vercel.tfstate`). Apply 주체가 `AWS_PROFILE=homelab` 자격증명을 가지면 위치와 무관하게 apply 가능.

## 사전 요구

1. **Vercel API token** — https://vercel.com/account/tokens → Create Token → 권장 scope: Amang team-only, 90일 만료
2. **AWS credentials** — `AWS_PROFILE=homelab` (homelab 레포 `.envrc` 구조 재사용)
3. `.envrc.local` 에 추가:
   ```bash
   export TF_VAR_vercel_api_token="<token>"
   export AWS_PROFILE="homelab"
   export AWS_REGION="ap-northeast-2"
   ```

## 최초 셋업 (import 1회)

```bash
cd infra/vercel
terraform init

# 기존 Vercel 리소스를 state로 편입
terraform import vercel_project.sme_tour prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq
terraform import \
  vercel_project_environment_variable.api_base \
  prj_AM3ftVU9rEv1rhdfpENy4T8l9bDq/14squVanlmQYCB2V

# 무변경 확인
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

## 리소스

| Resource | 설명 |
|---|---|
| `vercel_project.sme_tour` | Next.js · root=frontend · node 24.x · github integration |
| `vercel_project_environment_variable.api_base` | `NEXT_PUBLIC_API_BASE` (production+preview) |

### Custom domain 추가 예시

```hcl
resource "vercel_project_domain" "custom" {
  project_id = vercel_project.sme_tour.id
  domain     = "tour.example.com"
}
```

### env 추가 예시

env 1개일 땐 `vercel_project_environment_variable` 단일 resource 여러 개. 5+ 개 되면 `vercel_project_environment_variables` 복수 resource로 통합 migrate 고려.
