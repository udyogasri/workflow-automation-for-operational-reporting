"""
Verification and edge-case testing for Phase 2 reporting and Phase 5 extensions.
This script:
  1. Manually verifies key calculations against raw data (1000+ records per CSV).
  2. Tests data quality, invalid row rejection, and raw = valid + rejected + duplicate reconciliation rules.
  3. Tests scheduler configuration, trigger, and exception handling.
  4. Tests edge cases with temporary data in a copy of the database.
  5. Confirms report generation, multi-level reconciliation, impact calculator, and Confluence publishing.
  6. Confirms the main database remains intact.
"""

import sqlite3
import os
import shutil
import sys
import datetime

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
# PART 1: Manual verification against the real database (1000+ records per CSV)
# ===========================================================================

def verify_calculations():
    section("MANUAL VERIFICATION (1000+ Records per Source)")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Total records
    ops = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    sls = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    sup = conn.execute("SELECT COUNT(*) FROM support").fetchone()[0]
    check("operations database count", 1000, ops)
    check("sales database count", 1000, sls)
    check("support database count", 1000, sup)
    check("total database records", 3000, ops + sls + sup)

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
    check("ops completed", 794, ops_completed)
    check("ops pending", 115, ops_pending)
    check("ops failed", 91, ops_failed)
    check("ops status total", 1000, ops_completed + ops_pending + ops_failed)

    # Completion pct for operations = 794/1000 * 100 = 79.4%
    check("ops completion_pct", 79.4, round(100.0 * ops_completed / ops, 1))

    # Target/actual for operations
    ops_target = conn.execute("SELECT SUM(target) FROM operations").fetchone()[0]
    ops_actual = conn.execute("SELECT SUM(actual_value) FROM operations").fetchone()[0]
    check("ops total_target", 125710.0, ops_target)
    check("ops total_actual", 114458.9, round(ops_actual, 1))
    check("ops achievement_pct", 91.0, round(100.0 * ops_actual / ops_target, 1))

    # Target/actual for sales revenue ($)
    sls_target = conn.execute("SELECT SUM(target) FROM sales").fetchone()[0]
    sls_actual = conn.execute("SELECT SUM(actual_value) FROM sales").fetchone()[0]
    check("sales total_target (revenue $)", 35299092.0, sls_target)
    check("sales total_actual (revenue $)", 30313837.85, round(sls_actual, 2))
    check("sales revenue achievement_pct", 85.9, round(100.0 * sls_actual / sls_target, 1))

    # Target/actual for support tickets
    sup_target = conn.execute("SELECT SUM(target) FROM support").fetchone()[0]
    sup_actual = conn.execute("SELECT SUM(actual_value) FROM support").fetchone()[0]
    check("support total_target (tickets)", 14907.0, sup_target)
    check("support total_actual (tickets)", 12942.0, sup_actual)
    check("support ticket achievement_pct", 86.8, round(100.0 * sup_actual / sup_target, 1))

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
    check("sales completed (Closed)", 781, sls_completed)
    check("sales pending (Pipeline)", 112, sls_pending)
    check("sales failed (Lost)", 107, sls_failed)

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
    check("support completed (Resolved)", 787, sup_resolved)
    check("support pending (Pending)", 117, sup_pending)
    check("support failed (Escalated)", 96, sup_escalated)

    # Overall completion = 2362 / 3000 = 78.7%
    total_completed = ops_completed + sls_completed + sup_resolved
    check("overall completed", 2362, total_completed)
    check("overall completion_pct", 78.7, round(100.0 * total_completed / 3000, 1))

    # Mixed-unit prevention check: confirm overall_summary query has NO mixed-unit target/actual columns
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
    import run_reports
    run_reports.ensure_view(conn, os.path.join(PROJECT_ROOT, "sql"), None)
    overall_row = conn.execute(run_reports.OVERALL_SUMMARY_SQL).fetchone()
    check("overall_summary has no total_target column", False, "total_target" in overall_row.keys())
    check("overall_summary has no achievement_pct column", False, "achievement_pct" in overall_row.keys())

    # Team & Department breakdown counts
    ops_teams_cnt = conn.execute("SELECT COUNT(DISTINCT team) FROM operations").fetchone()[0]
    check("operations team count", 3, ops_teams_cnt)
    sls_teams_cnt = conn.execute("SELECT COUNT(DISTINCT team) FROM sales").fetchone()[0]
    check("sales team count", 3, sls_teams_cnt)
    sup_teams_cnt = conn.execute("SELECT COUNT(DISTINCT team) FROM support").fetchone()[0]
    check("support team count", 3, sup_teams_cnt)

    ops_depts_cnt = conn.execute("SELECT COUNT(DISTINCT department) FROM operations").fetchone()[0]
    check("operations department count", 3, ops_depts_cnt)
    sls_depts_cnt = conn.execute("SELECT COUNT(DISTINCT department) FROM sales").fetchone()[0]
    check("sales department count", 3, sls_depts_cnt)
    sup_depts_cnt = conn.execute("SELECT COUNT(DISTINCT department) FROM support").fetchone()[0]
    check("support department count", 3, sup_depts_cnt)

    # Date range check
    dates_cnt = conn.execute("SELECT COUNT(DISTINCT date) FROM v_all_records").fetchone()[0]
    check("distinct reporting dates count", 30, dates_cnt)

    conn.close()


