-- 1. SETUP & EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. ENUMS
-- Note: In SQLAlchemy `models.py`, we handle these via Enum types, 
-- but this script ensures the DB is primed if run manually.
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('patient', 'clinician', 'admin');
    CREATE TYPE metric_category AS ENUM ('Blood', 'DNA', 'Vitals', 'Functional', 'Fitness', 'Microbiome');
    CREATE TYPE file_category AS ENUM ('LabReport', 'Scan', 'UserUpload', 'FunctionalTestVideo', 'AudioNote');
    CREATE TYPE med_type AS ENUM ('Prescription', 'Supplement', 'Nootropic', 'Peptide');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. IDENTITY
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    auth0_sub VARCHAR(255) UNIQUE,
    role user_role DEFAULT 'patient',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_key_hash VARCHAR(255),
    is_trusted BOOLEAN DEFAULT FALSE
);

-- 4. OBSERVATION ENGINE
CREATE TABLE IF NOT EXISTS metric_definitions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    category metric_category NOT NULL,
    unit VARCHAR(20),
    description TEXT,
    ref_min NUMERIC(10, 4),
    ref_max NUMERIC(10, 4)
);

CREATE TABLE IF NOT EXISTS health_observations (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_id INT NOT NULL REFERENCES metric_definitions(id),
    source_id INT REFERENCES data_sources(id),
    recorded_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    value_numeric NUMERIC(18, 6),
    value_text TEXT,
    raw_metadata JSONB,
    CONSTRAINT check_has_value CHECK (value_numeric IS NOT NULL OR value_text IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_obs_user_metric_time ON health_observations (user_id, metric_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_obs_metric_code ON metric_definitions (code);

-- 5. CLINICAL & LIFESTYLE
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    type med_type DEFAULT 'Supplement',
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE
);

-- 6. UNSTRUCTURED DATA
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    content_markdown TEXT,
    mood_score INT CHECK (mood_score BETWEEN 1 AND 10),
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, entry_date)
);

CREATE TABLE IF NOT EXISTS media_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category file_category NOT NULL,
    s3_bucket VARCHAR(100) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    is_processed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- SEED DATA
INSERT INTO data_sources (name, is_trusted) VALUES
('Apple Health', TRUE),
('HealX Clinic Lab', TRUE),
('User Manual Entry', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO metric_definitions (code, display_name, category, unit, ref_min, ref_max) VALUES
('HEALX_TEST_TOTAL', 'Total Testosterone', 'Blood', 'ng/dL', 264.0, 916.0),
('HEALX_VIT_D', 'Vitamin D (25-OH)', 'Blood', 'nmol/L', 50.0, 250.0),
('HK_HR_RESTING', 'Resting Heart Rate', 'Vitals', 'bpm', 40.0, 100.0),
('HK_VO2_MAX', 'VO2 Max', 'Fitness', 'ml/kg/min', NULL, NULL),
('DNA_MTHFR_C677T', 'MTHFR C677T Variant', 'DNA', 'Genotype', NULL, NULL),
('DNA_APOE', 'APOE Status', 'DNA', 'Haplotype', NULL, NULL)
ON CONFLICT (code) DO NOTHING;
