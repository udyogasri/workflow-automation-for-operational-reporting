# Workflow Automation for Operational Reporting

An automated Python and SQL data pipeline that reads daily data files from multiple department sources, validates data quality, stores records in a central relational database, calculates performance metrics, performs multi-level reconciliation, and automatically generates an HTML operational report.

---

## Quick Navigation

- [1. Project Purpose & Overview](#1-project-purpose--overview)
- [2. Business Problem & Impact](#2-business-problem--impact)
- [3. Simple End-to-End Workflow](#3-simple-end-to-end-workflow)
- [4. Technology Stack](#4-technology-stack)
- [5. How Data Is Validated & Handled](#5-how-data-is-validated--handled)
- [6. What the System Produces](#6-what-the-system-produces)
- [7. Project Structure](#7-project-structure)
- [8. How to Run](#8-how-to-run)
- [9. Automated Scheduling](#9-automated-scheduling)
- [10. Engineering Development Methodology](#10-engineering-development-methodology)
- [11. Testing & Verification Suite](#11-testing--verification-suite)
- [12. Measured Impact](#12-measured-impact)
- [13. Optional Confluence Integration](#13-optional-confluence-integration)
- [14. Quick Explanation for Interviews & Presentations](#14-quick-explanation-for-interviews--presentations)
- [15. All Commands Quick Reference](#15-all-commands-quick-reference)

---

## 1. Project Purpose & Overview

This project automates daily and weekly operational reporting for multi-department organizations. 

Instead of requiring an operations team to manually gather CSV spreadsheet files from different teams, copy data between sheets, fix formatting inconsistencies, and build complex Excel formulas, this system automates the entire process. With a single command or on a background schedule, the application reads department data, verifies data quality, updates a central SQLite database, checks calculations for mathematical accuracy, and creates a formatted web report that automatically opens in your web browser.

---

## 2. Business Problem & Impact

### The Manual Problem
Before this automation was implemented, the operations team spent **~12 hours every week** manually preparing reports across three core business divisions:

- **Operations**: Production volumes, shift outputs, and manufacturing targets.
- **Sales**: Closed deals, sales pipelines, and monetary revenue targets ($).
- **Support**: Customer service ticket counts, resolution targets, and SLA metrics.

Executing this process manually created significant overhead:
- **Time Loss**: Operations staff spent hours downloading CSV files, aligning headers, and converting date formats.
- **Inconsistent Terminology**: Departments used different terms for completed work (Operations called completed work *"Completed"*, Sales called it *"Closed"*, and Support called it *"Resolved"*).
- **Formula & Human Errors**: Manual copy-pasting led to broken formulas, missing VLOOKUP values, and undetected duplicate records.
- **Lack of Audit Logs**: Invalid rows were frequently dropped without any formal error logs.

### The Automated Solution

```text
Manual Process (Before)
Open 3 CSV Files ──> Clean Formatting ──> Align Column Names ──> Build Formulas ──> Email Report
(Required ~12 hours of repetitive manual effort every week)

Automated Process (After)
Run One Command or Let Scheduler Trigger Automatically
(Performs validation, database update, reconciliation, and HTML report generation in < 1 second)
```

---

## 3. Simple End-to-End Workflow

### Main Reporting Pipeline

```text
CSV Files (Operations, Sales, Support)
  │
  ▼
Validation (Checks missing fields, date formats & numbers)
  │
  ▼
Data Cleaning (Invalid / duplicate rows filtered & logged safely)
  │
  ▼
SQLite Database (Central structured data storage)
  │
  ▼
SQL Reporting (Status mapping & aggregate metric queries)
  │
  ▼
Reconciliation (Independent 5-level math accuracy check)
  │
  ▼
HTML Report (Styled web report generated & auto-opened in browser)
  │
  ▼
Optional Confluence Publishing (Enterprise REST API integration)
```

### Background Scheduler Trigger

```text
Scheduler (Runs continuously in background)
  │
  ▼
main.py (Executes workflow daily at configured time e.g., 09:00 AM)
  │
  ▼
Same Complete Workflow (Runs automatically with catch-up recovery)
```

---

## 4. Technology Stack

This project is built using the **Python Standard Library**, requiring **zero third-party package installations**:

- **Python**: Core programming language used to orchestrate the pipeline, validate data, run tests, and generate reports.
- **CSV (Comma-Separated Values)**: Standard file format used by department teams to export raw data.
- **SQLite**: Lightweight relational database engine used to store validated operational records without requiring a external database server.
- **SQL (Structured Query Language)**: Query language used to unify tables, normalize status terms, and calculate aggregate metrics.
- **HTML / CSS**: Web markup and internal styling used to build the final interactive report.
- **Git & GitHub**: Version control system used to manage code changes, documentation, and project history.
- **Confluence REST API**: Optional HTTPS integration used to publish reports to Atlassian Confluence documentation spaces.
- **Scheduler**: Standard-library background automation loop supporting daily time triggers and offline catch-up recovery.

---

## 5. How Data Is Validated & Handled

When department CSV files are processed by the system, each row is inspected and categorized:

- **Valid Rows**: Records that pass all checks (valid dates, correct numeric types, no missing mandatory fields). These rows are inserted into the database.
- **Invalid Rows**: Records containing bad formatting (such as an invalid date format or text in a numeric column). These rows are skipped, logged as warnings in `logs/load_data_*.log`, and omitted from database insertion.
- **Duplicate Rows**: Records with a record ID that was already processed. These rows are skipped to prevent double-counting.
- **Database Rows**: The net count of valid rows successfully saved into the SQLite database.

### Mathematical Accounting & Reconciliation Formula

Skipping invalid or duplicate rows is an intentional data-cleaning safeguard. To ensure no data is lost or unaccounted for, the system enforces a strict mathematical accounting formula:

$$\text{RAW CSV ROWS} = \text{VALID ROWS} + \text{REJECTED ROWS} + \text{DUPLICATE ROWS}$$

$$\text{VALID ROWS} = \text{DATABASE ROWS}$$

#### Verified Dataset Example

```text
Operations:  1,005 Raw CSV Rows = 1,000 Valid + 4 Rejected + 1 Duplicate  │  1,000 Valid = 1,000 DB Rows
Sales:       1,002 Raw CSV Rows = 1,000 Valid + 2 Rejected + 0 Duplicates │  1,000 Valid = 1,000 DB Rows
Support:     1,008 Raw CSV Rows = 1,000 Valid + 7 Rejected + 1 Duplicate  │  1,000 Valid = 1,000 DB Rows
────────────────────────────────────────────────────────────────────────────────────────────────────
TOTAL:       3,015 Raw CSV Rows = 3,000 Valid + 13 Rejected + 2 Duplicates│  3,000 Valid = 3,000 DB Rows
```

---

## 6. What the System Produces

Running the workflow generates four key deliverables:

1. **SQLite Database (`database/reporting.db`)**: A clean relational database containing 3,000 validated department records and load tracking metrics (`load_stats`).
2. **HTML Operational Report (`reports/operational_report_*.html`)**: A styled web page containing Executive Summaries, Source-wise KPIs, Team Performance, Daily Activity Trends, Operational Exception Flags, and Data Quality statistics. Automatically opens in your browser upon completion.
3. **Execution Logs (`logs/`)**: Detailed log files capturing file checks, validation warnings, calculation metrics, and scheduler events.
4. **Optional Confluence Page**: Standardized documentation published directly to Atlassian Confluence Cloud portals via REST API when login credentials are provided in `.env`.

---

## 7. Project Structure

```text
workflow-automation-for-operational-reporting/
├── main.py                  # Main entry point orchestrating the complete workflow
├── scheduler.py             # Background automation loop with catch-up recovery
├── data/                    # Department source files (operations.csv, sales.csv, support.csv)
├── database/                # SQLite database location (reporting.db)
├── sql/                     # DDL table schemas & SQL reporting views
├── scripts/                 # Core Python modules (loading, reporting, reconciliation, HTML generator)
├── scratch/                 # Data generator script (generate_data.py creating 1,000+ record datasets)
├── reports/                 # Output folder for generated HTML reports
├── logs/                    # Execution and scheduler runtime logs
├── docs/                    # In-depth technical documentation files
├── .env.example             # Template file for environment settings
└── requirements.txt         # Standard library documentation (zero pip packages required)
```

> Note: For a detailed file-by-file codebase map, full database DDL schemas, and SQL query definitions, refer to [`docs/TECHNICAL_DETAILS.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/TECHNICAL_DETAILS.md).

---

## 8. How to Run

Running the workflow requires three simple steps:

### Step 1: Install Dependencies (Verify Environment)
Run the standard dependency installation command:
```powershell
pip install -r requirements.txt
```
*Note: This project is built using 100% Python Standard Library modules (`sqlite3`, `csv`, `os`, `datetime`, `logging`, `sys`, `urllib`, `webbrowser`). Running `pip install -r requirements.txt` verifies that your Python environment is active and ready.*

### Step 2: Initialize Environment File
Copy the example environment template to create your local `.env` configuration file:

- **Windows (PowerShell)**:
  ```powershell
  Copy-Item .env.example .env
  ```
- **macOS / Linux**:
  ```bash
  cp .env.example .env
  ```

### Step 3: Run the Reporting Workflow
Execute the main orchestrator script:
```powershell
python main.py
```

---

### Detailed Execution Sequence (What Happens When You Run `main.py`)

1. **Source File Verification**: Confirms `operations.csv`, `sales.csv`, and `support.csv` exist in the `data/` folder.
2. **Database Setup & Data Ingestion**:
   - Creates `database/reporting.db` if it does not exist yet.
   - Clears existing table entries to ensure an **idempotent load** (preventing duplicate rows across multiple runs).
   - Reads CSV records, validates field formats and ISO dates (`YYYY-MM-DD`), filters out duplicate IDs, and inserts clean records into SQLite.
   - Saves ingestion statistics (`raw_count`, `valid_count`, `invalid_count`, `duplicate_count`) into the `load_stats` database table.
3. **SQL Analytics & Metric Aggregation**: Refreshes the unified view `v_all_records`, maps department status terms (`Completed`/`Closed`/`Resolved`, `In Progress`/`Pipeline`/`Pending`, `Failed`/`Lost`/`Escalated`), and computes aggregate metrics.
4. **Independent 5-Level Reconciliation Audit**: Runs independent math checks to confirm that $\text{RAW} = \text{VALID} + \text{REJECTED} + \text{DUPLICATES}$ and $\text{VALID} = \text{DATABASE ROWS}$.
5. **HTML Report Generation & Auto-Launch**: Compiles metrics into an 8-section interactive report saved as `reports/operational_report_YYYY-MM-DD_HH-MM-SS.html` and **automatically opens it in your default web browser**.
6. **Logging & Console Summary**: Saves runtime logs to `logs/main_YYYYMMDD_HHMMSS.log` and prints a final execution summary (`Status: SUCCESS`) in your terminal.

---

## 9. Automated Scheduling

To run reports automatically every day without manual intervention, start the background scheduler script:

```powershell
python scheduler.py
```

### Key Scheduler Features
- **Configured Schedule Time**: By default, runs every day at `09:00 AM` (configurable in `.env`).
- **Catch-Up Recovery**: If your computer was powered off at 09:00 AM, the scheduler detects the missed run upon startup and executes the workflow immediately.
- **Single-Run Testing Flag**: Test a single schedule cycle and exit immediately using:
  ```powershell
  python scheduler.py --once
  ```

> Note: For step-by-step instructions on setting up automatic Windows boot startup, refer to [`docs/SCHEDULER.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/SCHEDULER.md).

---

## 10. Engineering Development Methodology

The architecture follows standard software engineering principles centered on modular design, code inspection, and test-driven quality assurance:

```text
Requirement Engineering ──> Component Prototyping ──> Code Review & Refactoring ──> Automated Testing ──> Production Acceptance
```

- **Modular Architecture**: Concerns are cleanly separated across data loading (`load_data.py`), database setup (`setup_database.py`), SQL reporting views (`reporting_queries.sql`), math reconciliation (`reconcile.py`), HTML rendering (`generate_report.py`), and background scheduling (`scheduler.py`).
- **Data Safeguards**: Explicit `NOT NULL` constraints, header validation, date format checks, duplicate ID filtering, and error logging.
- **Empirical Quality Assurance**: All pipeline logic is verified against 104 automated test assertions and a 5-level reconciliation framework.

> Note: For task tracking details and technical workflow guidelines, refer to [`docs/ENGINEERING_WORKFLOW.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/ENGINEERING_WORKFLOW.md).

---

## 11. Testing & Verification Suite

The repository includes an automated test suite to ensure system stability:

```powershell
python scripts/test_reports.py
```

### Verified Test Results
$$\text{RESULTS: } 104 \text{ passed, } 0 \text{ failed}$$

### High-Level Test Coverage
- **Database Setup**: Confirms tables exist and match DDL schema definitions.
- **Data Validation**: Tests header checks, date parsing, numeric conversions, and duplicate ID rejection.
- **Status Mapping**: Confirms department statuses map cleanly into `Completed`, `Pending`, and `Failed`.
- **5-Level Reconciliation**: Verifies math formulas across Python and SQL aggregations.
- **Edge Cases**: Tests handling of zero targets, NULL values, empty query results, and corrupt CSV rows.
- **Report Generation**: Verifies HTML section rendering and file creation.

### Regenerating Test Datasets
To regenerate fresh 1,000+ record test CSV datasets containing intentional invalid and duplicate records for data quality testing, run:
```powershell
python scratch/generate_data.py
```

> Note: For detailed test categories and assertion specifications, refer to [`docs/TESTING.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/TESTING.md).

---

## 12. Measured Impact

### 1. Operational Time Savings (*Scenario-Modeled Baseline*)
- **Manual Baseline**: 12.0 hours per week (based on a scenario model of weekly file gathering, date cleaning, formula updates, exception checks, and email formatting).
- **Automated Workflow Runtime**: < 1 second (< 0.0001 hours).
- **Weekly Time Saved**: 12.0 Hours / Week (~624 hours saved annually).

### 2. Software Development Speedup (*Measured Task Data*)
- **Baseline Estimated Development Time**: 25.0 Hours.
- **Optimized Development Time**: 17.5 Hours.
- **Measured Speedup**: **30.0% Improvement** (calculated via `scripts/impact_calculator.py` using tracked task data in `data/development_tasks.json`).

---

## 13. Optional Confluence Integration

The project includes an optional enterprise publishing module (`scripts/confluence_publisher.py`) to post reports directly to Atlassian Confluence Cloud portals via HTTPS REST API.

- **Optional Setup**: Managed in `.env` using your Confluence URL, email, and API token.
- **Graceful Fallback**: If credentials are missing, publishing is safely skipped without failing local report generation.

> Note: For REST API configuration details and payload structures, refer to [`docs/CONFLUENCE.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/CONFLUENCE.md).

---

## 14. Quick Explanation for Interviews & Presentations

If asked to describe this project in 30–60 seconds during an interview or presentation:

> *"I developed an automated operational reporting pipeline in Python and SQL that consolidates multi-department data across Operations, Sales, and Support. It ingests raw CSV files, validates data quality, stores clean records in SQLite, normalizes divergent status terms, and generates an 8-section interactive HTML report. To ensure 100% data correctness, I implemented an independent 5-level reconciliation framework that enforces mathematical accounting across all ingested records. The automation replaces 12 hours of weekly manual Excel reporting with a sub-second, error-free workflow."*

---

## 15. All Commands Quick Reference

| Command | Short Description | Purpose / When to Use |
| --- | --- | --- |
| `python main.py` | Runs full reporting workflow | Ingests CSVs, updates SQLite, runs reconciliation, and opens HTML report in browser. |
| `python scheduler.py` | Starts background scheduler | Runs daily background automation at configured schedule time (e.g., 09:00 AM). |
| `python scheduler.py --once` | Runs single schedule cycle | For quick schedule testing or automated CI/CD execution. |
| `python scripts/test_reports.py` | Runs automated test suite | Verifies 104 test assertions covering database, SQL, edge cases, and reports. |
| `python scripts/impact_calculator.py` | Displays efficiency metrics | Calculates 30% development speedup and 12 hours/week operational savings. |
| `python scratch/generate_data.py` | Regenerates test datasets | Produces 1,000+ record test CSV files with intentional invalid and duplicate rows. |
| `pip install -r requirements.txt` | Verifies Python environment | Confirms environment readiness (100% Python Standard Library used). |
| `Copy-Item .env.example .env` | Initializes `.env` file | Creates local environment configuration file from template in PowerShell. |

---

## Documentation Index

For deeper technical documentation, refer to the dedicated guides in `docs/`:

- [`docs/TECHNICAL_DETAILS.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/TECHNICAL_DETAILS.md) — Codebase map, DDL schemas, SQL views, and logging architecture.
- [`docs/SCHEDULER.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/SCHEDULER.md) — Scheduler loop mechanics, catch-up mode, and Windows Task Scheduler guide.
- [`docs/ENGINEERING_WORKFLOW.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/ENGINEERING_WORKFLOW.md) — Software engineering methodology, code review principles, and task audit trail.
- [`docs/TESTING.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/TESTING.md) — 104-assertion automated test suite and edge case verification.
- [`docs/CONFLUENCE.md`](file:///C:/Users/manik/Documents/workflow-automation-for-operational-reporting/docs/CONFLUENCE.md) — Confluence Cloud REST API publishing setup.