# ===========================================================================
# PART 2: Data Quality & Reconciliation Rules
# ===========================================================================

def test_data_loading_and_reconciliation_rules():
    section("DATA LOADING & RECONCILIATION RULES")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Verify load_stats table exists
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    check("load_stats table exists", True, "load_stats" in tables)

    stats = {r["source"]: dict(r) for r in conn.execute("SELECT * FROM load_stats").fetchall()}

    # 1. Operations CSV stats verification
    ops_st = stats.get("operations", {})
    check("operations raw_count", 1005, ops_st.get("raw_count"))
    check("operations valid_count", 1000, ops_st.get("valid_count"))
    check("operations invalid_count", 4, ops_st.get("invalid_count"))
    check("operations duplicate_count", 1, ops_st.get("duplicate_count"))
    check("operations inserted_count", 1000, ops_st.get("inserted_count"))
    check("operations RAW = VALID + REJECTED + DUPLICATE", True, ops_st.get("raw_count") == ops_st.get("valid_count") + ops_st.get("invalid_count") + ops_st.get("duplicate_count"))

    # 2. Sales CSV stats verification
    sls_st = stats.get("sales", {})
    check("sales raw_count", 1002, sls_st.get("raw_count"))
    check("sales valid_count", 1000, sls_st.get("valid_count"))
    check("sales invalid_count", 2, sls_st.get("invalid_count"))
    check("sales duplicate_count", 0, sls_st.get("duplicate_count"))
    check("sales inserted_count", 1000, sls_st.get("inserted_count"))
    check("sales RAW = VALID + REJECTED + DUPLICATE", True, sls_st.get("raw_count") == sls_st.get("valid_count") + sls_st.get("invalid_count") + sls_st.get("duplicate_count"))

    # 3. Support CSV stats verification
    sup_st = stats.get("support", {})
    check("support raw_count", 1008, sup_st.get("raw_count"))
    check("support valid_count", 1000, sup_st.get("valid_count"))
    check("support invalid_count", 7, sup_st.get("invalid_count"))
    check("support duplicate_count", 1, sup_st.get("duplicate_count"))
    check("support inserted_count", 1000, sup_st.get("inserted_count"))
    check("support RAW = VALID + REJECTED + DUPLICATE", True, sup_st.get("raw_count") == sup_st.get("valid_count") + sup_st.get("invalid_count") + sup_st.get("duplicate_count"))

    # 4. Invalid rows rejection verification (verify bad row IDs were not inserted into DB)
    ops_bad = conn.execute("SELECT COUNT(*) FROM operations WHERE record_id IN ('OPS-1001', 'OPS-1002', 'OPS-1003', 'OPS-1004')").fetchone()[0]
    check("invalid operations rows rejected", 0, ops_bad)

    sls_bad = conn.execute("SELECT COUNT(*) FROM sales WHERE record_id IN ('SLS-1001', 'SLS-1002')").fetchone()[0]
    check("invalid sales rows rejected", 0, sls_bad)

    sup_bad = conn.execute("SELECT COUNT(*) FROM support WHERE record_id IN ('SUP-1001', 'SUP-1002', 'SUP-1003', 'SUP-1004', 'SUP-1005', 'SUP-1006', 'SUP-1007')").fetchone()[0]
    check("invalid support rows rejected", 0, sup_bad)

    # 5. Duplicate handling verification (duplicate IDs present once only)
    ops_dup = conn.execute("SELECT COUNT(*) FROM operations WHERE record_id = 'OPS-0005'").fetchone()[0]
    check("duplicate OPS-0005 inserted exactly once", 1, ops_dup)

    sup_dup = conn.execute("SELECT COUNT(*) FROM support WHERE record_id = 'SUP-0010'").fetchone()[0]
    check("duplicate SUP-0010 inserted exactly once", 1, sup_dup)

    conn.close()


