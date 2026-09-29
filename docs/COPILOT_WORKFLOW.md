# GitHub Copilot Development Workflow & Verification Guide

This document details the human-in-the-loop AI pair programming workflow used during the development of the **Workflow Automation for Operational Reporting** system.

---

## 1. Development Principles & Human Quality Ownership

GitHub Copilot was utilized as an AI code-completion and refactoring assistant. To guarantee full quality ownership and zero regression:

```
[ Developer Task / Requirement ]
               │
               ▼
[ GitHub Copilot Prompt / Code Completion ]
               │
               ▼
[ Developer Code Inspection & Syntax Review ]
               │
               ▼
[ Refactoring & Constraint Alignment ]
               │
               ▼
[ Execution against SQLite & CSV Sources ]
               │
               ▼
[ 70-Assertion Automated Test Suite Verification ]
               │
               ▼
[ Multi-Level Reconciliation Audit (reconcile.py) ]
               │
               ▼
[ Final Production Acceptance ]
```

- **No Blind Acceptance**: All AI-suggested code snippets were inspected, modified, and validated against raw database schemas.
- **Empirical Verification**: Code functionality is verified by executable test assertions (`scripts/test_reports.py`) and independent Python calculation reconciliation (`scripts/reconcile.py`).

---

## 2. Project Task Implementations & Examples

### Task 1: DDL Schema & Database Setup (`sql/schema.sql`, `scripts/setup_database.py`)
- **Requirement**: Create three relational tables (`operations`, `sales`, `support`) with proper data types and primary key constraints.
- **Copilot Prompt**: *"Generate SQLite DDL for operations, sales, and support tables with record_id primary key and appropriate column types."*
- **Generated Code**: Drafted CREATE TABLE statements.
- **Developer Review & Refactoring**: Added `NOT NULL` constraints on mandatory metric fields (`target`, `actual_value`) and ensured table drop safety (`DROP TABLE IF EXISTS`).
- **Validation**: Executed `setup_database.py` and verified table creation via SQLite `sqlite_master` table checks.

---

### Task 2: Multi-Source CSV Ingestion & Validation (`scripts/load_data.py`)
- **Requirement**: Ingest CSV files from 3 departments, validate headers/types/dates/duplicates, and insert valid rows without crashing on invalid data.
- **Copilot Prompt**: *"Write a Python script using csv.DictReader and sqlite3 to load operations.csv, validate fields, log errors, and skip invalid rows."*
- **Generated Code**: Drafted row iteration loops and basic type conversion.
- **Developer Review & Refactoring**: Added header validation, ISO date format check (`YYYY-MM-DD`), file-level `seen_ids` tracking for duplicate detection, and `INSERT OR IGNORE` DB parameterization.
- **Validation**: Tested with corrupt sample CSV rows (missing fields, bad dates) and confirmed non-blocking warning logs.

---

### Task 3: Unified SQL View & Status Normalization (`sql/reporting_queries.sql`)
- **Requirement**: Standardize divergent department statuses (`Completed`/`Closed`/`Resolved`, `In Progress`/`Pipeline`/`Pending`, `Failed`/`Lost`/`Escalated`) into a single view.
- **Copilot Prompt**: *"Draft a SQL UNION ALL view combining operations, sales, and support tables with a CASE statement normalizing statuses into Completed, Pending, and Failed."*
- **Generated Code**: Drafted initial `v_all_records` view SQL structure.
- **Developer Review & Refactoring**: Aligned generic `item_count` column aliases and added `source` system tags (`operations`, `sales`, `support`).
- **Validation**: Executed `run_reports.py` and confirmed 150 rows were categorized into 117 Completed, 18 Pending, 15 Failed.

---

### Task 4: Unit-Consistent Sales Revenue Reporting (`data/sales.csv`, `sql/reporting_queries.sql`)
- **Requirement**: Ensure target and actual values in Sales represent the same monetary unit ($) to avoid mixed-unit percentage anomalies.
- **Copilot Assistance**: Suggested refactoring `sales.csv` targets to reflect monetary revenue targets matching actual revenue ($).
- **Developer Review & Verification**: Rewrote target columns to $ scale, verifying Sales Target Achievement evaluated to a realistic **86.5%**.

---

### Task 5: Automated Test Assertions (`scripts/test_reports.py`)
- **Requirement**: Build comprehensive test assertions covering DB calculations, edge cases, report structure, and reconciliation.
- **Copilot Prompt**: *"Generate Python test functions using sqlite3 to check zero target handling, missing fields, and date summary aggregations."*
- **Generated Code**: Drafted test helper assertions and sample test cases.
- **Developer Review & Refactoring**: Structured tests into 6 clean sections with 70 passing assertions.

---

## 3. Developer Copilot Activity Record Template

*For logging future task completions:*

```markdown
### Task ID: DEV-XXX
- **Requirement**: [Brief task description]
- **Copilot Assistance**: [Code completion / refactoring / test generation]
- **Developer Inspection**: [Modifications made to generated snippet]
- **Execution & Test Result**: [Pass / Fail status in test_reports.py]
- **Accepted Date**: YYYY-MM-DD
```
