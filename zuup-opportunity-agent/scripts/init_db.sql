-- ============================================================
-- Zuup Opportunity Agent — Database Init Script
-- Runs automatically when Postgres container starts
-- ============================================================

-- Enable pgvector extension for semantic similarity search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';