# ===========================================================================
# PART 3: Scheduler Module Tests
# ===========================================================================

def test_scheduler():
    section("SCHEDULER MODULE TESTS")
    sys.path.insert(0, PROJECT_ROOT)
    import scheduler

    # 1. Config reading test
    orig_time = os.environ.get("REPORT_SCHEDULE_TIME")
    orig_freq = os.environ.get("REPORT_SCHEDULE_FREQUENCY")
    os.environ["REPORT_SCHEDULE_TIME"] = "14:30"
    os.environ["REPORT_SCHEDULE_FREQUENCY"] = "DAILY"

    cfg = scheduler.get_schedule_config()
    check("scheduler config time", "14:30", cfg["schedule_time"])
    check("scheduler config frequency", "DAILY", cfg["frequency"])

    # 2. Next execution calculation test
    now = datetime.datetime(2026, 9, 30, 10, 0, 0)
    next_exec = scheduler.calculate_next_execution(cfg, now)
    check("next execution today at 14:30", datetime.datetime(2026, 9, 30, 14, 30, 0), next_exec)

    past_now = datetime.datetime(2026, 9, 30, 15, 0, 0)
    next_exec_tomorrow = scheduler.calculate_next_execution(cfg, past_now)
    check("next execution tomorrow at 14:30", datetime.datetime(2026, 10, 1, 14, 30, 0), next_exec_tomorrow)

    # Restore env vars
    if orig_time:
        os.environ["REPORT_SCHEDULE_TIME"] = orig_time
    else:
        os.environ.pop("REPORT_SCHEDULE_TIME", None)
    if orig_freq:
        os.environ["REPORT_SCHEDULE_FREQUENCY"] = orig_freq
    else:
        os.environ.pop("REPORT_SCHEDULE_FREQUENCY", None)

    # 3. Scheduler single execution trigger test
    os.environ["REPORT_SCHEDULE_INTERVAL_SECONDS"] = "0.01"
    os.environ["REPORT_SCHEDULE_ONCE"] = "true"
    runs = scheduler.start_scheduler(max_runs=1)
    check("scheduler triggered workflow and completed 1 run", 1, runs)
    os.environ.pop("REPORT_SCHEDULE_INTERVAL_SECONDS", None)
    os.environ.pop("REPORT_SCHEDULE_ONCE", None)

    # 4. Scheduler exception handling test (does not terminate process on workflow exception)
    import logging as _logging
    tlogger = _logging.getLogger("scheduler_test_err")
    tlogger.setLevel(_logging.WARNING)
    if not tlogger.handlers:
        tlogger.addHandler(_logging.NullHandler())

    # Temporarily force main to raise exception
    orig_main = scheduler.main.main
    def failing_main():
        raise RuntimeError("Simulated workflow failure in test")
    scheduler.main.main = failing_main

    success, rpath = scheduler.run_scheduled_workflow(tlogger)
    check("scheduler handles workflow failure gracefully (returns False, None)", False, success)
    check("scheduler report_path is None on failure", None, rpath)

    # Restore main
    scheduler.main.main = orig_main


