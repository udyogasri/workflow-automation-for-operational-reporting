"""
main.py
End-to-end entry point for Workflow Automation for Operational Reporting.

Executes the complete workflow:
  1. Verify CSV source files exist.
  2. Run Phase 1 data loading/validation (load_data).
  3. Confirm database loading completed.
  4. Run Phase 2 SQL reporting (run_reports) -- terminal summary.
  5. Generate Phase 3 standardized HTML report (generate_report).
  6. Create an execution log.
  7. Display a concise completion summary.

Reuses existing scripts via imports -- does not duplicate logic.
"""

import os
import sys
import logging
import webbrowser
from datetime import datetime

# Add scripts/ to the path so we can import the existing modules.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import setup_database
import load_data
import run_reports
import reconcile
import generate_report
import confluence_publisher


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def setup_logger():
    """Configure a single execution logger for main.py."""
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"main_{timestamp}.log")

    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, log_file


# ---------------------------------------------------------------------------
# Workflow steps
# ---------------------------------------------------------------------------

CSV_FILES = ["operations.csv", "sales.csv", "support.csv"]


def step_verify_sources(logger):
    """Step 1: Verify required CSV files exist."""
    logger.info("Step 1: Verifying source CSV files")
    data_dir = os.path.join(PROJECT_ROOT, "data")
    missing = []
    for csv_file in CSV_FILES:
        path = os.path.join(data_dir, csv_file)
        if os.path.exists(path):
            logger.info(f"  Found: {csv_file}")
        else:
            logger.error(f"  MISSING: {csv_file}")
            missing.append(csv_file)
    if missing:
        logger.error(f"Missing source files: {missing}")
        raise FileNotFoundError(f"Missing CSV files: {', '.join(missing)}")
    logger.info("  All source files verified.")


def step_setup_database(logger):
    """Step 2a: Ensure database and schema exist."""
    logger.info("Step 2a: Setting up database")
    db_path = os.path.join(PROJECT_ROOT, "database", "reporting.db")
    if os.path.exists(db_path):
        logger.info("  Database already exists -- skipping creation.")
    else:
        setup_database.setup_database()
        logger.info("  Database created.")


def step_load_data(logger):
    """Step 2b: Run Phase 1 data loading/validation."""
    logger.info("Step 2b: Loading and validating CSV data")

    # Clear any existing handlers on the load_data logger to avoid duplicates
    ld_logger = logging.getLogger("load_data")
    ld_logger.handlers.clear()

    load_data.main()
    logger.info("  Data loading completed.")


def step_confirm_database(logger):
    """Step 3: Confirm database has data."""
    logger.info("Step 3: Confirming database contents")
    import sqlite3
    db_path = os.path.join(PROJECT_ROOT, "database", "reporting.db")
    conn = sqlite3.connect(db_path)
    counts = {}
    for table in ["operations", "sales", "support"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        counts[table] = count
        logger.info(f"  {table}: {count} records")
    conn.close()

    total = sum(counts.values())
    if total == 0:
        raise RuntimeError("Database is empty after loading. Aborting.")
    logger.info(f"  Total: {total} records")
    return counts


def step_run_reports(logger):
    """Step 4: Run Phase 2 SQL reporting (terminal summary)."""
    logger.info("Step 4: Running SQL reporting")

    # Clear any existing handlers on the run_reports logger to avoid duplicates
    rr_logger = logging.getLogger("run_reports")
    rr_logger.handlers.clear()

    run_reports.main()
    logger.info("  SQL reporting completed.")


def step_generate_report(logger):
    """Step 5: Generate Phase 3 HTML report and open in browser."""
    logger.info("Step 5: Generating operational report")
    report_path = generate_report.generate_report(PROJECT_ROOT, logger)
    if report_path is None:
        raise RuntimeError("Report generation failed.")
    logger.info(f"  Report saved: {report_path}")
    
    # Automatically open the generated HTML report in the default web browser
    try:
        abs_report_path = os.path.abspath(report_path)
        clean_path = abs_report_path.replace("\\", "/")
        webbrowser.open(f"file:///{clean_path}")
        logger.info(f"  Opened report in browser: {abs_report_path}")
    except Exception as e:
        logger.warning(f"  Could not automatically open browser: {e}")

    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start_time = datetime.now()
    logger, log_file = setup_logger()

    divider = "=" * 60
    logger.info(divider)
    logger.info("WORKFLOW AUTOMATION FOR OPERATIONAL REPORTING")
    logger.info(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(divider)

    report_path = None
    status = "FAILED"

    try:
        # Step 1 -- Verify sources
        step_verify_sources(logger)

        # Step 2 -- Database setup + data loading
        step_setup_database(logger)
        step_load_data(logger)

        # Step 3 -- Confirm database
        counts = step_confirm_database(logger)

        # Step 4 -- SQL reporting (terminal)
        step_run_reports(logger)

        # Step 4b -- Multi-level data reconciliation
        logger.info("Step 4b: Performing Multi-Level Data Reconciliation")
        reconciled = reconcile.reconcile_all(PROJECT_ROOT, logger)
        if not reconciled:
            raise RuntimeError("Data reconciliation failed! Aborting report generation.")

        # Step 5 -- HTML report generation
        report_path = step_generate_report(logger)

        # Step 5b -- Optional Confluence publishing
        logger.info("Step 5b: Checking Confluence publishing configuration")
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as rf:
                report_html = rf.read()
            confluence_publisher.publish_to_confluence(
                title=f"Operational Report - {datetime.now().strftime('%Y-%m-%d')}",
                html_content=report_html,
                logger=logger
            )

        status = "SUCCESS"

    except FileNotFoundError as e:
        logger.error(f"Source file error: {e}")
        print(f"\nERROR: {e}")
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"\nERROR: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nERROR: {e}")

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(divider)
    logger.info("EXECUTION SUMMARY")
    logger.info(divider)
    logger.info(f"  Status   : {status}")
    logger.info(f"  Duration : {duration:.2f} seconds")
    if report_path:
        logger.info(f"  Report   : {report_path}")
    logger.info(f"  Log      : {log_file}")
    logger.info(divider)

    print()
    print(divider)
    print(f"  Status   : {status}")
    print(f"  Duration : {duration:.2f} seconds")
    if report_path:
        print(f"  Report   : {report_path}")
    print(f"  Log      : {log_file}")
    print(divider)

    if status != "SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
