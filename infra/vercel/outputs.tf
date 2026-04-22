output "project_id" {
  description = "Vercel project ID"
  value       = vercel_project.sme_tour.id
}

output "default_url" {
  description = "Vercel 기본 배포 URL"
  value       = "https://sme-tour.vercel.app"
}
