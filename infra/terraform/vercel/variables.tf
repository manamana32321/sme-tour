variable "vercel_api_token" {
  description = "Vercel API token. terraform.tfvars 에 설정 (gitignored). amang 레포의 동일 토큰 재사용 가능."
  type        = string
  sensitive   = true
}

variable "vercel_team_id" {
  description = "Vercel team id. 현재 Amang (Vercel Hobby 정책상 personal 이동 불가, 학기 후 destroy)."
  type        = string
  default     = "team_aDiKenl6xun665nVWV49POd4"
}

variable "api_base" {
  description = "Public API base URL → NEXT_PUBLIC_API_BASE. K8s ingress sme-tour-engine."
  type        = string
  default     = "https://api.sme-tour.json-server.win"
}
