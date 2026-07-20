# Deploy Arbi to a single Alibaba Cloud ECS instance (with Qwen)

This runs the whole stack — web UI, FastAPI backend, Postgres, Qdrant, Redis —
in Docker Compose on one ECS VM. The LLM is **Qwen** via Alibaba Cloud Model
Studio (DashScope); embeddings use DashScope too. nginx serves the web UI and
proxies the API on the same origin, so the browser makes same-origin calls and
the app's Content-Security-Policy holds.

```
Browser ──► ECS :80 (nginx) ──► SPA static files
                          └────► /auth,/chats,/documents,… ──► backend :8000
                                                                   ├─ Postgres
                                                                   ├─ Qdrant
                                                                   ├─ Redis
                                                                   └─ Qwen (Model Studio, HTTPS)
```

---

## 0. Prerequisites
- An Alibaba Cloud account with credits.
- A **Model Studio (DashScope) API key** — see step 2.
- A domain name (optional, only needed for HTTPS in step 8).

## 1. Create the ECS instance
In the Alibaba Cloud console → **ECS → Instances → Create Instance**:
- **Image:** Ubuntu 22.04 LTS (x86_64).
- **Type:** ≥ 2 vCPU / 4 GB RAM is enough with `ENABLE_RERANKER=false` (the default
  in `.env.prod.example`). Choose 8 GB if you turn reranking on.
- **Storage:** 40 GB+ system disk.
- **Public IP:** assign one (or bind an EIP).
- **Security Group — inbound rules:** allow `22/tcp` (SSH, ideally your IP only),
  `80/tcp` (HTTP), and `443/tcp` (only if you set up TLS in step 8).

SSH in:
```bash
ssh root@<ECS_PUBLIC_IP>
```

## 2. Get a Qwen (Model Studio) API key
Console → **Model Studio** (Bailian) → **API-KEY** → create one. It looks like
`sk-…`. Copy it — it goes into `DASHSCOPE_API_KEY`.
- International account → base URL `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (default).
- Mainland-China account → `https://dashscope.aliyuncs.com/compatible-mode/v1`.

## 3. Install Docker + Compose on the ECS
```bash
curl -fsSL https://get.docker.com | sh
docker compose version   # verify the compose plugin is present
```

## 4. Get the code
```bash
apt-get update && apt-get install -y git
git clone https://github.com/aumerez/arbiqwen.git
cd arbiqwen/deploy
```

## 5. Configure secrets
```bash
cp .env.prod.example .env
# JWT secret:
sed -i "s#<openssl-rand-hex-32>#$(openssl rand -hex 32)#" .env
# then edit .env and set DASHSCOPE_API_KEY + POSTGRES_PASSWORD:
nano .env
```
At minimum set: `DASHSCOPE_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET`. Keep
`LLM_PROVIDER=alibaba` and `EMBEDDING_PROVIDER=dashscope`.

## 6. Build and start
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
First build takes a few minutes (installs backend deps + builds the web bundle).
The backend applies DB migrations automatically on start. Watch it come up:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

## 7. Seed the demo data
Once `backend` is healthy:
```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.cli seed
# → Seeded demo data: demo@arbi.dev (user_id=…, project_id=…)
```

**Verify:**
```bash
curl -fsS http://localhost/health      # {"status":"ok"}
```
Open `http://<ECS_PUBLIC_IP>/` in a browser and sign in:
- **Email:** `demo@arbi.dev`
- **Password:** `demo1234`

Send a chat message — it's now answered by **Qwen**. (Change the demo password
after first login for anything non-throwaway: `… exec backend python -m app.cli promote-admin <email>` and manage users as needed.)

## 8. (Optional) HTTPS with a domain
Point an A record at the ECS public IP, then terminate TLS in front of nginx.
Simplest is Caddy as a reverse proxy on :443 → :80, or add certbot to the nginx
service. Alternatively put an Alibaba **SLB** / **CDN** with a managed cert in
front. If you terminate TLS upstream, the app already reads `X-Forwarded-Proto`.

---

## Operations
```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f
# Restart a service
docker compose -f docker-compose.prod.yml restart backend
# Update to latest code
git pull && docker compose -f docker-compose.prod.yml up -d --build
# Stop everything (keeps data volumes)
docker compose -f docker-compose.prod.yml down
# Full reset (DELETES data)
docker compose -f docker-compose.prod.yml down -v
```

## Cost notes
- **ECS**: the VM runs 24/7 — the main fixed cost. Stop it when idle to save.
- **Model Studio (Qwen)**: billed per token on chat/RAG calls against your credits.
- Postgres/Qdrant/Redis run in-container (no managed-service fees on this setup).

## Troubleshooting
- **Login fails / network error**: backend not healthy yet, or seed not run.
  Check `docker compose … logs backend`; re-run the seed (step 7).
- **Chat errors / no answer**: bad or missing `DASHSCOPE_API_KEY`, wrong
  `DASHSCOPE_BASE_URL` for your account region, or no Model Studio credits.
- **Upload rejected**: files over 25 MB are blocked by design (`MAX_UPLOAD_SIZE_MB`).
- **Backend OOM-killed**: reranking is on — set `ENABLE_RERANKER=false` in `.env`
  and `up -d` again, or use a larger instance.
- **502 from nginx**: backend still starting or unhealthy; check its logs.
