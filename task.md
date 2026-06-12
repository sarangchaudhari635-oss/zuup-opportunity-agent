# Zuup Opportunity Agent — Build Task Tracker

## Phase 0 — Project Setup & Repository Structure
- [/] Step 0.1 — Create monorepo directory structure
- [/] Step 0.2 — Create `.env.example`
- [ ] Step 0.3 — `docker-compose.yml` for local dev stack
- [ ] Step 0.4 — Backend `requirements.txt` + `Dockerfile`
- [ ] Step 0.5 — Initialize Next.js frontend

## Phase 1 — Infrastructure & DevOps
- [ ] Step 1.1 — Alembic setup + DB migrations (all tables)
- [ ] Step 1.2 — pgvector SQL setup
- [ ] Step 1.3 — Core config module (`backend/app/core/config.py`)

## Phase 2 — Backend Core Services
- [ ] Step 2.1 — Auth service (JWT + Google OAuth)
- [ ] Step 2.2 — Resume upload endpoint (S3)
- [ ] Step 2.3 — Profile service (CRUD + completeness)
- [ ] Step 2.4 — Opportunity feed API
- [ ] Step 2.5 — Application tracker API
- [ ] Step 2.6 — Notification service
- [ ] Step 2.7 — Rate limiting middleware

## Phase 3 — AI / ML Pipeline
- [ ] Step 3.1 — Resume parser (Claude API)
- [ ] Step 3.2 — Opportunity description normalizer
- [ ] Step 3.3 — Embedding generation service (OpenAI)
- [ ] Step 3.4 — Matching engine
- [ ] Step 3.5 — Ingestion pipeline (scrapers)

## Phase 4 — Frontend (Next.js 14)
- [ ] Step 4.1 — Design system (globals.css, fonts)
- [ ] Step 4.2 — Auth pages (login, register)
- [ ] Step 4.3 — Onboarding flow (3 steps)
- [ ] Step 4.4 — Opportunity feed page
- [ ] Step 4.5 — Application tracker (Kanban)
- [ ] Step 4.6 — Profile page
- [ ] Step 4.7 — Notification bell component

## Phase 5 — Async Jobs & Agent Loop
- [ ] Step 5.1 — Celery worker setup
- [ ] Step 5.2 — Agent Perceive→Reason→Act loop
- [ ] Step 5.3 — Email service (SendGrid)
- [ ] Step 5.4 — Redis caching layer

## Phase 6 — Testing
- [ ] Step 6.1 — Unit tests
- [ ] Step 6.2 — Integration tests

## Phase 7 — Launch
- [ ] Step 7.1 — CI/CD pipeline
- [ ] Step 7.2 — Seed script (500+ opportunities)
