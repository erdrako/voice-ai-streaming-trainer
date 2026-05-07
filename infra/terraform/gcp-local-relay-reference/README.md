# GCP Local Relay Reference

Esta carpeta existe para estudiar la alternativa GCP sin crear recursos reales.

## Idea conceptual

GCP no tiene un equivalente directo a Cloudflare Quick Tunnel para publicar tu
PC local gratis y sin dominio. La alternativa mas cercana seria usar una VM
pequena como relay:

```text
Browser
  -> GCP relay VM
  -> reverse tunnel hacia tu PC
  -> Docker Compose local
```

La VM no haria inferencia. Solo reenviaria trafico hacia tu maquina.

## Por que no lo aplicamos ahora

- Requiere billing activo.
- Aunque exista free tier para `e2-micro`, una mala region, disco, IP, trafico o
  recurso extra puede generar costo.
- No aporta tanto como Cloudflare para el objetivo actual de presupuesto cero.

## Uso recomendado en entrevista

Explicarlo como un `ExposureProvider` alternativo:

```text
cloudflare_quick_tunnel       -> funcional sin dominio
cloudflare_named_tunnel       -> funcional con dominio + Terraform
gcp_local_relay_reference     -> referencia conceptual sin aplicar
gcp_cloud_run_future          -> migracion futura cloud-native
```

## Terraform de esta carpeta

Los archivos `.tf` no crean recursos cloud. Solo producen outputs descriptivos
para que la estructura sea visible sin riesgo de costos.
