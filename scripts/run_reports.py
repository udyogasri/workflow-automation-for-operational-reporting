"""
run_reports.py
Executes SQL reporting queries against the SQLite database and prints
a readable terminal summary.

Phase 2 -- SQL Reporting for Operational Data.
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_project_root():
    """Return the project root directory (parent of scripts/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def setup_logger(project_root):
    """Configure logging to file and console."""
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_reports_{timestamp}.log")

    logger = logging.getLogger("run_reports")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info(f"Log file: {log_file}")
    return logger


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection(db_path):
    """Return a sqlite3 connection. Caller must close it."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # access columns by name
    return conn


def ensure_view(conn, sql_dir, logger):
    """Create/recreate the v_all_records view from reporting_queries.sql."""
    sql_path = os.path.join(sql_dir, "reporting_queries.sql")
    if not os.path.exists(sql_path):
        logger.error(f"Reporting SQL file not found: {sql_path}")
        sys.exit(1)

    with open(sql_path, "r", encoding="utf-8") as f:
        full_sql = f.read()

    # Extract the DROP VIEW and CREATE VIEW statements
    view_sql_lines = []
    capturing = False
    for line in full_sql.splitlines():
        if line.strip().upper().startswith("DROP VIEW"):
            capturing = True
        if capturing:
            view_sql_lines.append(line)
            if line.rstrip().endswith(";"):
                # Check if we finished the CREATE VIEW
                joined = "\n".join(view_sql_lines)
                if "CREATE VIEW" in joined.upper() and joined.rstrip().endswith(";"):
                    break

    view_sql = "\n".join(view_sql_lines)
    conn.executescript(view_sql)
    if logger:
        logger.debug("v_all_records view created/refreshed.")


# ---------------------------------------------------------------------------
# Query definitions
# ---------------------------------------------------------------------------
# Each query is defined inline (not parsed from the file) so that the Python
# script controls exactly what runs and can validate results.

OVERALL_SUMMARY_SQL = """
SELECT
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status_category = 'Pending'   THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status_category = 'Failed'    THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END)
        / MAX(COUNT(*), 1), 1
    )                                                           AS completion_pct
FROM v_all_records;
"""

SOURCE_SUMMARY_SQL = """
SELECT
    source,
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status_category = 'Pending'   THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status_category = 'Failed'    THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END)
        / MAX(COUNT(*), 1), 1
    )                                                           AS completion_pct,
    ROUND(SUM(target), 2)                                       AS total_target,
    ROUND(SUM(actual_value), 2)                                 AS total_actual,
    ROUND(
        CASE WHEN SUM(target) > 0
             THEN 100.0 * SUM(actual_value) / SUM(target)
             ELSE 0
        END, 1
    )                                                           AS achievement_pct
FROM v_all_records
GROUP BY source
ORDER BY source;
"""

TEAM_PERFORMANCE_SQL = """
SELECT
    source,
    team,
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status_category = 'Pending'   THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status_category = 'Failed'    THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END)
        / MAX(COUNT(*), 1), 1
    )                                                           AS completion_pct,
    ROUND(SUM(target), 2)                                       AS total_target,
    ROUND(SUM(actual_value), 2)                                 AS total_actual,
    ROUND(
        CASE WHEN SUM(target) > 0
             THEN 100.0 * SUM(actual_value) / SUM(target)
             ELSE 0
        END, 1
    )                                                           AS achievement_pct
FROM v_all_records
GROUP BY source, team
ORDER BY source, team;
"""

DEPARTMENT_PERFORMANCE_SQL = """
SELECT
    source,
    department,
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status_category = 'Pending'   THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status_category = 'Failed'    THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END)
        / MAX(COUNT(*), 1), 1
    )                                                           AS completion_pct,
    ROUND(SUM(target), 2)                                       AS total_target,
    ROUND(SUM(actual_value), 2)                                 AS total_actual,
    ROUND(
        CASE WHEN SUM(target) > 0
             THEN 100.0 * SUM(actual_value) / SUM(target)
             ELSE 0
        END, 1
    )                                                           AS achievement_pct
