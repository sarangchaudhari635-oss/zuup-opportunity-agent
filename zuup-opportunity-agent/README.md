# 🚀 Zuup Opportunity Agent

> **Autonomous AI-Powered Opportunity Discovery and Matching Engine for Students**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Zuup Opportunity Agent** is an intelligent, self-governing platform built for hackathon, scholarship, fellowship, internship, and exchange program discovery. It continuously ingests, analyzes, and matches opportunities to student profiles using semantic embeddings and hard-filtering constraints.

---

## 📋 Table of Contents

1. [What is Zuup?](#-what-is-zuup)
2. [Key Features](#-key-features)
3. [System Architecture](#-system-architecture)
4. [Repository Structure](#-repository-structure)
5. [Getting Started](#-getting-started)
   - [Option A: Docker Compose (Recommended)](#-option-a-run-everything-via-docker-compose-recommended)
   - [Option B: Manual Local Setup](#-option-b-run-services-locally-manual-development)
6. [Login Credentials](#-login-credentials)
7. [How to Use the App](#-how-to-use-the-app-user-guide)
   - [Step 1 — Create Your Account](#step-1--create-your-account)
   - [Step 2 — Set Up Your Profile](#step-2--set-up-your-profile)
   - [Step 3 — Browse Opportunities](#step-3--browse-opportunities)
   - [Step 4 — Track Your Applications](#step-4--track-your-applications)
8. [All Pages Explained](#-all-pages-explained)
9. [Developer Reference](#-developer-reference)
10. [Running Tests](#-running-tests)
11. [Security & Rate Limiting](#-security-and-rate-limiting)
12. [Troubleshooting](#-troubleshooting)
13. [Quick Cheat Sheet](#-quick-cheat-sheet)

---

## 🤔 What is Zuup?

Imagine you had a **super smart robot friend** 🤖 who spends all day searching the whole internet to find:

- 🎓 **Scholarships** — free money for your studies!
- 💼 **Internships** — work experience at cool companies
- 🏆 **Fellowships** — special programs for talented students
- 💻 **Hackathons** — coding competitions with prizes
- ✈️ **Exchange programs** — study in another country!

That's Zuup! It finds all of these for YOU, sorted by how well they match your skills and interests.

---

## 🌟 Key Features

- **🕵️ Ingestion & Perceive Loop**: Multi-source scrapers (Devpost, MLH, Opportunity Desk, RSS) running as scheduled Celery Cron jobs to continuously populate the platform with verified opportunities.
- **🧠 Hybrid Matching Engine**:
  1. *Hard Filters*: Discards opportunities failing GPA, enrollment status, nationality/citizenship, or deadline criteria.
  2. *Semantic Similarity*: Uses 1536-dimensional embeddings (via Cosine Similarity) to match career goals and skills.
  3. *Bonus Scoring*: Applies location matching, skills match bonuses, and recency boosts.
- **📁 Zero-Cost Local Fallbacks**: Allows the entire system to run offline and for free:
  - *Local Storage*: Automatically saves resumes to local folders if AWS S3 keys are not set.
  - *Regex Resume Parser*: Falls back to advanced local text-pattern mining if Anthropic keys are absent.
  - *Deterministic Embeddings*: Seeds a pseudo-random number generator with the text hash to produce 1536-dimensional unit vector embeddings locally if OpenAI keys are absent.
- **📊 Kanban Tracker**: Track matches from saved → applied → under review → shortlisted → outcome, with notes and CSV export.
- **⚡ Premium Dark UI**: Responsive dashboard with match rings, skeletons, tag editing, infinite scroll, and a notification drawer.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Frontend [zuup-frontend (Next.js)]
        UI[Dashboard / Kanban Tracker / Profile]
    end

    subgraph Backend [FastAPI Backend]
        API[FastAPI Router]
        Matching[Matching Engine]
        Parser[Resume Parser]
        Embedding[Embedding Service]
    end

    subgraph Data [Storage & Database]
        DB[(PostgreSQL + pgvector)]
        Cache[(Redis Cache & Broker)]
        LocalFS[(Local Storage Fallback)]
    end

    subgraph Workers [Async Queue]
        Celery[Celery Worker]
        Beat[Celery Beat Scheduler]
    end

    UI -->|HTTP / JSON / Auth| API
    API -->|Read/Write| DB
    API -->|Session & Rate Limits| Cache
    API -->|Upload Resume| LocalFS
    API -->|Queue Tasks| Cache

    Cache -->|Broker Queue| Celery
    Beat -->|Cron Schedule| Cache

    Celery -->|Process Resumes| Parser
    Celery -->|Calculate Embeddings| Embedding
    Celery -->|Execute Matching| Matching
    Celery -->|Update Database| DB
```

---

## 📁 Repository Structure

```
zuup-opportunity-agent/
├── .github/workflows/       # CI/CD Deployment GitHub Actions
├── backend/                 # FastAPI API Server
│   ├── app/
│   │   ├── api/             # REST Endpoints (Auth, Resume, Profile, Opps, Applications)
│   │   ├── core/            # Config, Security, Database & Redis Connections
│   │   ├── models/          # SQLAlchemy Database Models
│   │   ├── prompts/         # AI System Prompts (Parser, Summarizer)
│   │   ├── schemas/         # Pydantic Schemas
│   │   ├── services/        # Matching Engine, Parser Service, Embeddings Service
│   │   └── worker/          # Celery Async Tasks (Ingestion, Agent Loop)
│   ├── migrations/          # Alembic Database Migrations
│   ├── tests/               # pytest Unit Suites
│   └── requirements.txt     # Python Dependencies
├── scripts/
│   ├── init_db.sql          # pgvector postgres initializer
│   └── seed_opportunities.py# Seeds database with 12 mock opportunities
├── zuup-frontend/           # Next.js Dark Theme UI
│   ├── app/                 # App Router (Login, Dashboard, Tracker, Profile)
│   ├── public/              # Static assets
│   └── package.json         # NPM Dependencies
├── docker-compose.yml       # Local Development Orchestration File
├── HOW_TO_USE.md            # (Archived — content merged into this README)
└── .env.example             # Documented Template Environment variables
```

---

## 🚦 Getting Started

### Prerequisites

- [Docker & Docker Compose](https://www.docker.com/) *(Required — for pgvector and Redis)*
- Python 3.11+ *(only if running backend outside Docker)*
- Node.js 18+ & npm *(only if running frontend outside Docker)*

---

### 📦 Option A: Run Everything via Docker Compose (Recommended)

Starts the database, cache broker, API backend, worker queue, cron beat, and Next.js frontend in a single command.

**1. Copy Environment File:**
```bash
cp .env.example .env
```
> All cloud API credentials (AWS, Anthropic, OpenAI, SendGrid) are optional — local fallbacks are used automatically.

**2. Start All Services:**
```bash
docker compose up -d
```

**3. Run Database Migrations:**
```bash
docker compose exec backend alembic upgrade head
```

**4. Seed Opportunity Data (at least 12 items):**
```bash
docker compose exec backend python scripts/seed_opportunities.py
```

**5. Access the Application:**

| Service | URL |
|---|---|
| 🌐 Frontend | http://localhost:3000 |
| 🔌 Backend API Docs | http://localhost:8000/docs |
| ❤️ Health Check | http://localhost:8000/health |
| 🗄️ PostgreSQL | `localhost:5435` |
| ⚡ Redis | `localhost:6379` |

---

### 💻 Option B: Run Services Locally (Manual Development)

#### 1. Start only the Database & Redis via Docker
```bash
docker compose up -d postgres redis
```

#### 2. Backend (FastAPI + Celery)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
cp ../.env.example .env

alembic upgrade head
python ../scripts/seed_opportunities.py

# Terminal 1 — API server
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker
celery -A app.worker.celery_app worker --loglevel=info --concurrency=4

# Terminal 3 — Celery beat scheduler
celery -A app.worker.celery_app beat --loglevel=info
```

#### 3. Frontend (Next.js)
```bash
cd zuup-frontend
npm install
npm run dev
```
Open http://localhost:3000 in your browser.

---

## 🔑 Login Credentials

### 👨‍💻 Demo Account (Ready to Use!)

| Field | Value |
|---|---|
| **Email** | `demo@zuup.dev` |
| **Password** | `Zuup@1234` |

### 👤 Sarang's Account (Owner)

| Field | Value |
|---|---|
| **Email** | `sarangchaudhari635@gmail.com` |
| **Password** | *(the password you set when registering)* |

### 🆕 Create Your Own Account
Go to http://localhost:3000/register — enter your name, email, and a password. Done! 🎉

> 💡 **Password rules:** Minimum 8 characters, include at least one number and one symbol (e.g. `@`, `!`)

---

## 📖 How to Use the App (User Guide)

> *Written simply — even a kid can follow along!* 🧒👧

### Step 1 — Create Your Account

1. Open http://localhost:3000
2. You'll see the **Login page** 🔐
3. New user? Click **"Register"** → http://localhost:3000/register
4. Fill in your **name**, **email**, and **password**
5. Click **Register** ✅ — you're automatically logged in!

---

### Step 2 — Set Up Your Profile

> Your profile is like your report card + résumé. The better it is, the better matches Zuup finds for you! 🎯

Go to http://localhost:3000/profile and fill in:

| Section | What to write |
|---|---|
| **Full Name** | Your real name |
| **Location** | City & country (e.g. "Mumbai, India") |
| **Field of Study** | e.g. "Computer Science" |
| **Status** | Enrolled / Recent Graduate / Graduated |
| **GPA** | Optional — e.g. 3.7 |
| **Skills** | Python, Design, Writing, etc. |
| **Interests** | AI, Music, Sports, etc. |
| **Languages** | English, Hindi, etc. |
| **Career Goals** | A few sentences about your dream career |

Click **"Save Changes"** 💾 and watch the **Profile Strength bar** climb — aim for 80%+ for best results!

---

### Step 3 — Browse Opportunities

> Think of it like a special Instagram — but every post is a chance to win something amazing! 📱✨

Go to http://localhost:3000/dashboard — you'll see a personalised feed of opportunities!

**Each card shows:**
- 🟣 **Type badge** — Scholarship, Internship, Fellowship, Hackathon, Exchange
- ⏰ **Deadline chip** — days remaining
- 🌐 **Remote** — if you can do it from anywhere
- 💰 **Fully Funded** — if all your expenses are covered
- **Match score ring** — how well it fits YOU (🟢 green = great match!)

**Filter your feed:**
- 🔍 **Search box** — type keywords like "AI" or "Europe"
- **Type buttons** — click to filter by category
- 🌐 **Remote Only** toggle — work-from-home opportunities only
- **Min score slider** — show only top-matching opportunities

**On each card:**
- Click **"Save"** → adds it to your tracker 🔖
- Click **"View →"** → opens the official opportunity page

---

### Step 4 — Track Your Applications

> Like a Kanban board — move sticky notes across columns as you progress! 📋

Go to http://localhost:3000/tracker to see your applications in **5 columns**:

| Column | What it means |
|---|---|
| 🔖 **Saved** | Bookmarked, not applied yet |
| 📤 **Applied** | Application submitted |
| 👀 **Under Review** | They're reviewing your application |
| ⭐ **Shortlisted** | You made the shortlist — great job! |
| 🏆 **Outcome** | Final result (accepted or rejected) |

- **Move a card**: click the small arrow buttons on each card
- **Click any card**: a side panel opens to add notes and open the application link
- **Export CSV**: click **"↓ Export CSV"** to download all applications as a spreadsheet

---

## 📄 All Pages Explained

| Page | URL | Description |
|---|---|---|
| 🔐 **Login** | `/login` | Sign into your account |
| 📝 **Register** | `/register` | Create a new account |
| 🎯 **Onboarding** | `/onboarding` | First-time setup wizard |
| 📊 **Dashboard** | `/dashboard` | Browse your matched opportunities |
| 👤 **Profile** | `/profile` | Edit your details, skills & career goals |
| 📋 **Tracker** | `/tracker` | Kanban board to track all applications |
| 🔀 **Opportunities** | `/opportunities` | Redirects to `/dashboard` |
| 🔀 **Applications** | `/applications` | Redirects to `/tracker` |

---

## 🧑‍💻 Developer Reference

### Common Docker Commands

```powershell
# Start everything (first time / after code changes)
docker compose up --build -d

# Start without rebuilding (faster restarts)
docker compose up -d

# Stop all services
docker compose down

# View live logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f backend

# Restart a single service (e.g. after frontend changes)
docker compose restart frontend
```

### Database Commands

```powershell
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Generate a new migration after changing models
docker compose exec backend alembic revision --autogenerate -m "describe_your_change"

# View migration history
docker compose exec backend alembic history

# Open a direct DB shell
docker compose exec postgres psql -U zuup_user -d zuup_db
```

### API Testing (PowerShell)

```powershell
# Health check
Invoke-RestMethod "http://localhost:8000/health"

# Register a user
$body = '{"email":"test@zuup.dev","password":"Test@1234","full_name":"Test User"}'
Invoke-RestMethod "http://localhost:8000/auth/register" -Method POST -ContentType "application/json" -Body $body

# Login and get JWT token
$login = "username=test@zuup.dev&password=Test@1234&grant_type=password"
$r = Invoke-RestMethod "http://localhost:8000/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body $login
$token = $r.access_token

# Fetch authenticated profile
Invoke-RestMethod "http://localhost:8000/profile/me" -Headers @{Authorization="Bearer $token"}
```

### Key Environment Variables (`.env`)

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `localhost:5435/zuup_db` |
| `REDIS_URL` | Redis broker URL | `localhost:6379` |
| `JWT_SECRET_KEY` | Signs JWT access tokens | `zuup-super-secret-dev-key...` |
| `ANTHROPIC_API_KEY` | AI resume parsing *(optional)* | empty → regex fallback |
| `OPENAI_API_KEY` | Semantic embeddings *(optional)* | empty → deterministic mock |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifespan | `15` |

### Port Reference

| Service | Port |
|---|---|
| Next.js Frontend | `3000` |
| FastAPI Backend | `8000` |
| PostgreSQL | `5435` |
| Redis | `6379` |

---

## 🧪 Running Tests

The backend includes tests for Auth APIs, JWT security, and the Matching Engine.

```bash
# Activate your Python virtual environment first, then:
cd backend
pytest -v
```

---

## 🔒 Security and Rate Limiting

- **Rate Limiter**: FastAPI middleware using a Redis sliding-window algorithm. Defaults to **100 req/min** for authenticated users and **10 req/min** for anonymous traffic.
- **JWT Auth**: Signed HS256 access tokens (15-min expiry) + refresh tokens (7-day expiry). Logout revokes tokens via Redis TTL blacklisting.
- **Password Hashing**: Salted bcrypt via `passlib[bcrypt]`.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| **Can't log in** | Confirm app is running (`docker compose up -d`). Check email & password. Or register a fresh account. |
| **Dashboard shows no opportunities** | Fill in your Profile first. Run the seed script. The agent takes a few minutes to process on first run. |
| **Blank page / JS error** | Press F5. Check browser console (F12). Run `docker compose logs backend`. |
| **Docker won't start** | Make sure Docker Desktop is open. Run `docker compose down` then `docker compose up --build -d`. |
| **Database errors** | Run `docker compose exec backend alembic upgrade head` |
| **`script.py.mako` missing** | The file is now included in `backend/migrations/` — just re-run migrations. |

---

## 🎉 Quick Cheat Sheet

```
START APP     →  docker compose up -d
OPEN APP      →  http://localhost:3000
LOGIN (demo)  →  demo@zuup.dev  /  Zuup@1234
FIND OPPS     →  /dashboard
MY PROFILE    →  /profile
TRACK APPS    →  /tracker
API DOCS      →  http://localhost:8000/docs
HEALTH CHECK  →  http://localhost:8000/health
STOP APP      →  docker compose down
RUN TESTS     →  cd backend && pytest -v
```

---

*Made with ❤️ by Sarang Chaudhari — Zuup Opportunity Agent*
