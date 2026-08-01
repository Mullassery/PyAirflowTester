-- PyAirflowTester Initial Schema
-- Version 0.1.0

-- Extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: dags (Artifact analysis)
CREATE TABLE IF NOT EXISTS dags (
    id BIGSERIAL PRIMARY KEY,
    dag_id VARCHAR(250) NOT NULL,
    file_path TEXT NOT NULL,
    source_code TEXT,
    parse_time_ms FLOAT,
    task_count INT,
    max_task_depth INT,
    has_cycles BOOLEAN,
    dynamic_dag_detected BOOLEAN,
    risk_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dag_id),
    INDEX idx_dag_id (dag_id),
    INDEX idx_created_at (created_at)
);

-- Table: dag_violations (Static rule violations)
CREATE TABLE IF NOT EXISTS dag_violations (
    id BIGSERIAL PRIMARY KEY,
    dag_id BIGINT REFERENCES dags(id) ON DELETE CASCADE,
    rule_id VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    remediation TEXT,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dag_id (dag_id),
    INDEX idx_rule_id (rule_id),
    INDEX idx_severity (severity)
);

-- Table: dbt_projects (dbt artifact storage)
CREATE TABLE IF NOT EXISTS dbt_projects (
    id BIGSERIAL PRIMARY KEY,
    project_name VARCHAR(250),
    manifest JSONB,
    catalog JSONB,
    run_results JSONB,
    manifest_hash VARCHAR(64) UNIQUE,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_manifest_hash (manifest_hash)
);

-- Table: dbt_tests
CREATE TABLE IF NOT EXISTS dbt_tests (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES dbt_projects(id) ON DELETE CASCADE,
    test_id VARCHAR(500),
    test_name VARCHAR(250),
    model_name VARCHAR(250),
    source_name VARCHAR(250),
    description TEXT,
    severity VARCHAR(20),
    risk_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, test_id),
    INDEX idx_project_id (project_id),
    INDEX idx_model_name (model_name)
);

-- Table: dbt_models
CREATE TABLE IF NOT EXISTS dbt_models (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES dbt_projects(id) ON DELETE CASCADE,
    model_name VARCHAR(250),
    materialization VARCHAR(20),
    description TEXT,
    source_file TEXT,
    test_count INT,
    downstream_model_count INT,
    risk_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, model_name),
    INDEX idx_project_id (project_id),
    INDEX idx_model_name (model_name)
);

-- Table: dbt_model_dependencies (Lineage)
CREATE TABLE IF NOT EXISTS dbt_model_dependencies (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES dbt_projects(id) ON DELETE CASCADE,
    upstream_model_name VARCHAR(250),
    downstream_model_name VARCHAR(250),
    INDEX idx_project_id (project_id),
    INDEX idx_upstream (upstream_model_name),
    INDEX idx_downstream (downstream_model_name)
);

-- Table: analysis_runs (Track analysis executions)
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_type VARCHAR(50) NOT NULL,  -- 'static', 'runtime', 'correlation'
    status VARCHAR(50) NOT NULL,     -- 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    violation_count INT,
    error_message TEXT,
    INDEX idx_run_type (run_type),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- Table: rule_violations_all (Unified violations)
CREATE TABLE IF NOT EXISTS rule_violations_all (
    id BIGSERIAL PRIMARY KEY,
    rule_id VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    affected_resource VARCHAR(500),
    affected_resource_type VARCHAR(50),  -- 'dag', 'model', 'test', 'task'
    message TEXT,
    remediation TEXT,
    context JSONB,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rule_id (rule_id),
    INDEX idx_severity (severity),
    INDEX idx_category (category),
    INDEX idx_affected_resource (affected_resource),
    INDEX idx_analysis_run_id (analysis_run_id),
    INDEX idx_created_at (created_at)
);

-- Table: scoring_snapshots
CREATE TABLE IF NOT EXISTS scoring_snapshots (
    id BIGSERIAL PRIMARY KEY,
    resource_type VARCHAR(50),       -- 'dag', 'model', 'project'
    resource_id VARCHAR(500),
    reliability_score FLOAT,
    performance_score FLOAT,
    maintainability_score FLOAT,
    security_score FLOAT,
    cost_efficiency_score FLOAT,
    overall_health_score FLOAT,
    risk_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created_at (created_at)
);

-- View: violations_summary
CREATE OR REPLACE VIEW violations_summary AS
SELECT
    rule_id,
    severity,
    category,
    COUNT(*) as violation_count,
    COUNT(DISTINCT affected_resource) as affected_resources,
    MAX(created_at) as last_violation
FROM rule_violations_all
GROUP BY rule_id, severity, category;

-- View: health_summary
CREATE OR REPLACE VIEW health_summary AS
SELECT
    resource_type,
    COUNT(*) as total_resources,
    AVG(overall_health_score) as avg_health_score,
    MIN(overall_health_score) as min_health_score,
    MAX(overall_health_score) as max_health_score,
    COUNT(CASE WHEN risk_level = 'critical' THEN 1 END) as critical_count,
    COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_count,
    COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_count,
    COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_count
FROM scoring_snapshots
WHERE created_at >= (NOW() - INTERVAL '7 days')
GROUP BY resource_type;

-- Indexes for common queries
CREATE INDEX idx_violations_by_severity ON dag_violations(severity);
CREATE INDEX idx_violations_by_resource ON dag_violations(dag_id);
CREATE INDEX idx_dbt_model_tests ON dbt_tests(model_name);
CREATE INDEX idx_dbt_model_risk ON dbt_models(risk_score DESC);
