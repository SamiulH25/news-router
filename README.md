# News Router

A local-first household news router. Follow RSS feeds, tag them with topics and keywords, and read a clean feed in the browser. Get push notifications when your morning and evening briefs are ready.

## Features

- Multi-user accounts with simple username/password auth
- RSS feed ingestion with deduplication
- Per-user topics with keyword filtering
- Web feed grouped by topic (last 12 hours of stories)
- In-app article reader (content extraction via trafilatura)
- Scheduled morning and evening push via self-hosted [ntfy](https://ntfy.sh/)
- OPML import/export
- Docker Compose for one-command local deployment

## Quick start

From the project root:

```bash
npm install          # once — installs root orchestration scripts
npm run start:dev    # local dev (API + UI + ntfy, hot reload)
npm run start:prod   # production (Docker Compose)
```

**Windows shortcut:**

```powershell
.\run.ps1            # same as npm run start:dev
.\run.ps1 -Docker    # same as npm run start:prod
```

Open the **Web UI** URL printed in the terminal (ports are chosen automatically from a free range). Register the first account — it becomes admin.

| Command | What it does |
|---------|----------------|
| `npm run start:dev` | Picks free API/UI ports (8000–8099 / 5173–5272), starts stack + ntfy |
| `npm run start:prod` | Full stack via `docker compose up --build` |
| `npm run start:prod:local` | Built frontend + uvicorn without Docker |

### Services

| Service  | URL                      |
|----------|--------------------------|
| Web UI   | http://localhost:5173    |
| API      | http://localhost:8000    |
| ntfy     | http://localhost:2586    |

## LAN access (household devices)

1. Find your server's LAN IP (e.g. `192.168.1.50`).
2. Allow ports **5173**, **8000**, and **2586** through Windows Firewall.
3. Other devices open **http://192.168.1.50:5173**.
4. Set in `.env` / `docker-compose.yml`:
   - `CORS_ORIGINS=http://192.168.1.50:5173,...`
   - `APP_BASE_URL=http://192.168.1.50:5173`
5. Restart: `docker compose up -d`

## Push notifications (ntfy)

1. Install the ntfy app on your phone ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)).
2. Add server: `http://<server-ip>:2586` (or use default ntfy.sh with self-hosted topic — subscribe to your private topic from Settings).
3. In News Router **Settings**, copy your private topic name and subscribe in the app.
4. Digests go out at **7:00 AM** and **7:00 PM** server time with unread stories from the last 12 hours.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
mkdir data
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Workflow

1. **Register** each household member.
2. **Add feeds** (Settings → Feeds) — paste RSS URLs or import OPML.
3. **Create topics** (Settings → Topics) — name them, add keywords, link feeds.
4. Articles matching keywords from linked feeds appear in **Today's Feed**.
5. Tap an article to read in-app, or open the original source.

### Keyword matching

- Keywords are comma-separated (e.g. `climate, energy, solar`).
- Matching is case-insensitive substring search on title + summary.
- Empty keywords = all articles from linked feeds match.

## Cloud deployment (later)

Same Docker Compose stack on a VPS:

1. Swap `DATABASE_URL` to PostgreSQL.
2. Add Caddy/Traefik for HTTPS.
3. Point a domain at the server.
4. Run ntfy on a subdomain with TLS.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, feedparser, trafilatura, APScheduler
- **Frontend:** SvelteKit, Tailwind CSS
- **Push:** ntfy
- **Database:** SQLite (local) / PostgreSQL (production)

## License

MIT