FROM v_all_records
GROUP BY source, department
ORDER BY source, department;
"""

DAILY_SUMMARY_SQL = """
SELECT
    date,
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status_category = 'Pending'   THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status_category = 'Failed'    THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN status_category = 'Completed' THEN 1 ELSE 0 END)
        / MAX(COUNT(*), 1), 1
    )                                                           AS completion_pct
FROM v_all_records
GROUP BY date
ORDER BY date;
"""

ATTENTION_REQUIRED_SQL = """
SELECT
    record_id,
    source,
    employee,
    team,
    date,
    status,
    status_category,
    target,
    actual_value,
    CASE
        WHEN status_category = 'Failed'
            THEN 'Failed / Lost / Escalated -- requires review'
        WHEN status_category = 'Pending'
            THEN 'Still pending -- not yet completed'
        WHEN status_category = 'Completed' AND target > 0 AND actual_value < 0.5 * target
            THEN 'Completed but actual < 50% of target'
        ELSE 'Unknown'
    END AS attention_reason
FROM v_all_records
WHERE status_category IN ('Failed', 'Pending')
   OR (status_category = 'Completed' AND target > 0 AND actual_value < 0.5 * target)
ORDER BY
    CASE status_category
        WHEN 'Failed'  THEN 1
        WHEN 'Pending' THEN 2
        ELSE 3
    END,
    date;
"""

DATA_QUALITY_SQL = """
SELECT
    source,
    COUNT(*)                                                    AS total_records,
    SUM(CASE WHEN status_category = 'Unknown' THEN 1 ELSE 0 END) AS unexpected_status,
    SUM(CASE WHEN target IS NULL THEN 1 ELSE 0 END)            AS null_target,
    SUM(CASE WHEN actual_value IS NULL THEN 1 ELSE 0 END)      AS null_actual,
    SUM(CASE WHEN employee IS NULL OR employee = '' THEN 1 ELSE 0 END) AS null_employee,
    SUM(CASE WHEN date IS NULL OR date = '' THEN 1 ELSE 0 END) AS null_date
