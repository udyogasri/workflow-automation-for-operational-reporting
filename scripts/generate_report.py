"""
generate_report.py
Generates a standardized HTML operational report from the existing
Phase 2 SQL reporting results.

Reuses SQL queries and helpers from run_reports.py -- does NOT duplicate
the reporting logic.
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime

# Import Phase 2 query constants and helpers so we don't duplicate them.
# This file lives in scripts/, same as run_reports.py.
from run_reports import (
    OVERALL_SUMMARY_SQL,
    SOURCE_SUMMARY_SQL,
    TEAM_PERFORMANCE_SQL,
    DEPARTMENT_PERFORMANCE_SQL,
    DAILY_SUMMARY_SQL,
    ATTENTION_REQUIRED_SQL,
    DATA_QUALITY_SQL,
    get_connection,
    ensure_view,
    validate_summary_row,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def html_escape(text):
    """Escape special HTML characters."""
    if text is None:
        return ""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_num(value, decimals=2):
    """Format a number with commas and decimal places."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_pct(value):
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value}%"


def build_table(headers, rows, col_keys=None):
    """Build an HTML table string from headers and rows (sqlite3.Row list)."""
    if col_keys is None:
        col_keys = headers

    lines = ['<table>', '<thead><tr>']
    for h in headers:
        lines.append(f'<th>{html_escape(h)}</th>')
    lines.append('</tr></thead>')
    lines.append('<tbody>')

    if not rows:
        lines.append(
            f'<tr><td colspan="{len(headers)}" '
            f'style="text-align:center;">No data available</td></tr>'
        )
    else:
        for row in rows:
            lines.append('<tr>')
            for k in col_keys:
                val = row[k] if isinstance(row, sqlite3.Row) else row.get(k, "")
                lines.append(f'<td>{html_escape(val)}</td>')
            lines.append('</tr>')

    lines.append('</tbody></table>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report data collection (reuses Phase 2 queries)
# ---------------------------------------------------------------------------

def collect_report_data(conn, logger):
    """
    Execute all Phase 2 queries and return results as a dictionary.
    Returns None if a critical query fails.
    """
    data = {}

    try:
        # 1. Overall summary
        row = conn.execute(OVERALL_SUMMARY_SQL).fetchone()
        if row is None or row["total_records"] == 0:
            logger.error("Overall summary returned no data.")
            return None
        validate_summary_row(row, "Overall Summary", logger)
        data["overall"] = dict(row)

        # 2. Source-wise summary
        rows = conn.execute(SOURCE_SUMMARY_SQL).fetchall()
        for r in rows:
            validate_summary_row(r, f"Source: {r['source']}", logger)
        data["sources"] = [dict(r) for r in rows]

        # 3. Team performance
        data["teams"] = [dict(r) for r in conn.execute(TEAM_PERFORMANCE_SQL).fetchall()]

        # 4. Department performance
        data["departments"] = [
            dict(r) for r in conn.execute(DEPARTMENT_PERFORMANCE_SQL).fetchall()
        ]

        # 5. Daily summary
        data["daily"] = [dict(r) for r in conn.execute(DAILY_SUMMARY_SQL).fetchall()]

        # 6. Attention required
        data["attention"] = [
            dict(r) for r in conn.execute(ATTENTION_REQUIRED_SQL).fetchall()
        ]

        # 7. Data quality
        data["quality"] = [dict(r) for r in conn.execute(DATA_QUALITY_SQL).fetchall()]

        # Date range
        if data["daily"]:
            data["date_min"] = data["daily"][0]["date"]
            data["date_max"] = data["daily"][-1]["date"]
        else:
            data["date_min"] = "N/A"
            data["date_max"] = "N/A"

    except sqlite3.Error as e:
        logger.error(f"SQL error during data collection: {e}")
        return None

    return data


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

REPORT_CSS = """
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    margin: 30px auto;
    max-width: 1100px;
    color: #333;
    background: #f9f9f9;
}
h1 { color: #1a5276; border-bottom: 3px solid #1a5276; padding-bottom: 8px; }
h2 { color: #2c3e50; margin-top: 35px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0 20px 0;
    background: #fff;
}
th {
    background: #1a5276;
    color: #fff;
    padding: 8px 10px;
    text-align: left;
    font-size: 0.9em;
}
td {
    padding: 6px 10px;
    border-bottom: 1px solid #e0e0e0;
    font-size: 0.9em;
}
tr:nth-child(even) { background: #f4f6f7; }
.kv-table td:first-child { font-weight: bold; width: 220px; }
.summary-box {
    background: #fff;
    border: 1px solid #d5d8dc;
    border-left: 4px solid #1a5276;
    padding: 15px 20px;
    margin: 12px 0;
}
.good { color: #27ae60; font-weight: bold; }
.warn { color: #e67e22; font-weight: bold; }
.fail { color: #c0392b; font-weight: bold; }
.meta { color: #888; font-size: 0.85em; }
"""


def generate_html(data, generation_time, duration_seconds):
    """Build the full HTML report string from collected data."""
    o = data["overall"]

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en"><head><meta charset="UTF-8">')
    parts.append("<title>Operational Report</title>")
    parts.append(f"<style>{REPORT_CSS}</style>")
    parts.append("</head><body>")

    # Title
    parts.append("<h1>Operational Report</h1>")
    parts.append(f'<p class="meta">Report Generated: {generation_time}</p>')
    parts.append(
        f'<p class="meta">Reporting Period: {data["date_min"]} to {data["date_max"]}</p>'
    )

    # ---- 1. Executive Summary ----
    parts.append("<h2>1. Executive Summary</h2>")
    parts.append('<div class="summary-box"><table class="kv-table">')
    kv_rows = [
        ("Total Records", o["total_records"]),
        ("Completed", o["completed"]),
        ("Pending", o["pending"]),
        ("Failed", o["failed"]),
        ("Completion Rate", fmt_pct(o["completion_pct"])),
    ]
    for label, val in kv_rows:
        parts.append(f"<tr><td>{html_escape(label)}</td><td>{html_escape(val)}</td></tr>")
    parts.append("</table></div>")

    # ---- 2. Source-wise Summary ----
    parts.append("<h2>2. Source-wise Summary</h2>")
    src_headers = [
        "Source", "Total", "Completed", "Pending", "Failed",
        "Completion %", "Target", "Actual", "Achievement %",
    ]
    src_keys = [
        "source", "total_records", "completed", "pending", "failed",
        "completion_pct", "total_target", "total_actual", "achievement_pct",
    ]
    parts.append(build_table(src_headers, data["sources"], src_keys))

    # ---- 3. Team Performance ----
    parts.append("<h2>3. Team Performance</h2>")
    team_headers = [
        "Source", "Team", "Total", "Completed", "Pending", "Failed",
        "Completion %", "Target", "Actual", "Achievement %",
    ]
    team_keys = [
        "source", "team", "total_records", "completed", "pending", "failed",
        "completion_pct", "total_target", "total_actual", "achievement_pct",
    ]
    parts.append(build_table(team_headers, data["teams"], team_keys))

    # ---- 4. Department Performance ----
    parts.append("<h2>4. Department Performance</h2>")
    dept_headers = [
        "Source", "Department", "Total", "Completed", "Pending", "Failed",
        "Completion %", "Target", "Actual", "Achievement %",
    ]
    dept_keys = [
        "source", "department", "total_records", "completed", "pending", "failed",
        "completion_pct", "total_target", "total_actual", "achievement_pct",
    ]
    parts.append(build_table(dept_headers, data["departments"], dept_keys))

    # ---- 5. Daily Summary ----
    parts.append("<h2>5. Daily Summary</h2>")
    daily_headers = ["Date", "Total", "Completed", "Pending", "Failed", "Completion %"]
    daily_keys = ["date", "total_records", "completed", "pending", "failed", "completion_pct"]
    parts.append(build_table(daily_headers, data["daily"], daily_keys))

    # ---- 6. Attention Required ----
    parts.append("<h2>6. Attention Required</h2>")
    attn = data["attention"]
    if attn:
        parts.append(f'<p><strong>{len(attn)}</strong> record(s) require attention.</p>')
        attn_headers = [
            "Record ID", "Source", "Employee", "Team", "Date",
            "Status", "Target", "Actual", "Reason",
        ]
        attn_keys = [
            "record_id", "source", "employee", "team", "date",
            "status", "target", "actual_value", "attention_reason",
        ]
        parts.append(build_table(attn_headers, attn, attn_keys))
    else:
        parts.append('<p class="good">No records require attention.</p>')

    # ---- 7. Data Quality ----
    parts.append("<h2>7. Data Quality</h2>")
    dq_headers = [
        "Source", "Total Records", "Unexpected Status", "Null Target",
        "Null Actual", "Null Employee", "Null Date",
    ]
    dq_keys = [
        "source", "total_records", "unexpected_status", "null_target",
        "null_actual", "null_employee", "null_date",
    ]
    parts.append(build_table(dq_headers, data["quality"], dq_keys))

    total_issues = sum(
        (r.get("unexpected_status") or 0) + (r.get("null_target") or 0) +
        (r.get("null_actual") or 0) + (r.get("null_employee") or 0) +
        (r.get("null_date") or 0)
        for r in data["quality"]
    )
    if total_issues == 0:
        parts.append('<p class="good">Data quality: GOOD -- no issues detected.</p>')
    else:
        parts.append(f'<p class="warn">Data quality: {total_issues} issue(s) detected.</p>')

    # ---- 8. Process Summary ----
    parts.append("<h2>8. Process Summary</h2>")
    parts.append('<div class="summary-box"><table class="kv-table">')
    source_names = ", ".join(r["source"] for r in data["sources"]) if data["sources"] else "N/A"
    proc_rows = [
        ("Data Sources Processed", source_names),
        ("Total Records Processed", o["total_records"]),
        ("Report Generated At", generation_time),
        ("Generation Duration", f"{duration_seconds:.2f} seconds"),
        ("Report Status", "Completed"),
    ]
    for label, val in proc_rows:
        parts.append(f"<tr><td>{html_escape(label)}</td><td>{html_escape(val)}</td></tr>")
    parts.append("</table></div>")

    parts.append("</body></html>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API (called by main.py)
# ---------------------------------------------------------------------------

def generate_report(project_root, logger):
    """
    Generate the HTML operational report.
    Returns the report file path on success, or None on failure.
    """
    db_path = os.path.join(project_root, "database", "reporting.db")
    sql_dir = os.path.join(project_root, "sql")
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    start_time = datetime.now()
    generation_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    try:
        ensure_view(conn, sql_dir, logger)
        data = collect_report_data(conn, logger)
    finally:
        conn.close()

    if data is None:
        logger.error("Report generation aborted -- no data collected.")
        return None

    duration = (datetime.now() - start_time).total_seconds()

    html = generate_html(data, generation_time, duration)

    filename = f"operational_report_{start_time.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    report_path = os.path.join(reports_dir, filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Report generated: {report_path}")
    return report_path


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    project_root = get_project_root()

    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"generate_report_{timestamp}.log")

    logger = logging.getLogger("generate_report")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)

    path = generate_report(project_root, logger)
    if path:
        print(f"Report saved: {path}")
    else:
        print("Report generation failed.")
        sys.exit(1)
