-- LudwigOne Database Schema
-- PostgreSQL 16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Job Types Enum
CREATE TYPE job_type AS ENUM ('tar_processing', 'pdf_splitting');

-- Job Status Enum
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');

-- Extraction Type Enum
CREATE TYPE extraction_type AS ENUM ('text', 'vision', 'ocr');

-- Jobs Table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    workflow_id VARCHAR(255),

    -- Progress tracking
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,

    -- Original upload
    original_filename VARCHAR(512) NOT NULL,
    original_blob BYTEA NOT NULL,

    -- Output
    output_archive_path VARCHAR(512),
    output_archive_blob BYTEA,
    insight_xml TEXT,

    -- Metadata
    error_message TEXT,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_workflow_id ON jobs(workflow_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- Documents Table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Original file info
    original_filename VARCHAR(512) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes INTEGER,
    original_blob BYTEA NOT NULL,

    -- PDF page info (for Flow 2)
    page_number INTEGER,
    total_pages INTEGER,

    -- Categorization results
    assigned_category_id UUID,
    assigned_filename VARCHAR(512),
    categorization_confidence FLOAT,

    -- Merging info (Flow 2)
    merged_into_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_merged_parent BOOLEAN DEFAULT FALSE,

    -- Token usage
    total_tokens INTEGER DEFAULT 0,

    -- Status
    processing_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_job_id ON documents(job_id);
CREATE INDEX idx_documents_category ON documents(assigned_category_id);
CREATE INDEX idx_documents_merged_into ON documents(merged_into_id);
CREATE INDEX idx_documents_page_number ON documents(job_id, page_number);

-- Extractions Table
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    extraction_type extraction_type NOT NULL,

    -- Content
    content TEXT,
    image_blob BYTEA,

    -- Metadata
    token_count INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,

    -- Status
    extraction_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_extractions_document_id ON extractions(document_id);
CREATE INDEX idx_extractions_type ON extractions(extraction_type);

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code

    -- Ordering
    display_order INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_categories_active ON categories(is_active, display_order);

-- Add foreign key for documents -> categories
ALTER TABLE documents
ADD CONSTRAINT fk_documents_category
FOREIGN KEY (assigned_category_id)
REFERENCES categories(id)
ON DELETE SET NULL;

-- Prompt Templates Table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    name VARCHAR(255) NOT NULL UNIQUE,
    purpose VARCHAR(100) NOT NULL, -- vision_extraction, categorization_flow1, merge_decision_flow2, etc.

    template TEXT NOT NULL,

    -- Model config
    model_name VARCHAR(100) NOT NULL DEFAULT 'mistral-large-latest',
    temperature FLOAT DEFAULT 0.1,
    max_tokens INTEGER DEFAULT 4096,
    token_limit INTEGER, -- Max token limit for chunking (insight_generation only)

    -- Version control
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_templates_purpose ON prompt_templates(purpose, is_active);

-- System Config Table (Key-Value Store)
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    value_type VARCHAR(50) NOT NULL DEFAULT 'string', -- string, integer, boolean, json

    description TEXT,
    is_secret BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- API Call Logs Table
CREATE TABLE api_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    extraction_id UUID REFERENCES extractions(id) ON DELETE SET NULL,

    -- Call details
    api_provider VARCHAR(50) NOT NULL, -- mistral, ollama
    model_name VARCHAR(100) NOT NULL,
    call_type VARCHAR(50) NOT NULL, -- vision, text_completion, structured_output

    -- Request
    prompt_text TEXT,
    prompt_tokens INTEGER,
    image_count INTEGER DEFAULT 0,

    -- Response
    response_text TEXT,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Performance
    duration_ms INTEGER,
    retry_attempt INTEGER DEFAULT 0,

    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_call_logs_document ON api_call_logs(document_id);
CREATE INDEX idx_api_call_logs_created ON api_call_logs(created_at DESC);
CREATE INDEX idx_api_call_logs_success ON api_call_logs(success);

-- Insert default categories
INSERT INTO categories (name, description, color, display_order) VALUES
('Anträge', 'Anträge und Antragsformulare', '#3B82F6', 1),
('Bescheide', 'Bescheide und Entscheidungen', '#10B981', 2),
('Gutachten', 'Gutachten und Expertisen', '#8B5CF6', 3),
('Korrespondenz', 'Briefe und E-Mails', '#F59E0B', 4),
('Verträge', 'Verträge und Vereinbarungen', '#EF4444', 5),
('Fotoprotokoll', 'Fotoprotokoll und Bildmaterial', '#EC4899', 6),
('Sonstiges', 'Andere Dokumente', '#6B7280', 7);

-- Insert default system config
INSERT INTO system_config (key, value, value_type, description, is_secret) VALUES
('recipient_email', 'info@stefanai.de', 'string', 'Default recipient for notification emails', false),
('smtp_host', 'smtp.ionos.de', 'string', 'SMTP server hostname', false),
('smtp_port', '587', 'integer', 'SMTP server port', false),
('smtp_use_tls', 'true', 'boolean', 'Use TLS for SMTP', false),
('smtp_username', 'lo-donotreply@stefan-ai.de', 'string', 'SMTP username', false),
('smtp_password', '', 'string', 'SMTP password', true),
('mistral_api_key', '', 'string', 'Mistral API key', true),
('use_ollama', 'false', 'boolean', 'Use Ollama instead of Mistral', false),
('ollama_url', 'http://ollama:11434', 'string', 'Ollama server URL', false),
('upload_max_size_mb', '500', 'integer', 'Maximum upload size in MB', false),
('output_retention_days', '7', 'integer', 'Days to keep output archives', false),
('max_concurrent_vision_calls', '5', 'integer', 'Maximum concurrent Vision API calls', false),
('vision_api_timeout_seconds', '300', 'integer', 'Vision API call timeout', false),
('vision_api_max_retries', '5', 'integer', 'Maximum retries for Vision API', false);

-- Insert default prompt templates
INSERT INTO prompt_templates (name, purpose, template, model_name, temperature, max_tokens) VALUES
(
    'Vision Extraction',
    'vision_extraction',
    'You are analyzing an image extracted from a document. Please describe what you see in detail, focusing on:
- Type of document (form, letter, table, diagram, photo, etc.)
- Key text content visible
- Important visual elements
- Any identifying information

Be thorough but concise. Extract all readable text.',
    'mistral-large-latest',
    0.1,
    4096
),
(
    'Categorization Flow 1',
    'categorization_flow1',
    'Based on the following document content, assign it to one of these categories and suggest a descriptive filename.

Available categories:
{categories}

Document content:
{content}

Respond with a JSON object containing:
- category: exact category name from the list
- new_filename: descriptive filename (without extension)
- confidence: confidence score 0-1',
    'mistral-large-latest',
    0.1,
    1024
),
(
    'Categorization Flow 2',
    'categorization_flow2',
    'Based on the following PDF page content, assign it to one of these categories.

Available categories:
{categories}

Page content:
{content}

Respond with a JSON object containing:
- category: exact category name from the list
- confidence: confidence score 0-1',
    'mistral-large-latest',
    0.1,
    512
),
(
    'Merge Decision Flow 2',
    'merge_decision_flow2',
    'You are comparing two consecutive PDF pages from the same category to determine if they belong to the same document.

First document (first 2-3 pages):
{doc1_content}

Next document (first 2-3 pages):
{doc2_content}

Consider:
- Are they part of the same logical document?
- Do they have continuity in content/formatting?
- Do page numbers suggest they belong together?

Respond with JSON:
- should_merge: boolean
- reasoning: brief explanation',
    'mistral-large-latest',
    0.2,
    512
),
(
    'Filename Generation Flow 2',
    'filename_generation_flow2',
    'Based on this merged document content, suggest a descriptive filename.

Document content:
{content}

Category: {category}

Respond with JSON:
- new_filename: descriptive filename (without extension)
- confidence: confidence score 0-1',
    'mistral-large-latest',
    0.1,
    512
),
(
    'Insight Generation',
    'insight_generation',
    'Generate a comprehensive insight summary for this document processing job.

Documents processed:
{documents_summary}

Extract and structure:
- Applicant name (if identifiable)
- Application numbers
- Key findings and themes
- Category distribution
- Important dates or deadlines

Respond with structured JSON containing all relevant metadata.',
    'mistral-large-latest',
    0.1,
    4096
);

-- Users Table (Admin Authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- Admin user should be created by seed script with explicit credentials:
-- ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD
-- Run: docker-compose exec api python scripts/seed_admin_user.py

-- Audit Logs Table (Admin Action Tracking)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Who
    user_id UUID NOT NULL,
    username VARCHAR(255) NOT NULL,

    -- What
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),

    -- Details
    description TEXT,
    changes JSONB,

    -- Request metadata
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    endpoint VARCHAR(255),
    method VARCHAR(10),

    -- Status
    success VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
