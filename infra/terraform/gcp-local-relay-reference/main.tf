terraform {
  required_version = ">= 1.6.0"
}

locals {
  provider_name = "gcp_local_relay_reference"

  # Esta lista describe los componentes que existiran si algun dia se decide
  # implementar la variante GCP. No se declaran recursos reales a proposito.
  conceptual_components = [
    "free-tier-aware e2-micro relay VM",
    "minimal firewall rules",
    "least-privilege service account",
    "reverse tunnel from local workstation to relay VM",
    "future replacement by Cloud Run or GKE when budget exists"
  ]
}
