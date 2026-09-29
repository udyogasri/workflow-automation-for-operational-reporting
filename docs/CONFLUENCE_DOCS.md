# Confluence Documentation

This document contains standardized enterprise documentation designed for publishing directly to a Confluence Knowledge Base space.

---

## 1. Business Requirement

### Business Objective
The Central Operations team requires an automated data consolidation and reporting solution. Previously, operational data was manually gathered from three core business functions (Operations, Sales, and Support). The goal is to eliminate manual Excel consolidation, validate incoming operational data, store clean records in a structured SQLite database, and generate standardized HTML reports.

### Stakeholders & Target Users
- **Operations Managers**: Require overview of overall organizational output and efficiency.
- **Department Leads**: Require visibility into team and department-level targets vs. actuals.
- **Quality & Support Teams**: Require immediate identification of failed, pending, or underperforming operations.

### Key Performance Indicators (KPIs) & Domain Unit Definitions
To ensure business metric clarity across distinct functional domains, target and actual metrics are defined per business function:
- **Operations Function**:
  - `quantity`: Physical units produced/processed.
  - `target`: Production target volume (units).
  - `actual_value`: Actual physical output (units).
  - *Domain Metric*: Quantitative production output.
- **Sales Function**:
  - `quantity`: Number of commercial deals/contracts closed.
  - `target`: Monetary revenue target ($).
  - `actual_value`: Actual monetary revenue realized ($).
  - *Domain Metric*: Monetary sales revenue.
- **Support Function**:
  - `tickets_count`: Number of customer support tickets received.
  - `target`: Target ticket resolution count.
  - `actual_value`: Actual resolved ticket count.
  - *Domain Metric*: Support ticket resolution efficiency.

---

## 2. Existing Manual Reporting Process

Before automation, the operations team executed a manual consolidation workflow every week:

```
[ Operations Team ]
        │
        ▼
[ Receive CSV Files from Operations, Sales, Support ]
        │
        ▼
[ Open Files in Excel & Verify Columns / Formatting ]
        │
        ▼
[ Manually Align Differing Status Names & Columns ]
        │
        ▼
[ Apply Formulae for KPIs (Completion %, Target/Actual) ]
        │
        ▼
[ Highlight Exceptions (Failures, Delays, Low Output) ]
        │
        ▼
[ Copy Data into Standardized Presentation / PDF ]
        │
        ▼
[ Email / Share Report with Stakeholders ]
```

### Manual Process Overhead & Limitations
- **Labor Effort**: ~12 hours weekly spent opening files, aligning columns, copying data, and fixing formula errors.
- **Frequent Human Errors**: Misaligned VLOOKUPs, inconsistent status naming (`In Progress` vs `Pipeline` vs `Pending`), missing duplicate checks.
- **Lack of Audit Trail**: No centralized log of data errors or rejected records.

---

## 3. Data Source Specifications

The automation ingests three CSV data files from separate business functions:

### 1. Operations (`data/operations.csv`)
- **Function**: Manufacturing, Logistics, Quality Control
- **Schema**: `record_id` (PK, String), `employee` (String), `team` (String), `date` (YYYY-MM-DD), `department` (String), `status` (`Completed`, `In Progress`, `Failed`), `quantity` (Int), `target` (Float), `actual_value` (Float), `shift` (String), `notes` (String).
- **Units**: Units produced / Target units / Actual units.

### 2. Sales (`data/sales.csv`)
- **Function**: Retail, Wholesale, Online Sales
- **Schema**: `record_id` (PK, String), `employee` (String), `team` (String), `date` (YYYY-MM-DD), `department` (String), `status` (`Closed`, `Pipeline`, `Lost`), `quantity` (Int deals count), `target` (Float revenue target $), `actual_value` (Float actual revenue $), `region` (String), `product_category` (String).
- **Units**: Deals count / Revenue target ($) / Actual revenue ($).

### 3. Support (`data/support.csv`)
- **Function**: Technical Support, Customer Service, Billing
- **Schema**: `record_id` (PK, String), `employee` (String), `team` (String), `date` (YYYY-MM-DD), `department` (String), `status` (`Resolved`, `Pending`, `Escalated`), `tickets_count` (Int), `target` (Float ticket target), `actual_value` (Float resolved tickets), `priority` (String), `resolution_time_hrs` (Float).
- **Units**: Tickets count / Target resolved tickets / Actual resolved tickets.

---

## 4. Report Requirements

The system must produce a standardized 8-section report containing:
1. **Executive Summary**: High-level KPIs (`Total Records`, `Completed`, `Pending`, `Failed`, `Completion Rate`, `Total Target`, `Total Actual`, `Achievement %`).
2. **Source-Wise Summary**: Function-by-function comparison.
3. **Team Performance**: Productivity and achievement breakdown by team.
4. **Department Performance**: Departmental analysis.
5. **Daily Summary**: 25-day activity trend.
6. **Attention Required**: Exception table flagging urgent items.
7. **Data Quality Summary**: Source file error/NULL audit.
8. **Process Summary**: Execution duration, record counts, timestamp.

---

## 5. Business Rules

### Status Normalization
Differing departmental status strings map into unified categories:
- **Completed**: `Completed` (Ops), `Closed` (Sales), `Resolved` (Support).
- **Pending**: `In Progress` (Ops), `Pipeline` (Sales), `Pending` (Support).
- **Failed**: `Failed` (Ops), `Lost` (Sales), `Escalated` (Support).

