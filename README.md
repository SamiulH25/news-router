# News Router

**News Router** is a self-hosted news reader for households and small teams. It pulls stories from RSS feeds, organizes them into topics you define, and delivers a focused daily edition in the browser—with optional morning and evening push briefings.

Your data stays on your server. No ads, no algorithmic feed, no third-party tracking.

---

## Why News Router

- **One place for your sources** — CBC, BBC, NPR, regional papers, niche blogs: add any RSS feed or pick from a curated catalog at signup.
- **Topics that match how you think** — Group feeds into channels (Headlines, Politics, Local) and filter with keywords.
- **Edition, not endless scroll** — Stories from the last 12 hours, ranked and grouped so you can finish the news and move on.
- **Reels or list** — Swipe through stories with tap-to-read sections, or browse a traditional list view.
- **Push when it matters** — Morning and evening digests via [ntfy](https://ntfy.sh/) to your phone or desktop.
- **Multi-user** — Separate accounts for everyone at home; each person gets their own feeds, topics, and read state.

---

## Features

| | |
|---|---|
| **Feed ingestion** | RSS/Atom with automatic discovery, deduplication, and parallel polling |
| **Onboarding** | Pre-configured outlets by country; choose what to follow at setup |
| **Reader** | In-app reading with full-article extraction |
| **Personalization** | Read/unread state, “less like this,” optional ranking signals |
| **Import / export** | OPML for feeds |
| **Notifications** | Scheduled digests through a self-hosted ntfy instance |
| **Admin** | First registered user is admin; registration can be disabled in production |

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (recommended)
- Or: Node.js 20+, Python 3.11+ for manual deployment
- A server or always-on home machine with outbound HTTPS (for fetching feeds)

---

## Quick start (production)

### 1. Clone and configure

```bash
git clone https://github.com/SamiulH25/news-router.git
cd news-router
cp .env.example .env
```

Edit `.env` before first run:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | **Required.** Long random string for session signing |
| `APP_BASE_URL` | Public URL users open (e.g. `https://news.example.com`) |
| `CORS_ORIGINS` | Same origin(s) as `APP_BASE_URL`, comma-separated |
| `ALLOW_REGISTRATION` | Set `false` after creating accounts (via compose env) |
| `DATABASE_URL` | SQLite by default; use PostgreSQL for heavier use |
| `NTFY_BASE_URL` | URL of your ntfy server for push |

### 2. Start the stack

```bash
docker compose --profile prod up -d --build
```

Open **http://localhost:3000** (or your configured `APP_BASE_URL`).

### 3. Create your account

Register the first user — this account receives admin access. Complete onboarding: timezone, first topic, and news outlets by region.

### 4. Pull your first edition

Open **Read**, tap **Pull latest**, and stories from your sources appear within the edition window (default: last 12 hours).

---

## Push notifications

News Router sends digest notifications through ntfy (included in the Docker stack on port 2586).

1. Install the [ntfy app](https://ntfy.sh/) on your devices.
2. In **Settings**, copy your private topic name.
3. Subscribe to that topic in the app, pointing at your ntfy server URL.
4. Digests arrive at the morning and evening times set in your account (default 7:00 and 19:00 in your timezone).

For production, put ntfy behind HTTPS on a subdomain (e.g. `ntfy.example.com`) and update `NTFY_BASE_URL`.

---

## Configuration reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | Session encryption key (change in production) |
| `DATABASE_URL` | SQLite file | Database connection string |
| `CORS_ORIGINS` | localhost | Allowed browser origins |
| `APP_BASE_URL` | `http://localhost:5173` | Canonical app URL for links |
| `NTFY_BASE_URL` | `http://localhost:2586` | ntfy server for push |
| `FEED_POLL_INTERVAL_MINUTES` | `45` | Background poll interval |
| `FEED_WINDOW_HOURS` | `12` | How far back the edition looks |
| `DIGEST_MORNING_HOUR` | `7` | Default morning digest hour (UTC server; users set timezone) |
| `DIGEST_EVENING_HOUR` | `19` | Default evening digest hour |

---

## Deployment behind HTTPS

Use a reverse proxy (Caddy, nginx, Traefik) in front of the production frontend (port 3000) and API. A sample [Caddyfile](./Caddyfile) is included.

For PostgreSQL instead of SQLite:

```bash
docker compose --profile prod --profile postgres up -d --build
```

Set `DATABASE_URL=postgresql+asyncpg://news:news@postgres:5432/news_router` on the API service and use a strong `POSTGRES_PASSWORD`.

---

## How it works

```
RSS feeds  →  poll & dedupe  →  match topics  →  daily edition  →  browser / push
```

1. **Sources** — Feeds are fetched on a schedule and stored once globally; each user subscribes to the feeds they want.
2. **Topics** — You link feeds to topics and optionally add keywords. Matching stories route into that channel.
3. **Edition** — The Read view shows recent, unread stories grouped by topic—with reels or list layout.
4. **Digests** — At scheduled times, unread highlights are summarized and sent via ntfy.

---

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, feedparser, trafilatura
- **Frontend:** SvelteKit
- **Database:** SQLite (default) or PostgreSQL
- **Push:** ntfy
- **Deploy:** Docker Compose

---

## License

MIT
