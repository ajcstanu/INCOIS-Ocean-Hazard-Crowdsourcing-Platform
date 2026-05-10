# INCOIS Ocean Hazard Platform — Python Backend

FastAPI rewrite of the original Node.js/Express backend.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| ODM / DB | Beanie (Motor async driver) + MongoDB |
| Cache | Redis (redis-py async) |
| Auth | JWT via python-jose + passlib bcrypt |
| Media | Cloudinary |
| NLP | Custom pipeline (langdetect + NLTK + keyword matching) |
| Clustering | scikit-learn DBSCAN |
| Scheduler | APScheduler (asyncio) |
| WebSocket | FastAPI native WebSocket |
| Testing | pytest + pytest-asyncio |

## Quick Start

```bash
# 1. Copy env
cp .env.example .env
# Edit .env with your values

# 2. Install deps
pip install -r requirements.txt

# 3. Run (dev with auto-reload)
python main.py
# OR
uvicorn main:app --reload --port 5000

# 4. Seed sample data
python -m app.utils.seed_data

# 5. Run tests
pytest tests/ -v
```

## Docker

```bash
docker-compose up --build
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:5000/api/docs
- ReDoc:       http://localhost:5000/api/redoc

## Project Structure

```
incois-backend/
├── main.py                  # App factory & entry point
├── config/
│   ├── settings.py          # Pydantic settings (reads .env)
│   ├── database.py          # MongoDB / Beanie init
│   └── redis.py             # Redis client + cache helper
├── app/
│   ├── models/              # Beanie document models
│   │   ├── user.py
│   │   ├── report.py
│   │   ├── hotspot.py
│   │   └── social_post.py
│   ├── routes/              # FastAPI routers
│   │   ├── auth.py
│   │   ├── reports.py
│   │   ├── hotspots.py
│   │   ├── social.py
│   │   ├── admin.py
│   │   ├── analytics.py
│   │   ├── ws.py            # WebSocket endpoint
│   │   └── schemas/         # Pydantic request/response models
│   ├── middleware/
│   │   ├── auth.py          # JWT dependency + role guards
│   │   ├── rate_limit.py    # SlowAPI limiter
│   │   └── upload.py        # Cloudinary upload helper
│   ├── services/
│   │   ├── nlp_service.py   # Multilingual NLP pipeline
│   │   ├── hotspot_service.py # DBSCAN clustering
│   │   ├── social_media_service.py # Twitter ingestion
│   │   ├── scheduler.py     # Background jobs (APScheduler)
│   │   └── websocket_manager.py # WS broadcast manager
│   └── utils/
│       ├── security.py      # JWT + password helpers
│       ├── logger.py        # Loguru setup
│       └── seed_data.py     # DB seeder
├── tests/
│   └── test_auth.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Environment Variables

See `.env.example` for full list.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Register |
| POST | `/api/v1/auth/login` | — | Login |
| POST | `/api/v1/auth/refresh` | — | Refresh token |
| GET | `/api/v1/auth/me` | ✅ | Current user |
| GET | `/api/v1/reports` | — | List reports (filterable) |
| POST | `/api/v1/reports` | ✅ | Submit report |
| POST | `/api/v1/reports/{id}/media` | ✅ | Upload media |
| GET | `/api/v1/reports/{id}` | — | Get report |
| PUT | `/api/v1/reports/{id}` | Official+ | Verify/reject |
| DELETE | `/api/v1/reports/{id}` | Owner/Admin | Delete |
| GET | `/api/v1/hotspots` | — | List hotspots |
| POST | `/api/v1/hotspots/recalculate` | Admin | Force recalc |
| GET | `/api/v1/social/trends` | Analyst+ | Social trends |
| GET | `/api/v1/social/posts` | Analyst+ | Hazard posts |
| GET | `/api/v1/analytics/dashboard` | Analyst+ | Dashboard stats |
| GET | `/api/v1/analytics/trends` | Analyst+ | Daily trends |
| GET | `/api/v1/admin/users` | Admin | List users |
| PUT | `/api/v1/admin/users/{id}/role` | Admin | Change role |
| WS | `/ws/dashboard?token=` | Optional | Live updates |
