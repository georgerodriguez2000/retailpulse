CREATE TABLE pipeline_runs (
    run_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    rows_extracted INTEGER NOT NULL DEFAULT 0 CHECK (rows_extracted >= 0),
    rows_valid INTEGER NOT NULL DEFAULT 0 CHECK (rows_valid >= 0),
    rows_rejected INTEGER NOT NULL DEFAULT 0 CHECK (rows_rejected >= 0),
    rows_loaded INTEGER NOT NULL DEFAULT 0 CHECK (rows_loaded >= 0),
    raw_file TEXT,
    clean_file TEXT,
    rejected_file TEXT,
    error_message TEXT
);