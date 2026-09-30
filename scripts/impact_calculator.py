"""
impact_calculator.py
Impact & Efficiency Measurement Calculator.

Provides an adjustable framework to calculate:
  1. Manual vs. Automated Operational Time Savings (12 Hours Weekly Savings).
     - Supports SCENARIO_BASELINE mode and MEASURED mode.
  2. Software Development Speed Improvement (30% Development Speedup).
     - Supports SCENARIO_MODELED mode and MEASURED mode (parsing data/development_tasks.json).
"""

import os
import sys
import json

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Default Scenario Baselines (Configurable)
# ---------------------------------------------------------------------------

DEFAULT_MANUAL_BASELINE = {
    "source_file_collection": 1.5,      # hours/week opening 3 CSVs from email/drives
    "schema_alignment_cleaning": 3.5,   # hours/week aligning headers, dates, data types
    "kpi_formula_calculations": 3.0,   # hours/week building VLOOKUPs & SUM formulas
    "exception_identification": 2.5,    # hours/week manually flagging failures & underperformance
    "report_formatting_distribution": 1.5  # hours/week formatting final report & emailing
}

DEFAULT_DEVELOPMENT_BASELINE = {
    "estimated_baseline_hours": 25.0,  # Estimated baseline dev hours
    "scenario_modeled_optimized_hours": 17.5  # Optimized dev hours
}


# ---------------------------------------------------------------------------
# Calculation Logic
# ---------------------------------------------------------------------------

def calculate_time_savings(manual_baseline=None, automated_duration_seconds=0.15, weekly_frequency=1, mode="SCENARIO_BASELINE"):
    """
    Calculate operational time savings based on manual baseline hours vs. automated execution seconds.
    Mode: SCENARIO_BASELINE or MEASURED.
    """
    if manual_baseline is None:
        manual_baseline = DEFAULT_MANUAL_BASELINE

    total_manual_hours_per_run = sum(manual_baseline.values()) if isinstance(manual_baseline, dict) else float(manual_baseline)
    total_manual_weekly_hours = total_manual_hours_per_run * weekly_frequency

    automated_hours_per_run = float(automated_duration_seconds) / 3600.0
    total_automated_weekly_hours = automated_hours_per_run * weekly_frequency

    weekly_hours_saved = max(total_manual_weekly_hours - total_automated_weekly_hours, 0.0)
    annual_hours_saved = weekly_hours_saved * 52.0
    
    denom = max(total_manual_weekly_hours, 0.000001)
    efficiency_gain_pct = round(100.0 * weekly_hours_saved / denom, 1)

    status_label = "MEASURED" if mode.upper() == "MEASURED" else "SCENARIO-MODELED BASELINE"

    return {
        "mode": mode.upper(),
        "status_label": status_label,
        "manual_breakdown_hours": manual_baseline if isinstance(manual_baseline, dict) else {"total": manual_baseline},
        "total_manual_weekly_hours": round(total_manual_weekly_hours, 2),
        "total_automated_weekly_hours": round(total_automated_weekly_hours, 4),
        "weekly_hours_saved": round(weekly_hours_saved, 2),
        "annual_hours_saved": round(annual_hours_saved, 1),
        "efficiency_gain_pct": efficiency_gain_pct
    }


def calculate_dev_speedup(data_path=None, mode="SCENARIO_MODELED"):
    """
    Calculate development speed improvement % using task dataset or default baseline:
    Speedup % = ((Estimated Baseline Hours - Optimized Hours) / Estimated Baseline Hours) * 100
    Mode: SCENARIO_MODELED or MEASURED.
    """
    project_root = get_project_root()
    if data_path is None:
        data_path = os.path.join(project_root, "data", "development_tasks.json")

    tasks = []
    if mode.upper() == "MEASURED" and os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            tasks = []

    if tasks:
        baseline_hours = sum(t.get("baseline_hours", 0.0) for t in tasks)
        optimized_hours = sum(t.get("optimized_hours", t.get("copilot_assisted_hours", 0.0)) for t in tasks)
        mode_used = "MEASURED"
        status_label = "MEASURED TASK DATA"
    else:
        baseline_hours = DEFAULT_DEVELOPMENT_BASELINE["estimated_baseline_hours"]
        optimized_hours = DEFAULT_DEVELOPMENT_BASELINE["scenario_modeled_optimized_hours"]
        mode_used = "SCENARIO_MODELED"
        status_label = "SCENARIO-MODELED METHODOLOGY"

    denom = max(baseline_hours, 0.000001)
    hours_saved = max(baseline_hours - optimized_hours, 0.0)
    speedup_pct = round(100.0 * hours_saved / denom, 1)

    return {
        "mode": mode_used,
        "status_label": status_label,
        "estimated_baseline_hours": round(baseline_hours, 2),
        "copilot_hours": round(optimized_hours, 2),
        "optimized_hours": round(optimized_hours, 2),
        "hours_saved": round(hours_saved, 2),
        "speedup_pct": speedup_pct,
        "task_count": len(tasks)
    }


def print_impact_report(automated_duration_seconds=0.15):
    """Print formatted impact summary."""
    ts = calculate_time_savings(automated_duration_seconds=automated_duration_seconds)
    ds = calculate_dev_speedup(mode="MEASURED")

    print("=" * 65)
    print("  AUTOMATION IMPACT & EFFICIENCY METRICS SUMMARY")
    print("=" * 65)
    print("  1. OPERATIONAL TIME SAVINGS ('12 Hours Weekly Claim'):")
    print(f"     - Status / Mode                     : {ts['status_label']}")
    print(f"     - Manual Weekly Baseline             : {ts['total_manual_weekly_hours']} Hours/Week")
    print(f"     - Automated Workflow Runtime         : {ts['total_automated_weekly_hours']:.4f} Hours (< 1 sec)")
    print(f"     - Weekly Hours Saved                 : {ts['weekly_hours_saved']} Hours/Week")
    print(f"     - Annualized Impact                  : ~{ts['annual_hours_saved']} Hours Saved / Year")
    print(f"     - Workflow Efficiency Gain           : {ts['efficiency_gain_pct']}%")
    print()
    print("  2. DEV SPEED IMPROVEMENT ('30% Development Speedup Claim'):")
    print(f"     - Status / Mode                     : {ds['status_label']}")
    print(f"     - Baseline Dev Time (Est.)           : {ds['estimated_baseline_hours']} Hours")
    print(f"     - Optimized Dev Time                 : {ds['optimized_hours']} Hours")
    print(f"     - Hours Saved in Dev                 : {ds['hours_saved']} Hours")
    print(f"     - Development Speedup                : {ds['speedup_pct']}%")
    print("=" * 65)


if __name__ == "__main__":
    print_impact_report()
