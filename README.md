# 🚀 Zuup Opportunity Agent

> **Autonomous AI-Powered Opportunity Discovery and Matching Engine for Students**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Zuup Opportunity Agent** is an intelligent, self-governing platform built for hackathons, scholarships, fellowships, internships, and exchange program discovery. It continuously ingests, analyzes, and matches opportunities to student profiles utilizing semantic embeddings and hard-filtering constraints.

---

## 🌟 Key Features

*   **🕵️ Ingestion & Perceive Loop**: Multi-source scrapers (Devpost, MLH, Opportunity Desk, RSS) running as scheduled Celery Cron jobs to continuously populate the platform with verified opportunities.
*   **🧠 Hybrid Matching Engine**: 
    1.  *Hard Filters*: Discards opportunities failing GPA, enrollment status, nationality/citizenship, or deadline criteria.
    2.  *Semantic Similarity*: Uses 1536-dimensional embeddings (via Cosine Similarity) to match career goals and skills.
    3.  *Bonus Scoring*: Applies location matching, skills match bonuses, and recency boosts (recently created opportunities).
*   **📁 Zero-Cost local Fallbacks**: Allows the entire system to run offline and for free:
    *   *Local Storage*: Automatically saves resumes to local folders if AWS S3 keys are not set.
    *   *Regex Resume Parser*: Falls back to advanced local text-pattern mining if Anthropic keys are absent.
    *   *Deterministic Embeddings*: Seeds a pseudo-random number generator with the text hash to produce deterministic 1536-dimensional unit vector embeddings locally if OpenAI keys are absent.
*   **📊 Kanban Tracker**: Track matches from saved to applied, interviewing, offered, or archived, complete with quick transitions, notes, and CSV data export.
*   **⚡ Premium Dark UI**: Responsive dashboard with match rings, skeletons, tag editing, and a notification drawer.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Frontend [zuup-frontend (Next.js 14)]
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

## 📁 Repository Directory Structure

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
├── zuup-frontend/           # Next.js 14 Dark Theme UI
│   ├── app/                 # App Router (Login, Dashboard, Tracker, Profile)
│   ├── public/              # Static assets
│   └── package.json         # NPM Dependencies
├── docker-compose.yml       # Local Development Orchestration File
└── .env.example             # Documented Template Environment variables
```

---

## 🚦 Getting Started

### Prerequisites

*   [Docker & Docker Compose](https://www.docker.com/) (Required for pgvector and Redis)
*   Python 3.11+ (if running backend outside Docker)
*   Node.js 18+ & npm (if running frontend outside Docker)

---

### 📦 Option A: Run Everything via Docker Compose (Recommended)

This compiles and starts the database, cache broker, API backend, worker queue, cron beat, and Next.js frontend in a single network interface.

1.  **Copy Environment File**:
    ```bash
    cp .env.example .env
    ```
    *All cloud API credentials (AWS, Anthropic, OpenAI, SendGrid) are optional and default to local fallbacks.*

2.  **Start Services**:
    ```bash
    docker compose up -d
    ```

3.  **Run Database Migrations**:
    ```bash
    docker compose exec backend alembic upgrade head
    ```

4.  **Seed Opportunity Data (minimum 12 items)**:
    ```bash
    docker compose exec backend python scripts/seed_opportunities.py
    ```

5.  **Access the Application**:
    *   **Frontend**: `http://localhost:3000`
    *   **Backend REST Docs**: `http://localhost:8000/docs`
    *   **Redis**: `localhost:6379`
    *   **Postgres**: `localhost:5432`

---

### 💻 Option B: Run Services Locally (Manual Development)

If you prefer to run services outside Docker for faster reload speeds:

#### 1. Setup the Database & Redis
Ensure Docker runs Postgres and Redis:
```bash
docker compose up -d postgres redis
```

#### 2. Run Backend API & Celery Workers
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate    # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment configuration:
   ```bash
   cp ../.env.example .env
   ```
5. Apply migrations & seed:
   ```bash
   alembic upgrade head
   python ../scripts/seed_opportunities.py
   ```
6. Start the FastAPI application:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
7. Start the Celery Worker (in a separate terminal):
   ```bash
   celery -A app.worker.celery_app worker --loglevel=info --concurrency=4
   ```
8. Start the Celery Beat Scheduler (in a separate terminal):
   ```bash
   celery -A app.worker.celery_app beat --loglevel=info
   ```

#### 3. Run Frontend (Next.js)
1. Navigate to the frontend directory:
   ```bash
   cd zuup-frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:3000`.

---

## 🧪 Running Unit Tests

The backend includes tests for the Auth APIs, JWT Security mechanisms, and the Matching Engine.

To run the tests, activate your Python virtual environment, navigate to the `backend` folder, and execute:
```bash
pytest -v
```

---

## 🔒 Security and Rate Limiting

*   **Rate Limiter**: Implemented as FastAPI middleware using a Redis sliding-window algorithm. Defaults to 100 requests/min for logged-in users and 10 requests/min for anonymous traffic.
*   **JSON Web Tokens (JWT)**: Secure, signed HS256 JWT access tokens (15-
