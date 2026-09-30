# Automated Scheduler Architecture & Operations Guide

This document details the architecture, configuration, offline catch-up behavior, and Windows Task Scheduler integration for `scheduler.py`.

---

## 1. Scheduler Overview & Architecture

`scheduler.py` is a lightweight, background process built entirely with the Python Standard Library. It periodically invokes `main.main()` based on configuration settings stored in `.env`.

### Executive Execution Flow

```text
                     python scheduler.py
                              │
                    Load Configuration (.env)
                              │
             Check Missed Run Today (Catch-Up Mode)
                              │
             ┌────────────────┴────────────────┐
             │                                 │
   [Missed Run Detected]              [No Missed Run]
             │                                 │
             ▼                                 ▼
   Run main.main() Now               Calculate Next Execution Time
             │                                 │
             └────────────────┬────────────────┘
                              │
                              ▼
                     Sleep Loop (1s Chunks)
                              │
                              ▼
                    Target Time Reached?
                              │
                       (Yes) ─┴─ (No) ──> [Continue Sleep Loop]
                              │
                              ▼
                       Run main.main()
                              │
                              ▼
                 Wait for Next Scheduled Run
```

---

## 2. Environment Configuration (`.env`)

Schedule parameters are controlled via `.env`:

```env
# Time of day to run the scheduled workflow (Format: HH:MM or HH:MM:SS)
REPORT_SCHEDULE_TIME=09:00

# Schedule frequency (DAILY)
REPORT_SCHEDULE_FREQUENCY=DAILY

# Catch-up mode: Automatically run missed reports on startup if computer was offline (true/false)
REPORT_SCHEDULE_CATCHUP=true

# Testing flag: Run scheduler at fixed interval in seconds (uncomment to activate)
# REPORT_SCHEDULE_INTERVAL_SECONDS=60

# Testing flag: Run scheduler once and exit immediately (uncomment to activate)
# REPORT_SCHEDULE_ONCE=true
```

---

## 3. Catch-Up Mode (Offline Computer Recovery)

### The Offline Laptop Scenario
If your scheduler is configured for 09:00 AM daily, but your laptop was powered off from 8:00 AM until 2:00 PM:

1. When you power on your laptop and start `python scheduler.py`, the scheduler reads `REPORT_SCHEDULE_CATCHUP=true`.
2. It executes `has_report_run_today()`, inspecting the `reports/` folder for files named `operational_report_YYYY-MM-DD_HH-MM-SS.html` matching today's date with a timestamp at or after `09:00`.
3. If **no report exists for today**, it logs:
   ```text
   Catch-up Mode: Today's (2026-09-30) scheduled 09:00 run was missed (system offline). Triggering catch-up execution now...
   ```
   and executes `main.main()` immediately.
4. If **a report already exists for today** (for example, if a report was run manually at 8:30 AM), it logs:
   ```text
   Catch-up Check: Report for today (2026-09-30) at/after 09:00 already exists. Skipping duplicate catch-up run.
   ```
   and waits until tomorrow at 09:00 AM.

---

## 4. High-Frequency Testing & Single Cycle Options

### High-Frequency Interval Testing (1-Minute Test)
To verify scheduler loop execution without waiting for 09:00 AM:
1. Uncomment line in `.env`:
   ```env
   REPORT_SCHEDULE_INTERVAL_SECONDS=60
   ```
2. Run `python scheduler.py`. The scheduler will execute immediately and repeat every 60 seconds.
3. Re-comment line when testing is finished.

### Single-Cycle CLI Execution
To execute a single schedule cycle and exit immediately (ideal for automated CI/CD pipelines):
```powershell
python scheduler.py --once
```

---

## 5. Windows Task Scheduler Guide (Automatic Boot Startup)

To run `python scheduler.py` automatically whenever Windows boots up or when your user logs in:

1. Press `Win + R`, type `taskschd.msc`, and press **Enter** to open Windows Task Scheduler.
2. Click **Create Task** in the right-hand panel.
3. **General Tab**:
   - Name: `Operational Reporting Scheduler`
   - Select **Run only when user is logged on** (or *Run whether user is logged on or not*).
4. **Triggers Tab**:
   - Click **New...**
   - Begin the task: **At log on** or **At startup**. Click **OK**.
5. **Actions Tab**:
   - Click **New...**
   - Action: **Start a program**
   - Program/script: Enter Python executable path (find via `where python` in PowerShell):
     ```text
     C:\Users\<username>\AppData\Local\Programs\Python\Python311\python.exe
     ```
   - Add arguments: `scheduler.py`
   - Start in: Enter project root directory path:
     ```text
     C:\Users\manik\Documents\workflow-automation-for-operational-reporting
     ```
6. Click **OK** to save the task.
