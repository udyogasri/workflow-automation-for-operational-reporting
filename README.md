# Workflow Automation for Operational Reporting

This project automates daily reporting for an operations team. It reads data from three team files (Operations, Sales, and Support), cleans the data, saves it in a database, calculates report numbers, and creates a report page that opens automatically in your web browser.

---

## Quick Start

Run the entire workflow with one command:

```bash
python main.py
```

Running this command executes the full process in under 1 second.

---

## How the Workflow Works (Start to End)

The process runs automatically through 5 simple steps:

1. **START: Read Data Files (`data/`)**
   The process starts by reading three CSV data files from the `data/` folder:
   - `operations.csv` (Manufacturing and Logistics output)
   - `sales.csv` (Sales deals and revenue)
   - `support.csv` (Customer support tickets)

2. **Check & Clean Data (`scripts/load_data.py`)**
   The script checks every row for errors (missing fields, bad dates, or invalid numbers). Bad rows are logged in `logs/` and skipped safely.

3. **Save to Database (`database/reporting.db`)**
   Clean data is saved into a local SQLite database. Statuses from different teams are mapped into standard terms (`Completed`, `Pending`, `Failed`).

4. **Calculate Results & Check Accuracy (`scripts/run_reports.py` & `scripts/reconcile.py`)**
   The system runs SQL queries to summarize targets and actual numbers by department. A Python auditor independently checks the numbers to guarantee accuracy.

5. **END: Open Report in Browser (`reports/`)**
   An HTML report file is created in the `reports/` folder and opens automatically in your web browser.

---

## Project Structure

- [`main.py`](main.py): Runs the complete workflow from start to end.
- [`data/`](data/): Contains the three input CSV data files (`operations.csv`, `sales.csv`, `support.csv`).
- [`database/`](database/): Stores the SQLite database file (`reporting.db`).
- [`scripts/`](scripts/): Python scripts for loading data, running SQL reports, checking accuracy, generating HTML reports, and testing.
- [`sql/`](sql/): SQL files defining database tables ([`schema.sql`](sql/schema.sql)) and reporting queries ([`reporting_queries.sql`](sql/reporting_queries.sql)).
- [`reports/`](reports/): Stores generated HTML reports (opened automatically in your browser).
- [`logs/`](logs/): Stores execution log files.
- [`docs/`](docs/): Extra documentation, runbooks, and workflow guides ([`CONFLUENCE_DOCS.md`](docs/CONFLUENCE_DOCS.md)).

---

## Data Units by Department

To keep calculations correct, each team uses its own unit of measurement:
- **Operations**: Number of physical items produced (Output Units).
- **Sales**: Money earned in dollars (Revenue $).
- **Support**: Number of resolved support issues (Ticket Count).

---

## How to Run Commands

### 1. Run Complete Workflow
```bash
python main.py
```

### 2. Run All 85 Automated Tests
```bash
python scripts/test_reports.py
```

---

## Optional Confluence Publishing

To send reports to Atlassian Confluence, set your credentials before running:

```powershell
$env:CONFLUENCE_BASE_URL="https://your-domain.atlassian.net"
$env:CONFLUENCE_EMAIL="your-email@example.com"
$env:CONFLUENCE_API_TOKEN="your-api-token"
$env:CONFLUENCE_SPACE_KEY="OPS"

python main.py
```
*(If no credentials are set, the script skips Confluence publishing safely without errors).*

---

## Requirement Summary

| Requirement | What It Does | Key File |
|---|---|---|
| **Multiple Data Sources** | Ingests 3 CSV files (Ops, Sales, Support) | [`data/*.csv`](data/) |
| **Python Automation** | Runs end-to-end workflow in under 1 second | [`main.py`](main.py) |
| **HTML Report** | Generates web report and opens in browser | [`scripts/generate_report.py`](scripts/generate_report.py) |
| **SQL Reporting** | Groups metrics by team and department | [`sql/reporting_queries.sql`](sql/reporting_queries.sql) |
| **Data Reconciliation** | Verifies 100% accuracy between CSV, DB, and SQL | [`scripts/reconcile.py`](scripts/reconcile.py) |
| **Automated Testing** | Verifies code with 85 test assertions | [`scripts/test_reports.py`](scripts/test_reports.py) |