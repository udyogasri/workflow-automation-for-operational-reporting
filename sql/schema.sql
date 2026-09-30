-- Schema for Workflow Automation for Operational Reporting
-- Database: SQLite (reporting.db)

CREATE TABLE IF NOT EXISTS operations (
    record_id       TEXT PRIMARY KEY,
    employee        TEXT NOT NULL,
    team            TEXT NOT NULL,
    date            TEXT NOT NULL,
    department      TEXT NOT NULL,
    status          TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    target          REAL NOT NULL,
    actual_value    REAL NOT NULL,
    shift           TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS sales (
    record_id           TEXT PRIMARY KEY,
    employee            TEXT NOT NULL,
    team                TEXT NOT NULL,
    date                TEXT NOT NULL,
    department          TEXT NOT NULL,
    status              TEXT NOT NULL,
    quantity            INTEGER NOT NULL,
    target              REAL NOT NULL,
    actual_value        REAL NOT NULL,
    region              TEXT,
    product_category    TEXT
);

CREATE TABLE IF NOT EXISTS support (
    record_id               TEXT PRIMARY KEY,
    employee                TEXT NOT NULL,
    team                    TEXT NOT NULL,
    date                    TEXT NOT NULL,
    department              TEXT NOT NULL,
    status                  TEXT NOT NULL,
    tickets_count           INTEGER NOT NULL,
    target                  REAL NOT NULL,
    actual_value            REAL NOT NULL,
    priority                TEXT,
    resolution_time_hrs     REAL
);

CREATE TABLE IF NOT EXISTS load_stats (
    source          TEXT PRIMARY KEY,
    raw_count       INTEGER NOT NULL,
    valid_count     INTEGER NOT NULL,
    invalid_count   INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL,
    inserted_count  INTEGER NOT NULL,
    loaded_at       TEXT NOT NULL
);

