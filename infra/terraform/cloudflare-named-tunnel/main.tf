terraform {
  required_version = ">= 1.6.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.19"
    }
  }
}

provider "cloudflare" {
  # Terraform lee el token desde la variable de entorno CLOUDFLARE_API_TOKEN.
  # Esto evita escribir secretos en archivos versionados.
}

locals {
  # Hostname publico estable que reemplaza al *.trycloudflare.com temporal.
  public_hostname = "${var.app_subdomain}.${var.cloudflare_zone_name}"
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "voice_ai" {
  account_id = var.cloudflare_account_id
  name       = var.tunnel_name
  config_src = "cloudflare"
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "voice_ai" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.voice_ai.id
}

resource "cloudflare_dns_record" "voice_ai" {
  zone_id = var.cloudflare_zone_id
  name    = var.app_subdomain
  content = "${cloudflare_zero_trust_tunnel_cloudflared.voice_ai.id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "voice_ai" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.voice_ai.id

  config = {
    ingress = [
      {
        hostname = local.public_hostname
        service  = var.origin_service_url
      },
      {
        service = "http_status:404"
      }
    ]
  }
}
