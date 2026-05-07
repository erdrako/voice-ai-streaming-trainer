variable "cloudflare_account_id" {
  description = "Cloudflare account id where the tunnel will be created."
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare DNS zone id for the registered domain."
  type        = string
}

variable "cloudflare_zone_name" {
  description = "Registered domain managed by Cloudflare, for example example.com."
  type        = string
}

variable "app_subdomain" {
  description = "Subdomain that will expose the local training app."
  type        = string
  default     = "voice"
}

variable "tunnel_name" {
  description = "Human readable Cloudflare Tunnel name."
  type        = string
  default     = "voice-ai-streaming-trainer"
}

variable "origin_service_url" {
  description = "Service URL that cloudflared can reach from the machine running the tunnel."
  type        = string
  default     = "http://localhost:8000"
}
