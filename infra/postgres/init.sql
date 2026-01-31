-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create initial schema (will be managed by Alembic migrations)
-- This file just enables extensions and any initial setup

-- Verify pgvector is installed
SELECT * FROM pg_extension WHERE extname = 'vector';
