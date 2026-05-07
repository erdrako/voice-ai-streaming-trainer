# Cloudflare Quick Tunnel

Este modo publica la app local sin dominio propio y sin recursos persistentes en
Cloudflare. Es el camino recomendado para el entrenamiento con presupuesto cero.

## Flujo

```text
Browser publico
  -> URL temporal *.trycloudflare.com
  -> Cloudflare Quick Tunnel
  -> cloudflared en esta maquina
  -> http://host.docker.internal:8000
  -> Docker Compose local
```

## Requisitos

- Docker Desktop.
- La app local corriendo en `http://127.0.0.1:8000`.
- Salida a internet desde tu maquina.

No requiere:

- Dominio.
- Zona DNS en Cloudflare.
- Terraform apply.
- Cuenta de GCP.

## Ejecutar

Desde la raiz del repo:

```powershell
docker compose up -d --build
docker compose -f infra/cloudflare/quick-tunnel/docker-compose.quick-tunnel.yml up
```

El contenedor imprimira una URL similar a:

```text
https://example-random-name.trycloudflare.com
```

Abrir esa URL en el navegador. El frontend, el WebSocket y el backend seguiran
ejecutandose en tu maquina.

## Notas de entrenamiento

- La URL es temporal y cambia cada vez que reinicias el tunnel.
- Mientras `cloudflared` este corriendo, la app queda accesible desde internet.
- Si apagas Docker, la PC o el tunnel, el acceso publico deja de funcionar.
- Este modo demuestra exposicion cloud sin mover la inferencia pesada fuera de
  tu maquina.

## Evolucion natural

Cuando tengas dominio propio en Cloudflare, usa la plantilla:

```text
infra/terraform/cloudflare-named-tunnel
```

Esa version reemplaza la URL temporal por un hostname estable, por ejemplo:

```text
https://voice.example.com
```
