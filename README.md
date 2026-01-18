# Jarvis Web (Fly.io)

Proyecto listo para desplegar en **Fly.io** como webapp.

## Qué hace
- UI web tipo chat (FastAPI)
- Genera un plan JSON con un LLM (HuggingFace InferenceClient)
- Ejecuta acciones server-side usando Playwright:
  - Spotify: buscar y reproducir
  - WhatsApp: buscar chat y mandar mensaje
- Recordatorios/alarmas: se guardan en SQLite en /data y se emiten como eventos

## Requisitos
- Cuenta + CLI: `flyctl`

## Variables de entorno (Fly Secrets)
- `HF_TOKEN` (requerido si PLANNER_MODE=llm)
- `HF_PROVIDER` (default: fireworks-ai)
- `HF_MODEL` (default: openai/gpt-oss-120b)
- `API_BEARER_TOKEN` (opcional: protege /api/* y /auth/*)
- `PLANNER_MODE` (llm|rules)
- `PW_HEADLESS` (1|0)

## Deploy en Fly.io
1) En este folder:
```bash
flyctl auth login
flyctl launch  # detecta el Dockerfile
```
2) Crea un volumen (persistencia):
```bash
flyctl volumes create data --size 3 --region iad
```
3) Configura secrets:
```bash
flyctl secrets set HF_TOKEN="..." API_BEARER_TOKEN="una_clave_larga"
```
4) Deploy:
```bash
flyctl deploy
```

## Login WhatsApp/Spotify
Abre en el navegador:
- `https://<tu-app>.fly.dev/auth/whatsapp.png`
- `https://<tu-app>.fly.dev/auth/spotify.png`

Si aparece QR/login, inicia sesión. La sesión se persiste en `/data/browser/...`.

## Notas
- Automatización web es frágil: si WhatsApp/Spotify cambian UI, puede requerir ajustar selectores en `app/actions/*`.
