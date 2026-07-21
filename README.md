# Anthology

A self-hostable read-later app. Import your Pocket/Instapaper export, extract
clean article text, and tag, full-text search, and highlight your own library.

## Tech stack

- **Frontend:** React + TypeScript (Vite), Tailwind CSS
- **Backend:** Python + FastAPI (3 services: gateway, extraction, search)
- **Database:** PostgreSQL (full-text search)
- **Packaging:** Docker Compose

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:5173 and click **"Try the demo (dev login)"**.
Import a sample file from `samples/` to see the full pipeline.