FROM v_all_records
GROUP BY source
ORDER BY source;
"""


# ---------------------------------------------------------------------------
# Result validation helpers
# ---------------------------------------------------------------------------

def validate_summary_row(row, label, logger):
    """Validate a summary row for common issues."""
    issues = []

    total = row["total_records"]
    if total is None or total == 0:
        issues.append("total_records is zero or NULL")

    for col in ["completed", "pending", "failed"]:
        val = row[col]
        if val is not None and val < 0:
            issues.append(f"{col} is negative ({val})")

    # Check counts add up
    if total and total > 0:
        parts = (row["completed"] or 0) + (row["pending"] or 0) + (row["failed"] or 0)
        if parts != total:
            issues.append(
                f"Status counts ({parts}) do not add up to total ({total})"
            )

    pct = row["completion_pct"]
    if pct is not None and (pct < 0 or pct > 100):
        issues.append(f"completion_pct out of range ({pct})")

    ach = row.get("achievement_pct") if isinstance(row, dict) else (row["achievement_pct"] if "achievement_pct" in row.keys() else None)
    if ach is not None and ach < 0:
        issues.append(f"achievement_pct is negative ({ach})")

    for col in ["total_target", "total_actual"]:
        val = row.get(col) if isinstance(row, dict) else (row[col] if col in row.keys() else None)
        if val is not None and val < 0:
            issues.append(f"{col} is negative ({val})")

    if issues:
        for issue in issues:
            logger.warning(f"[{label}] Validation: {issue}")
    return issues


def safe_pct(numerator, denominator, decimals=1):
    """Calculate percentage avoiding division by zero."""
    if denominator is None or denominator == 0:
        return 0.0
    return round(100.0 * numerator / denominator, decimals)


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

DIVIDER = "=" * 72
SUB_DIVIDER = "-" * 72


def print_section(title):
    print()
    print(DIVIDER)
    print(f"  {title}")
    print(DIVIDER)


def print_kv(label, value, indent=2):
    """Print a key-value pair."""
    prefix = " " * indent
    print(f"{prefix}{label:30s}: {value}")


def print_table(rows, columns, col_widths=None):
    """Print rows as a simple text table."""
    if not rows:
        print("  (no data)")
        return

    if col_widths is None:
        col_widths = {}

    # Build format string
    parts = []
    for c in columns:
        w = col_widths.get(c, max(len(c), 12))
        parts.append(f"{{:<{w}}}")
    fmt = "  " + "  ".join(parts)

    # Header
    print(fmt.format(*columns))
    print("  " + "  ".join("-" * col_widths.get(c, max(len(c), 12)) for c in columns))

    for row in rows:
        vals = []
        for c in columns:
            v = row[c] if isinstance(row, sqlite3.Row) else row.get(c, "")
            if v is None:
                v = ""
            vals.append(str(v))
        print(fmt.format(*vals))


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def report_overall_summary(conn, logger):
    """1. Overall Operational Summary."""
    print_section("1. OVERALL OPERATIONAL SUMMARY")
    cursor = conn.execute(OVERALL_SUMMARY_SQL)
    row = cursor.fetchone()

    if row is None or row["total_records"] == 0:
        logger.warning("Overall summary returned no data.")
        print("  No data available.")
        return

    validate_summary_row(row, "Overall Summary", logger)

    print_kv("Total Records", row["total_records"])
    print_kv("Completed", row["completed"])
    print_kv("Pending", row["pending"])
    print_kv("Failed", row["failed"])
    print_kv("Completion %", f"{row['completion_pct']}%")


def report_source_summary(conn, logger):
    """2. Source-wise Summary."""
    print_section("2. SOURCE-WISE SUMMARY")
    cursor = conn.execute(SOURCE_SUMMARY_SQL)
    rows = cursor.fetchall()

    if not rows:
        logger.warning("Source summary returned no data.")
        print("  No data available.")
        return

    for row in rows:
        validate_summary_row(row, f"Source: {row['source']}", logger)

    columns = [
        "source", "total_records", "completed", "pending", "failed",
        "completion_pct", "total_target", "total_actual", "achievement_pct",
    ]
    widths = {
        "source": 12, "total_records": 8, "completed": 9, "pending": 7,
        "failed": 6, "completion_pct": 10, "total_target": 12,
        "total_actual": 12, "achievement_pct": 10,
    }
    print_table(rows, columns, widths)


def report_team_performance(conn, logger):
    """3. Team Performance."""
    print_section("3. TEAM PERFORMANCE")
    cursor = conn.execute(TEAM_PERFORMANCE_SQL)
    rows = cursor.fetchall()

    if not rows:
        logger.warning("Team performance returned no data.")
        print("  No data available.")
        return

    columns = [
        "source", "team", "total_records", "completed", "pending", "failed",
        "completion_pct", "total_target", "total_actual", "achievement_pct",
    ]
    widths = {
        "source": 12, "team": 16, "total_records": 8, "completed": 9,
        "pending": 7, "failed": 6, "completion_pct": 10,
        "total_target": 12, "total_actual": 12, "achievement_pct": 10,
    }
    print_table(rows, columns, widths)


def report_department_performance(conn, logger):
    """4. Department Performance."""
    print_section("4. DEPARTMENT PERFORMANCE")
    cursor = conn.execute(DEPARTMENT_PERFORMANCE_SQL)
    rows = cursor.fetchall()

    if not rows:
        logger.warning("Department performance returned no data.")
        print("  No data available.")
        return

    columns = [
        "source", "department", "total_records", "completed", "pending",
        "failed", "completion_pct", "total_target", "total_actual",
        "achievement_pct",
    ]
    widths = {
        "source": 12, "department": 20, "total_records": 8,
        "completed": 9, "pending": 7, "failed": 6, "completion_pct": 10,
        "total_target": 12, "total_actual": 12, "achievement_pct": 10,
    }
    print_table(rows, columns, widths)


def report_daily_summary(conn, logger):
    """5. Daily Summary."""
    print_section("5. DAILY SUMMARY")
    cursor = conn.execute(DAILY_SUMMARY_SQL)
    rows = cursor.fetchall()

    if not rows:
        logger.warning("Daily summary returned no data.")
        print("  No data available.")
        return

    columns = [
        "date", "total_records", "completed", "pending", "failed",
        "completion_pct",
    ]
    widths = {
        "date": 12, "total_records": 8, "completed": 9, "pending": 7,
        "failed": 6, "completion_pct": 10,
    }
    print_table(rows, columns, widths)


def report_attention_required(conn, logger):
    """6. Attention Required."""
    print_section("6. ATTENTION REQUIRED")
    cursor = conn.execute(ATTENTION_REQUIRED_SQL)
    rows = cursor.fetchall()

    if not rows:
        print("  No records require attention.")
        return

    print(f"  {len(rows)} record(s) require attention:\n")

    columns = [
        "record_id", "source", "employee", "status", "target",
        "actual_value", "attention_reason",
    ]
    widths = {
        "record_id": 10, "source": 12, "employee": 20, "status": 12,
        "target": 8, "actual_value": 12, "attention_reason": 45,
    }
    print_table(rows, columns, widths)

    # Count by category
    print()
    reasons = {}
    for row in rows:
        cat = row["status_category"]
        reasons[cat] = reasons.get(cat, 0) + 1
    for cat, cnt in sorted(reasons.items()):
        print_kv(f"  {cat}", cnt, indent=0)


def report_data_quality(conn, logger):
    """7. Data Quality Summary."""
    print_section("7. DATA QUALITY SUMMARY")
    cursor = conn.execute(DATA_QUALITY_SQL)
    rows = cursor.fetchall()

    if not rows:
        logger.warning("Data quality summary returned no data.")
        print("  No data available.")
        return

    columns = [
        "source", "total_records", "unexpected_status", "null_target",
        "null_actual", "null_employee", "null_date",
    ]
    widths = {
        "source": 12, "total_records": 8, "unexpected_status": 17,
        "null_target": 11, "null_actual": 11, "null_employee": 13,
        "null_date": 9,
    }
    print_table(rows, columns, widths)

    # Overall quality verdict
    total_issues = sum(
        (row["unexpected_status"] or 0) + (row["null_target"] or 0) +
        (row["null_actual"] or 0) + (row["null_employee"] or 0) +
        (row["null_date"] or 0)
        for row in rows
    )
    print()
    if total_issues == 0:
        print("  Data quality: GOOD -- no issues detected.")
    else:
        print(f"  Data quality: {total_issues} issue(s) detected.")
        logger.warning(f"Data quality: {total_issues} issue(s) found.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    project_root = get_project_root()
    logger = setup_logger(project_root)

    db_path = os.path.join(project_root, "database", "reporting.db")
    sql_dir = os.path.join(project_root, "sql")

    logger.info(DIVIDER)
    logger.info("Starting reporting process")
    logger.info(DIVIDER)

    conn = get_connection(db_path)
    try:
        # Create the unified view
        ensure_view(conn, sql_dir, logger)

        # Run all report sections
        report_overall_summary(conn, logger)
        report_source_summary(conn, logger)
        report_team_performance(conn, logger)
        report_department_performance(conn, logger)
        report_daily_summary(conn, logger)
        report_attention_required(conn, logger)
        report_data_quality(conn, logger)

        print()
        print(DIVIDER)
        print("  Reporting complete.")
        print(DIVIDER)

    finally:
        conn.close()

    logger.info("Reporting process completed.")


if __name__ == "__main__":
    main()
