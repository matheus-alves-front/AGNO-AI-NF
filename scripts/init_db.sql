-- Initialize Fiscal Agent Database
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension for RAG embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for storing NFe documents
CREATE TABLE IF NOT EXISTS nfe_documents (
    id SERIAL PRIMARY KEY,
    access_key VARCHAR(44) UNIQUE NOT NULL,
    xml_content TEXT NOT NULL,
    parsed_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table for audit results
CREATE TABLE IF NOT EXISTS audit_results (
    id SERIAL PRIMARY KEY,
    nfe_access_key VARCHAR(44) NOT NULL REFERENCES nfe_documents(access_key),
    risk_score INTEGER NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    inconsistencies JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table for knowledge base (RAG)
CREATE TABLE IF NOT EXISTS tax_knowledge (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768),  -- Gemini text-embedding-004 dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS tax_knowledge_embedding_idx 
ON tax_knowledge 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for fast NFe access key lookup
CREATE INDEX IF NOT EXISTS nfe_access_key_idx ON nfe_documents(access_key);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fiscal_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fiscal_user;
