output "public_hostname" {
  description = "Stable public hostname that routes to the local backend through Cloudflare Tunnel."
  value       = local.public_hostname
}

output "public_url" {
  description = "Browser URL for the local training app once cloudflared is running."
  value       = "https://${local.public_hostname}"
}

output "cloudflared_token" {
  description = "Sensitive token used by cloudflared to connect this machine to the named tunnel."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.voice_ai.token
  sensitive   = true
}

output "cloudflared_run_command_hint" {
  description = "Command shape. Replace TOKEN_FROM_TERRAFORM_OUTPUT with the sensitive cloudflared_token output."
  value       = "cloudflared tunnel --no-autoupdate run --token TOKEN_FROM_TERRAFORM_OUTPUT"
}
