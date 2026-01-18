#!/usr/bin/env sh
set -eu

cat <<'TXT'
Pasos sugeridos (Fly.io):

1) Login
   flyctl auth login

2) En el directorio del proyecto:
   flyctl launch
   - Si ya tienes fly.toml en el repo, puedes conservarlo.

3) Crear volumen persistente (necesario para sesiones de navegador + SQLite):
   flyctl volumes create data --size 3 --region <tu-region>

4) Configurar secretos del LLM (ejemplo Fireworks via huggingface_hub provider):
   flyctl secrets set HF_TOKEN="..." HF_PROVIDER="fireworks-ai" HF_MODEL="openai/gpt-oss-120b"

   (Opcional) Proteger la API con un token:
   flyctl secrets set API_BEARER_TOKEN="una_clave_larga"

5) Deploy
   flyctl deploy

6) Abrir la app y loguear WhatsApp/Spotify:
   - Abre /auth/whatsapp.png (muestra QR o estado)
   - Abre /auth/spotify.png (muestra estado)
   La sesion se guarda en /data.
TXT