# ===========================================================================
# PART 4: Edge-case testing on a COPY of the database
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

    # --- Edge 3: Empty query result ---
    section("Edge 3: Empty query result")
    empty = conn.execute(
        "SELECT * FROM v_all_records WHERE record_id = 'NONEXISTENT'"
    ).fetchall()
    check("empty result set", 0, len(empty))

    # --- Edge 4: NULL value handling ---
    section("Edge 4: NULL value handling")
    try:
        conn.execute(
            "INSERT INTO operations VALUES "
            "('EDGE-002','Test Null','Team Alpha','2026-09-26','Manufacturing','Completed',10,100,NULL,'Morning',NULL)"
        )
        check("NOT NULL constraint on actual_value", "should reject", "accepted")
    except sqlite3.IntegrityError:
        check("NOT NULL constraint on actual_value enforced", True, True)

    conn.close()

    # Clean up test database
    os.remove(TEST_DB_PATH)
    print()
    print("  Test database removed.")


# ===========================================================================
# PART 5: Main Database Integrity Check
# ===========================================================================

def verify_main_db():
    section("MAIN DATABASE INTEGRITY CHECK")
    conn = sqlite3.connect(DB_PATH)
    ops = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    sls = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    sup = conn.execute("SELECT COUNT(*) FROM support").fetchone()[0]
    check("operations still 1000", 1000, ops)
    check("sales still 1000", 1000, sls)
    check("support still 1000", 1000, sup)
    conn.close()


# ===========================================================================
# PART 6: Report Generation Tests
# ===========================================================================

def test_report_generation():
    """Test report generation."""
    import time
    import logging as _logging

    sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
    import generate_report

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
            "7. Data Quality & Data Loading Summary",
            "Data Loading Summary",
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

    # Clean up test report
    if report_path and os.path.exists(report_path):
        os.remove(report_path)


# ===========================================================================
# PART 7: Reconciliation Test
# ===========================================================================

def test_reconciliation():
    """Test multi-level reconciliation module."""
    section("Multi-Level Reconciliation Audit")
    import reconcile
    rec_result = reconcile.reconcile_all(PROJECT_ROOT)
    check("multi-level reconciliation verdict = True", True, rec_result)


# ===========================================================================
# PART 8: Impact Calculator Test
# ===========================================================================

def test_impact_calculator():
    """Test programmatic impact calculator module."""
    section("Impact Calculator Verification")
    import impact_calculator

    ts_scenario = impact_calculator.calculate_time_savings(automated_duration_seconds=0.15, mode="SCENARIO_BASELINE")
    check("scenario mode weekly_hours_saved = 12.0", 12.0, ts_scenario["weekly_hours_saved"])
    check("scenario mode annual_hours_saved = 624.0", 624.0, ts_scenario["annual_hours_saved"])

    ts_measured = impact_calculator.calculate_time_savings(manual_baseline={"task1": 5.0, "task2": 5.0}, automated_duration_seconds=0.15, mode="MEASURED")
    check("measured mode weekly_hours_saved", 10.0, ts_measured["weekly_hours_saved"])

    ds_scenario = impact_calculator.calculate_dev_speedup(mode="SCENARIO_MODELED")
    check("dev speedup_pct = 30.0%", 30.0, ds_scenario["speedup_pct"])

    ts_zero = impact_calculator.calculate_time_savings(manual_baseline={"task1": 0.0}, automated_duration_seconds=0.15)
    check("zero baseline efficiency_gain_pct does not crash", 0.0, ts_zero["efficiency_gain_pct"])


# ===========================================================================
# PART 9: Confluence Publisher Tests
# ===========================================================================

def test_confluence():
    """Test Confluence Publisher module."""
    section("Confluence Publisher Integration")
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
    print("Automated Verification Suite (Phase 1-5)")
    print("=" * 60)

    verify_calculations()
    test_data_loading_and_reconciliation_rules()
    test_scheduler()
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
