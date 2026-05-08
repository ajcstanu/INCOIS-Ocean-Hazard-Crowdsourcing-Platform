# 🌊 INCOIS Ocean Hazard Crowdsourcing Platform

An integrated web + mobile platform for real-time citizen reporting of ocean hazards, social media monitoring, and emergency situational awareness — built for the Indian National Centre for Ocean Information Services (INCOIS).

---

## 📋 Features

- 🗺️ **Interactive Map Dashboard** — Live geotagged reports with dynamic hotspot generation
- 📱 **Mobile-first reporting** — Photo/video upload, offline sync, multilingual UI
- 🤖 **NLP Engine** — Social media hazard detection (Twitter, Facebook, YouTube)
- 👥 **Role-based access** — Citizens, Officials, Analysts, Admins
- 🌐 **Multilingual** — English, Hindi, Tamil, Telugu, Malayalam, Kannada, Bengali, Odia
- 📡 **Early warning integration** — REST API for INCOIS warning systems
- ⚡ **Real-time updates** — WebSocket-based live dashboard

---

## 🏗️ Architecture

```
incois-platform/
├── backend/          # Node.js + Express REST API
│   ├── src/
│   │   ├── models/      # Mongoose schemas
│   │   ├── routes/      # API endpoints
│   │   ├── middleware/  # Auth, validation, upload
│   │   ├── services/    # NLP, social media, notifications
│   │   └── utils/       # Helpers
│   └── config/          # DB, env config
├── frontend/         # React + Vite web app
│   └── src/
│       ├── components/  # Reusable UI components
│       ├── pages/       # Route pages
│       ├── hooks/       # Custom React hooks
│       └── services/    # API calls
├── mobile/           # React Native app (Expo)
└── docs/             # API docs, architecture diagrams
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.x
- MongoDB >= 6.x
- Redis >= 7.x (for sessions/caching)
- AWS S3 or Cloudinary (media storage)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/incois-platform.git
cd incois-platform

# Backend
cd backend && npm install

# Frontend
cd ../frontend && npm install
```

### 2. Environment Setup

```bash
# Backend
cp backend/.env.example backend/.env
# Fill in your values (MongoDB URI, JWT secret, Twitter API keys, etc.)
```

### 3. Run Development

```bash
# Terminal 1 — Backend
cd backend && npm run dev

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Backend runs on `http://localhost:5000`  
Frontend runs on `http://localhost:3000`

---

## 🔑 Environment Variables

See [`backend/.env.example`](backend/.env.example) for full list.

Key variables:
| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `JWT_SECRET` | JWT signing secret |
| `TWITTER_BEARER_TOKEN` | Twitter API v2 bearer token |
| `CLOUDINARY_URL` | Media storage URL |
| `INCOIS_WEBHOOK_URL` | INCOIS early warning system endpoint |

---

## 📡 API Reference

See [`docs/API.md`](docs/API.md) for full endpoint documentation.

Base URL: `http://localhost:5000/api/v1`

| Endpoint | Method | Description |
|---|---|---|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Login |
| `/reports` | GET/POST | List/create hazard reports |
| `/reports/:id` | GET/PUT/DELETE | Report CRUD |
| `/social/trends` | GET | Social media hazard trends |
| `/hotspots` | GET | Dynamic hotspot data |
| `/admin/users` | GET | User management (Admin) |
| `/analytics/dashboard` | GET | Aggregated analytics |

---

## 🤖 NLP Pipeline

The NLP engine (`backend/src/services/nlpService.js`) uses:
1. **Keyword matching** — Domain-specific ocean hazard vocabulary
2. **Multilingual support** — Processes posts in 8 Indian languages
3. **Sentiment analysis** — Urgency scoring (0–1)
4. **Entity extraction** — Location, hazard type, time references
5. **Clustering** — Groups related reports into incidents

---

## 🗺️ Hotspot Algorithm

Hotspots are generated in `backend/src/services/hotspotService.js` using:
- **DBSCAN clustering** on geotagged report coordinates
- **Weighted density** by report severity + recency
- **Social media signal boosting** when online mentions spike

---

## 📱 Mobile App

Built with React Native + Expo.

```bash
cd mobile
npm install
npx expo start
```

Supports:
- Offline report drafting (syncs on reconnect)
- Camera integration for photo/video evidence
- Push notifications for nearby hazard alerts
- GPS auto-tagging

---

## 🌐 Multilingual Support

Translations in `frontend/src/i18n/locales/`:
- `en.json` — English
- `hi.json` — Hindi
- `ta.json` — Tamil
- `te.json` — Telugu
- `ml.json` — Malayalam
- `kn.json` — Kannada
- `bn.json` — Bengali
- `or.json` — Odia

---

## 👥 Roles & Permissions

| Role | Capabilities |
|---|---|
| **Citizen** | Submit reports, view public map |
| **Official** | Verify/reject reports, view all data |
| **Analyst** | Access NLP dashboard, export data, view social trends |
| **Admin** | Full access + user management + system config |

---

## 🔒 Security

- JWT authentication with refresh tokens
- Rate limiting on all endpoints
- File upload validation (type, size, virus scan)
- Input sanitization against XSS/injection
- CORS configured for allowed origins

---

## 📦 Deployment

### Docker

```bash
docker-compose up --build
```

### Manual (Production)

```bash
# Backend
cd backend && npm run build && npm start

# Frontend
cd frontend && npm run build
# Serve dist/ with nginx
```