### KPI Calculation Formulas
- **Completion Rate (%)**: `(Completed Count / Total Valid Records) * 100`
- **Achievement Rate (%)**: `CASE WHEN Target > 0 THEN (Actual / Target) * 100 ELSE 0 END`

---

## 6. Data Validation Rules

1. **Required Columns**: Headers must contain all mandatory columns.
2. **Non-Empty Check**: Mandatory fields cannot be empty strings.
3. **Date Validation**: Dates must follow strict `YYYY-MM-DD` ISO format.
4. **Type Check**: Quantities must parse as integers; Target/Actual must parse as floats.
5. **Duplicate Check**: Duplicate `record_id` values within the file or DB are rejected (`INSERT OR IGNORE`).
6. **Fault Tolerance**: Invalid rows produce structured warning logs; valid rows continue processing.

---

## 7. Automated Workflow

```
[ CSV Sources ] ──> [ load_data.py (Python Ingestion) ] ──> [ SQLite database ] ──> [ reconcile.py ] ──> [ generate_report.py ]
                                  │                                   │                     │                      │
                                  ▼                                   ▼                     ▼                      ▼
                           [ Ingestion Log ]                 [ Terminal Summary ]    [ Discrepancy Audit ]   [ HTML Report File ]
```

---

## 8. SQL Reporting Logic

The database view `v_all_records` combines all three tables into a unified view:
```sql
CREATE VIEW v_all_records AS
SELECT record_id, employee, team, date, department, status,
  CASE
    WHEN status IN ('Completed', 'Closed', 'Resolved') THEN 'Completed'
    WHEN status IN ('In Progress', 'Pipeline', 'Pending') THEN 'Pending'
    WHEN status IN ('Failed', 'Lost', 'Escalated') THEN 'Failed'
    ELSE 'Unknown'
  END AS status_category,
  quantity AS item_count, target, actual_value, 'operations' AS source
FROM operations
UNION ALL ...
```

---

## 9. Standardized Report User Guide

- **How to Open**: Open `reports/operational_report_YYYY-MM-DD_HH-MM-SS.html` in any standard web browser (Chrome, Edge, Firefox).
- **Reading Executive KPIs**: View completion rate and target achievement at a glance.
- **Reviewing Exceptions**: Scroll to **Section 6: Attention Required** to inspect records that require manual escalation or followup.

---

## 10. Error Handling

| Error Type | Handling Strategy | User Impact |
|---|---|---|
| Missing Source CSV | Halts workflow prior to DB load | Clear error log created; main process aborts safely |
| Invalid CSV Row | Row skipped; warning logged | Valid records loaded successfully; audit log records skip reason |
| Division by Zero | Handled via SQL `CASE WHEN` | Achievement rate defaults safely to `0.0%` |
| Reconciliation Mismatch | Aborts report generation | Prevents corrupt or inconsistent reports from being published |

---

## 11. Operational Runbook

### Step 1: Pre-Execution
Place updated CSV files into the `data/` directory (`operations.csv`, `sales.csv`, `support.csv`).

### Step 2: Execution
Run the automated entry point:
```bash
python main.py
```

### Step 3: Post-Execution & Review
- Check terminal output for `Status: SUCCESS`.
- Open the generated HTML file in `reports/`.
- Verify **Section 6: Attention Required** for items needing action.

---

## 12. Testing & Validation

Run the 70-check automated test suite:
```bash
python scripts/test_reports.py
```
Validates:
- Database record counts & schema.
- SQL query aggregations against independent Python calculations.
- Edge case handling (zero targets, empty queries, NULL fields, abnormal statuses).
- Output report file structure and value consistency.
- Impact calculator calculations.

---

## 13. Before vs After Process

| Process Metric | Before Automation (Manual) | After Automation (System) |
|---|---|---|
| **Execution Time** | ~12 hours / week (Scenario Baseline) | < 0.2 seconds (Automated Runtime) |
| **Error Rate** | High (Human copy/paste errors) | 0% (Rule-based validation) |
| **Status Alignment** | Manual / Inconsistent | Automated View Normalization |
| **Audit Trail** | None | Timestamped Logs & Reconciliation |
| **Output Consistency** | Variable Excel formatting | Standardized HTML Reports |

---

## 14. Automation Impact & Measurement Methodology

### Time Savings Methodology ("12 Hours Weekly Claim")
*Classification: Scenario-Modeled Operational Baseline*:
- File Collection & Opening: 1.5 hrs
- Schema Alignment & Cleaning: 3.5 hrs
- KPI Calculation & Formula Checks: 3.0 hrs
- Exception Identification & Formatting: 2.5 hrs
- Distribution & Verification: 1.5 hrs
- **Scenario-Modeled Manual Baseline**: **12.0 Hours / Week**
- **Automated Workflow Runtime**: **< 1 Second**
- **Estimated Annualized Impact**: ~624 Hours Saved Annually.

### Development Efficiency Methodology ("30% Speedup Claim")
*Classification: Scenario-Modeled Development Efficiency Methodology*:
- Estimated baseline development time without Copilot assistance: ~25.0 Hours.
- Scenario-modeled Copilot-assisted development time: ~17.5 Hours.
- **Calculated Speedup**: `(25.0 - 17.5) / 25.0 * 100 = 30.0% Improvement`.
- *Note*: All Copilot suggestions were validated manually via the 70-check test suite (`scripts/test_reports.py`).
