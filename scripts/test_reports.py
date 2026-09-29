"""
Verification and edge-case testing for Phase 2 reporting.
This script:
  1. Manually verifies key calculations against raw data.
  2. Tests edge cases with temporary data in a copy of the database.
  3. Confirms the main database is untouched at the end.
"""

import sqlite3
import os
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "reporting.db")
TEST_DB_PATH = os.path.join(PROJECT_ROOT, "database", "reporting_test.db")

PASS = 0
FAIL = 0


def check(label, expected, actual):
    global PASS, FAIL
    if expected == actual:
        print(f"  PASS: {label}  (expected={expected}, got={actual})")
        PASS += 1
    else:
        print(f"  FAIL: {label}  (expected={expected}, got={actual})")
        FAIL += 1


def section(title):
    print()
    print(f"--- {title} ---")


# ===========================================================================
# PART 1: Manual verification against the real database
# ===========================================================================

def verify_calculations():
    section("MANUAL VERIFICATION")
    conn = sqlite3.connect(DB_PATH)

    # Total records
    ops = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    sls = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    sup = conn.execute("SELECT COUNT(*) FROM support").fetchone()[0]
    check("operations count", 50, ops)
    check("sales count", 50, sls)
    check("support count", 50, sup)
    check("total records", 150, ops + sls + sup)

    # Status counts -- operations
    ops_completed = conn.execute(
        "SELECT COUNT(*) FROM operations WHERE status = 'Completed'"
    ).fetchone()[0]
    ops_pending = conn.execute(
        "SELECT COUNT(*) FROM operations WHERE status = 'In Progress'"
    ).fetchone()[0]
    ops_failed = conn.execute(
        "SELECT COUNT(*) FROM operations WHERE status = 'Failed'"
    ).fetchone()[0]
    check("ops completed", 39, ops_completed)
    check("ops pending", 6, ops_pending)
    check("ops failed", 5, ops_failed)
    check("ops status total", 50, ops_completed + ops_pending + ops_failed)

    # Completion pct for operations = 39/50 * 100 = 78.0
    check("ops completion_pct", 78.0, round(100.0 * ops_completed / ops, 1))

    # Target/actual for operations
    ops_target = conn.execute("SELECT SUM(target) FROM operations").fetchone()[0]
    ops_actual = conn.execute("SELECT SUM(actual_value) FROM operations").fetchone()[0]
    check("ops total_target", 6795.0, ops_target)
    check("ops total_actual", 6271.0, ops_actual)
    check("ops achievement_pct", 92.3, round(100.0 * ops_actual / ops_target, 1))

    # Target/actual for sales revenue ($)
    sls_target = conn.execute("SELECT SUM(target) FROM sales").fetchone()[0]
    sls_actual = conn.execute("SELECT SUM(actual_value) FROM sales").fetchone()[0]
    check("sales total_target (revenue $)", 1569750.0, sls_target)
    check("sales total_actual (revenue $)", 1357100.0, sls_actual)
    check("sales revenue achievement_pct", 86.5, round(100.0 * sls_actual / sls_target, 1))

    # Target/actual for support tickets
    sup_target = conn.execute("SELECT SUM(target) FROM support").fetchone()[0]
    sup_actual = conn.execute("SELECT SUM(actual_value) FROM support").fetchone()[0]
    check("support total_target (tickets)", 649.0, sup_target)
    check("support total_actual (tickets)", 603.0, sup_actual)
    check("support ticket achievement_pct", 92.9, round(100.0 * sup_actual / sup_target, 1))

    # Sales status counts
    sls_completed = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE status = 'Closed'"
    ).fetchone()[0]
    sls_pending = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE status = 'Pipeline'"
    ).fetchone()[0]
    sls_failed = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE status = 'Lost'"
    ).fetchone()[0]
    check("sales completed (Closed)", 39, sls_completed)
    check("sales pending (Pipeline)", 6, sls_pending)
    check("sales failed (Lost)", 5, sls_failed)

    # Support status counts
    sup_resolved = conn.execute(
        "SELECT COUNT(*) FROM support WHERE status = 'Resolved'"
    ).fetchone()[0]
    sup_pending = conn.execute(
        "SELECT COUNT(*) FROM support WHERE status = 'Pending'"
    ).fetchone()[0]
    sup_escalated = conn.execute(
        "SELECT COUNT(*) FROM support WHERE status = 'Escalated'"
    ).fetchone()[0]
    check("support completed (Resolved)", 39, sup_resolved)
    check("support pending (Pending)", 6, sup_pending)
    check("support failed (Escalated)", 5, sup_escalated)

    # Overall completion = 117/150 = 78.0
    total_completed = ops_completed + sls_completed + sup_resolved
    check("overall completed", 117, total_completed)
    check("overall completion_pct", 78.0, round(100.0 * total_completed / 150, 1))

    # Mixed-unit prevention check: confirm overall_summary query has NO mixed-unit target/actual columns
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
    import run_reports
    conn.row_factory = sqlite3.Row
    run_reports.ensure_view(conn, os.path.join(PROJECT_ROOT, "sql"), None)
    overall_row = conn.execute(run_reports.OVERALL_SUMMARY_SQL).fetchone()
    check("overall_summary has no total_target column", False, "total_target" in overall_row.keys())
    check("overall_summary has no achievement_pct column", False, "achievement_pct" in overall_row.keys())

    # Verify a specific team: operations Team Alpha
    ta = conn.execute(
        "SELECT COUNT(*), "
        "SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END), "
        "SUM(target), SUM(actual_value) "
        "FROM operations WHERE team = 'Team Alpha'"
    ).fetchone()
    check("ops Team Alpha total", 17, ta[0])
    check("ops Team Alpha completed", 13, ta[1])
    check("ops Team Alpha target", 2940.0, ta[2])
    check("ops Team Alpha actual", 2723.0, ta[3])

    # Verify a date: 2026-09-01 should have 6 records all completed
    day1 = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT status FROM operations WHERE date = '2026-09-01'
            UNION ALL
            SELECT status FROM sales WHERE date = '2026-09-01'
            UNION ALL
            SELECT status FROM support WHERE date = '2026-09-01'
        )
    """).fetchone()[0]
    check("2026-09-01 total records", 6, day1)

    conn.close()


# ===========================================================================
# PART 2: Edge-case testing on a COPY of the database
# ===========================================================================

def create_view(conn):
    """Create the v_all_records view on the test database."""
    sql_path = os.path.join(PROJECT_ROOT, "sql", "reporting_queries.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        full_sql = f.read()

    view_sql_lines = []
    capturing = False
    for line in full_sql.splitlines():
        if line.strip().upper().startswith("DROP VIEW"):
            capturing = True
        if capturing:
            view_sql_lines.append(line)
            if line.rstrip().endswith(";"):
                joined = "\n".join(view_sql_lines)
                if "CREATE VIEW" in joined.upper() and joined.rstrip().endswith(";"):
                    break
    conn.executescript("\n".join(view_sql_lines))


def test_edge_cases():
    section("EDGE CASE TESTING (using test database copy)")

    # Make a copy
    shutil.copy2(DB_PATH, TEST_DB_PATH)
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row

    # --- Edge 1: Zero target ---
    section("Edge 1: Zero target")
    conn.execute(
        "INSERT INTO operations VALUES "
        "('EDGE-001','Test','Team Alpha','2026-09-26','Manufacturing','Completed',10,0,50,'Morning','zero target')"
    )
    conn.commit()
    create_view(conn)
    row = conn.execute(
        "SELECT target, actual_value FROM v_all_records WHERE record_id = 'EDGE-001'"
    ).fetchone()
    check("zero target record exists", 0.0, row["target"])
    check("zero target actual_value", 50.0, row["actual_value"])
    # Achievement pct with zero target should not cause division by zero
    row2 = conn.execute("""
        SELECT ROUND(
            CASE WHEN SUM(target) > 0
                 THEN 100.0 * SUM(actual_value) / SUM(target)
                 ELSE 0
            END, 1
        ) AS ach
        FROM v_all_records WHERE record_id = 'EDGE-001'
    """).fetchone()
    check("zero target achievement = 0 (safeguard)", 0.0, row2["ach"])

    # --- Edge 2: No pending records (insert only completed) ---
    section("Edge 2: Query with no pending results")
    pending_only_completed = conn.execute("""
        SELECT SUM(CASE WHEN status_category = 'Pending' THEN 1 ELSE 0 END) AS p
        FROM v_all_records WHERE source = 'operations' AND team = 'Team Beta'
          AND status_category = 'Completed'
    """).fetchone()
    check("no pending in completed filter", 0, pending_only_completed["p"])

    # --- Edge 3: No failed records query ---
    section("Edge 3: No failed records in filtered query")
    no_fail = conn.execute("""
        SELECT SUM(CASE WHEN status_category = 'Failed' THEN 1 ELSE 0 END) AS f
        FROM v_all_records WHERE date = '2026-09-01'
    """).fetchone()
    check("no failed on 2026-09-01", 0, no_fail["f"])

    # --- Edge 4: Empty result ---
    section("Edge 4: Empty query result")
    empty = conn.execute(
        "SELECT * FROM v_all_records WHERE record_id = 'NONEXISTENT'"
    ).fetchall()
    check("empty result set", 0, len(empty))

    # --- Edge 5: NULL value handling ---
    # The schema enforces NOT NULL on required columns (target, actual_value).
    # Test that the constraint works, and test NULLs in optional columns (shift, notes).
    section("Edge 5: NULL value handling")
    try:
        conn.execute(
            "INSERT INTO operations VALUES "
            "('EDGE-002','Test Null','Team Alpha','2026-09-26','Manufacturing','Completed',10,100,NULL,'Morning',NULL)"
        )
        check("NOT NULL constraint on actual_value", "should reject", "accepted")
    except sqlite3.IntegrityError:
        check("NOT NULL constraint on actual_value enforced", True, True)

    # Insert with NULL in optional columns (shift, notes are nullable)
    conn.execute(
        "INSERT INTO operations VALUES "
        "('EDGE-002','Test Null','Team Alpha','2026-09-26','Manufacturing','Completed',10,100,80,NULL,NULL)"
    )
    conn.commit()
    create_view(conn)
    row3 = conn.execute(
        "SELECT record_id, actual_value FROM v_all_records WHERE record_id = 'EDGE-002'"
    ).fetchone()
    check("record with NULL optional fields exists", "EDGE-002", row3["record_id"])
    check("actual_value is not NULL", 80.0, row3["actual_value"])

    # --- Edge 6: Unexpected status ---
    section("Edge 6: Unexpected status value")
    conn.execute(
        "INSERT INTO operations VALUES "
        "('EDGE-003','Test Status','Team Alpha','2026-09-26','Manufacturing','Cancelled',10,100,90,'Morning','weird status')"
    )
    conn.commit()
    create_view(conn)
    row4 = conn.execute(
        "SELECT status_category FROM v_all_records WHERE record_id = 'EDGE-003'"
    ).fetchone()
    check("unexpected status maps to Unknown", "Unknown", row4["status_category"])

    # Data quality should flag it
    dq = conn.execute("""
        SELECT SUM(CASE WHEN status_category = 'Unknown' THEN 1 ELSE 0 END) AS u
        FROM v_all_records
    """).fetchone()
    check("data quality catches unknown status", True, dq["u"] >= 1)

    # --- Edge 7: Target greater than actual (normal underperformance) ---
    section("Edge 7: Target > Actual")
    conn.execute(
        "INSERT INTO operations VALUES "
        "('EDGE-004','Test Under','Team Beta','2026-09-26','Logistics','Completed',10,200,50,'Morning','underperform')"
    )
    conn.commit()
    create_view(conn)
    row5 = conn.execute(
        "SELECT target, actual_value FROM v_all_records WHERE record_id = 'EDGE-004'"
    ).fetchone()
    check("target > actual record exists", True, row5["target"] > row5["actual_value"])
    # This should appear in attention_required (50 < 50% of 200 = 100)
    attn = conn.execute("""
        SELECT attention_reason FROM (
            SELECT record_id,
                CASE
                    WHEN status_category = 'Failed'
                        THEN 'Failed'
                    WHEN status_category = 'Pending'
                        THEN 'Pending'
                    WHEN status_category = 'Completed' AND target > 0 AND actual_value < 0.5 * target
                        THEN 'Underperformed'
                    ELSE 'None'
                END AS attention_reason
            FROM v_all_records
        ) WHERE record_id = 'EDGE-004'
    """).fetchone()
    check("underperformance flagged", "Underperformed", attn["attention_reason"])

    # --- Edge 8: Actual greater than target (overperformance) ---
    section("Edge 8: Actual > Target")
    conn.execute(
        "INSERT INTO operations VALUES "
        "('EDGE-005','Test Over','Team Gamma','2026-09-26','Quality Control','Completed',10,50,150,'Morning','overperform')"
    )
    conn.commit()
    create_view(conn)
    row6 = conn.execute(
        "SELECT target, actual_value FROM v_all_records WHERE record_id = 'EDGE-005'"
    ).fetchone()
    check("actual > target record", True, row6["actual_value"] > row6["target"])
    ach = round(100.0 * row6["actual_value"] / row6["target"], 1)
    check("overperformance achievement > 100%", True, ach > 100.0)

    conn.close()

    # Clean up test database
    os.remove(TEST_DB_PATH)
    print()
    print("  Test database removed.")


# ===========================================================================
# PART 3: Confirm main database is untouched
# ===========================================================================

def verify_main_db():
    section("MAIN DATABASE INTEGRITY CHECK")
    conn = sqlite3.connect(DB_PATH)
    ops = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    sls = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    sup = conn.execute("SELECT COUNT(*) FROM support").fetchone()[0]
    check("operations still 50", 50, ops)
    check("sales still 50", 50, sls)
    check("support still 50", 50, sup)
    conn.close()


# ===========================================================================
# PART 4: Phase 3 -- Report Generation Tests
# ===========================================================================

def test_report_generation():
    """Test Phase 3 report generation."""
    import time
    import logging as _logging

    sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
    import generate_report

    # Quiet logger for tests
    tlogger = _logging.getLogger("test_generate")
    tlogger.setLevel(_logging.WARNING)
    if not tlogger.handlers:
        tlogger.addHandler(_logging.NullHandler())

    # --- Test 1: Report file is generated ---
    section("Phase 3 Test 1: Report file is generated")
    report_path = generate_report.generate_report(PROJECT_ROOT, tlogger)
    check("report_path is not None", True, report_path is not None)
    if report_path:
        check("report file exists", True, os.path.exists(report_path))

    # --- Test 2: Report filename format ---
    section("Phase 3 Test 2: Report filename format")
    if report_path:
        basename = os.path.basename(report_path)
        check("filename starts with operational_report_",
              True, basename.startswith("operational_report_"))
        check("filename ends with .html",
              True, basename.endswith(".html"))

    # --- Test 3: Report contains required sections ---
    section("Phase 3 Test 3: Report contains required sections")
    html = ""
    if report_path:
        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()
        required_sections = [
            "1. Executive Summary",
            "2. Source-wise Summary",
            "3. Team Performance",
            "4. Department Performance",
            "5. Daily Summary",
            "6. Attention Required",
            "7. Data Quality",
            "8. Process Summary",
        ]
        for sec in required_sections:
            check(f"contains '{sec}'", True, sec in html)

    # --- Test 4: Report contains DB-calculated values ---
    section("Phase 3 Test 4: Report values match DB")
    if report_path and html:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        generate_report.ensure_view(
            conn, os.path.join(PROJECT_ROOT, "sql"), tlogger,
        )
        row = conn.execute(generate_report.OVERALL_SUMMARY_SQL).fetchone()
        total = row["total_records"]
        completed = row["completed"]
        pending = row["pending"]
        failed = row["failed"]
        attn_count = len(
            conn.execute(generate_report.ATTENTION_REQUIRED_SQL).fetchall()
        )
        conn.close()

        check(f"total ({total}) in report", True, f">{total}<" in html)
        check(f"completed ({completed}) in report", True, f">{completed}<" in html)
        check(f"pending ({pending}) in report", True, f">{pending}<" in html)
        check(f"failed ({failed}) in report", True, f">{failed}<" in html)
        check(f"attention ({attn_count}) in report", True, str(attn_count) in html)

    # --- Test 5: Multiple runs produce separate reports ---
    section("Phase 3 Test 5: Separate reports per run")
    time.sleep(1)
    report_path_2 = generate_report.generate_report(PROJECT_ROOT, tlogger)
    if report_path and report_path_2:
        check("different report paths", True, report_path != report_path_2)
        check("second report exists", True, os.path.exists(report_path_2))

    # --- Test 6: Execution log exists ---
    section("Phase 3 Test 6: Execution log exists")
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    main_logs = [f for f in os.listdir(log_dir) if f.startswith("main_")]
    check("at least one main_ log", True, len(main_logs) >= 1)

    # Clean up test reports
    for p in [report_path, report_path_2]:
        if p and os.path.exists(p):
            os.remove(p)


# ===========================================================================
# PART 5: Reconciliation Test
# ===========================================================================

def test_reconciliation():
    """Test multi-level reconciliation module."""
    section("Phase 4 Test: Multi-Level Reconciliation Audit")
    import reconcile
    rec_result = reconcile.reconcile_all(PROJECT_ROOT)
    check("multi-level reconciliation verdict = True", True, rec_result)


# ===========================================================================
# PART 6: Impact Calculator Test
# ===========================================================================

# ===========================================================================
# PART 6: Impact Calculator Test
# ===========================================================================

def test_impact_calculator():
    """Test programmatic impact calculator module."""
    section("Phase 4 Test: Impact Calculator Verification")
    import impact_calculator

    # Test 1: Scenario baseline mode
    ts_scenario = impact_calculator.calculate_time_savings(automated_duration_seconds=0.15, mode="SCENARIO_BASELINE")
    check("scenario mode weekly_hours_saved = 12.0", 12.0, ts_scenario["weekly_hours_saved"])
    check("scenario mode annual_hours_saved = 624.0", 624.0, ts_scenario["annual_hours_saved"])
    check("scenario mode label", "SCENARIO-MODELED BASELINE", ts_scenario["status_label"])

    # Test 2: Measured mode
    ts_measured = impact_calculator.calculate_time_savings(manual_baseline={"task1": 5.0, "task2": 5.0}, automated_duration_seconds=0.15, mode="MEASURED")
    check("measured mode weekly_hours_saved", 10.0, ts_measured["weekly_hours_saved"])
    check("measured mode status label", "MEASURED", ts_measured["status_label"])

    # Test 3: Dev speedup calculations
    ds_scenario = impact_calculator.calculate_dev_speedup(mode="SCENARIO_MODELED")
    ds_measured = impact_calculator.calculate_dev_speedup(mode="MEASURED")
    check("dev speedup_pct = 30.0%", 30.0, ds_scenario["speedup_pct"])
    check("measured dev tasks detected", True, ds_measured["task_count"] > 0)

    # Test 4: Zero baseline protection
    ts_zero = impact_calculator.calculate_time_savings(manual_baseline={"task1": 0.0}, automated_duration_seconds=0.15)
    check("zero baseline efficiency_gain_pct does not crash", 0.0, ts_zero["efficiency_gain_pct"])


# ===========================================================================
# PART 7: Confluence Publisher Tests
# ===========================================================================

def test_confluence():
    """Test Confluence Publisher module."""
    section("Phase 4 Test: Confluence Publisher Integration")
    import confluence_publisher

    # Test 1: Missing credentials -> skips safely
    orig_url = os.environ.pop("CONFLUENCE_BASE_URL", None)
    res_skipped = confluence_publisher.publish_to_confluence("Test Page", "<p>Test</p>")
    check("missing Confluence credentials skips safely (returns True)", True, res_skipped)

    # Test 2: Invalid credentials -> fails safely with HTTP error log
    os.environ["CONFLUENCE_BASE_URL"] = "https://invalid-confluence-domain-test.atlassian.net"
    os.environ["CONFLUENCE_EMAIL"] = "invalid@user.com"
    os.environ["CONFLUENCE_API_TOKEN"] = "invalid_token_12345"
    os.environ["CONFLUENCE_SPACE_KEY"] = "INVALID"
    res_failed = confluence_publisher.publish_to_confluence("Test Page", "<p>Test</p>")
    check("invalid Confluence credentials returns False safely without crash", False, res_failed)

    # Clean up test env vars
    os.environ.pop("CONFLUENCE_BASE_URL", None)
    os.environ.pop("CONFLUENCE_EMAIL", None)
    os.environ.pop("CONFLUENCE_API_TOKEN", None)
    os.environ.pop("CONFLUENCE_SPACE_KEY", None)
    if orig_url:
        os.environ["CONFLUENCE_BASE_URL"] = orig_url


# ===========================================================================

def main():
    print("=" * 60)
    print("Verification and Edge-Case Testing (Phases 1-4 Complete)")
    print("=" * 60)

    verify_calculations()
    test_edge_cases()
    verify_main_db()
    test_report_generation()
    test_reconciliation()
    test_impact_calculator()
    test_confluence()
    verify_main_db()

    print()
    print("=" * 60)
    print(f"RESULTS:  {PASS} passed,  {FAIL} failed")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
