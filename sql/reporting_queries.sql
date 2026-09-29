-- reporting_queries.sql
-- SQL reporting queries for Phase 2: Operational Reporting
-- Database: SQLite (reporting.db)
--
-- Status mapping across tables:
--   operations: Completed, In Progress, Failed
--   sales:      Closed,    Pipeline,    Lost
--   support:    Resolved,  Pending,     Escalated
--
-- "completed" = Completed / Closed / Resolved
-- "pending"   = In Progress / Pipeline / Pending
-- "failed"    = Failed / Lost / Escalated


-- ============================================================
-- 1. OVERALL OPERATIONAL SUMMARY
-- ============================================================
-- Combines all three tables using UNION ALL with normalized
-- status categories.  The quantity column is named generically.

-- VIEW: v_all_records
-- A unified view of all three operational tables with a
-- normalized status_category column.
DROP VIEW IF EXISTS v_all_records;

CREATE VIEW v_all_records AS
SELECT
    record_id,
    employee,
    team,
    date,
    department,
    status,
    CASE
        WHEN status IN ('Completed', 'Closed', 'Resolved') THEN 'Completed'
        WHEN status IN ('In Progress', 'Pipeline', 'Pending') THEN 'Pending'
        WHEN status IN ('Failed', 'Lost', 'Escalated')       THEN 'Failed'
        ELSE 'Unknown'
    END AS status_category,
    quantity   AS item_count,
    target,
    actual_value,
    'operations' AS source
FROM operations

UNION ALL

SELECT
    record_id,
    employee,
    team,
    date,
    department,
    status,
    CASE
        WHEN status IN ('Completed', 'Closed', 'Resolved') THEN 'Completed'
        WHEN status IN ('In Progress', 'Pipeline', 'Pending') THEN 'Pending'
        WHEN status IN ('Failed', 'Lost', 'Escalated')       THEN 'Failed'
        ELSE 'Unknown'
    END AS status_category,
    quantity   AS item_count,
    target,
    actual_value,
    'sales' AS source
FROM sales

UNION ALL

SELECT
    record_id,
    employee,
    team,
    date,
    department,
    status,
    CASE
        WHEN status IN ('Completed', 'Closed', 'Resolved') THEN 'Completed'
        WHEN status IN ('In Progress', 'Pipeline', 'Pending') THEN 'Pending'
        WHEN status IN ('Failed', 'Lost', 'Escalated')       THEN 'Failed'
        ELSE 'Unknown'
    END AS status_category,
    tickets_count AS item_count,
    target,
    actual_value,
    'support' AS source
FROM support;


-- QUERY: overall_summary
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


-- ============================================================
-- 2. SOURCE-WISE SUMMARY
-- ============================================================
-- QUERY: source_summary

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


-- ============================================================
-- 3. TEAM PERFORMANCE
-- ============================================================
-- QUERY: team_performance

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


-- ============================================================
-- 4. DEPARTMENT PERFORMANCE
-- ============================================================
-- QUERY: department_performance

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


-- ============================================================
-- 5. DAILY SUMMARY
-- ============================================================
-- QUERY: daily_summary

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


-- ============================================================
-- 6. ATTENTION REQUIRED
-- ============================================================
-- Records that need operational attention.
--
-- Rules (simple and explainable):
--   a) Status is Failed/Lost/Escalated     (action needed on failures)
--   b) Status is Pending/In Progress/Pipeline (unfinished work)
--   c) actual_value < 50% of target AND status_category = 'Completed'
--      (completed but significantly underperformed)
--
-- QUERY: attention_required

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


-- ============================================================
-- 7. DATA QUALITY SUMMARY
-- ============================================================
-- Counts records per source, checks for NULLs in key columns,
-- and checks for any unexpected status values.
--
-- QUERY: data_quality

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
