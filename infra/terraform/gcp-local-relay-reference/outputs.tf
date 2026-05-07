output "provider_name" {
  description = "Conceptual exposure provider name."
  value       = local.provider_name
}

output "conceptual_components" {
  description = "Non-applied components that would be needed for a GCP relay implementation."
  value       = local.conceptual_components
}

output "cost_safety_note" {
  description = "Why this reference intentionally avoids cloud resources."
  value       = "This Terraform reference creates no GCP resources to avoid accidental costs."
}
