# Cloudflare Named Tunnel Terraform

Esta carpeta es la version profesional del Quick Tunnel. Requiere un dominio
registrado y delegado a Cloudflare.

## Que crea

- Un Cloudflare Tunnel nombrado.
- Un DNS record CNAME que apunta al tunnel.
- Una regla de ingress que envia trafico a tu backend local.
- Outputs con el hostname publico y el comando sugerido para correr
  `cloudflared`.

## Que no crea

- No crea dominio.
- No levanta Docker Compose.
- No mueve Ollama, STT ni TTS a la nube.
- No crea recursos en GCP.

## Flujo

```text
Browser
  -> https://voice.example.com
  -> Cloudflare DNS
  -> Cloudflare Tunnel
  -> cloudflared en tu PC
  -> http://localhost:8000
  -> FastAPI + Ollama + STT + TTS local
```

## Variables

Copiar el ejemplo:

```powershell
Copy-Item infra/terraform/cloudflare-named-tunnel/terraform.tfvars.example `
  infra/terraform/cloudflare-named-tunnel/terraform.tfvars
```

Completar:

```hcl
cloudflare_account_id = "..."
cloudflare_zone_id    = "..."
cloudflare_zone_name  = "example.com"
app_subdomain         = "voice"
origin_service_url    = "http://localhost:8000"
```

## Aplicar

Solo ejecutar esto si ya tenes dominio en Cloudflare:

```powershell
cd infra/terraform/cloudflare-named-tunnel
terraform init
terraform plan
terraform apply
```

Despues correr `cloudflared` en tu maquina usando el token sensible generado
por Terraform. El output `cloudflared_run_command_hint` muestra el formato del
comando, pero no imprime el token completo por seguridad.

## Costos

Cloudflare Tunnel esta disponible en todos los planes, pero revisar siempre los
limites vigentes de Cloudflare antes de usarlo fuera de entrenamiento. Esta
plantilla no crea recursos de computo cloud: el procesamiento sigue en tu PC.

## Seguridad

- No commitear `terraform.tfvars`.
- No commitear tokens de Cloudflare.
- Si expones la app durante una demo publica, detener el tunnel cuando termines.
- Considerar Cloudflare Access antes de compartir la URL con terceros.
