"""
scheduler.py
Lightweight Automated Scheduler for Operational Reporting.

Configurable Schedule (Environment Variables):
  - REPORT_SCHEDULE_TIME              : Time of day to run workflow (format: HH:MM or HH:MM:SS, default: 09:00)
  - REPORT_SCHEDULE_FREQUENCY         : Schedule frequency (default: DAILY)
  - REPORT_SCHEDULE_INTERVAL_SECONDS : Optional fixed interval in seconds (for high-frequency testing)
  - REPORT_SCHEDULE_ONCE             : Set to "true" to run a single scheduled cycle and exit (useful for automated testing)

Timezone Behavior:
  - Uses system local timezone consistently (datetime.now().astimezone()).
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Import existing main workflow entrypoint to avoid code duplication
import main


def setup_scheduler_logger(project_root):
    """Configure logging for the scheduler process."""
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "scheduler.log")

    logger = logging.getLogger("scheduler")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, log_file


def load_dotenv(project_root=None):
    """Load environment variables from a .env file if present."""
    if project_root is None:
        project_root = main.PROJECT_ROOT
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    if key and key not in os.environ:
                        os.environ[key] = val


def get_schedule_config():
    """Read schedule settings from environment variables or .env file."""
    load_dotenv()
    schedule_time = os.environ.get("REPORT_SCHEDULE_TIME", "09:00").strip()
    frequency = os.environ.get("REPORT_SCHEDULE_FREQUENCY", "DAILY").strip().upper()
    interval_sec_env = os.environ.get("REPORT_SCHEDULE_INTERVAL_SECONDS", "").strip()
    run_once = os.environ.get("REPORT_SCHEDULE_ONCE", "").strip().lower() in ("true", "1", "yes")
    catchup = os.environ.get("REPORT_SCHEDULE_CATCHUP", "true").strip().lower() in ("true", "1", "yes")

    interval_seconds = None
    if interval_sec_env:
        try:
            interval_seconds = float(interval_sec_env)
        except ValueError:
            interval_seconds = None

    return {
        "schedule_time": schedule_time,
        "frequency": frequency,
        "interval_seconds": interval_seconds,
        "run_once": run_once,
        "catchup": catchup
    }


def calculate_next_execution(config, now=None):
    """Calculate the next execution time based on configuration and current time."""
    if now is None:
        now = datetime.now()

    if config["interval_seconds"] is not None:
        return now + timedelta(seconds=config["interval_seconds"])

    time_str = config["schedule_time"]
    try:
        parts = [int(p) for p in time_str.split(":")]
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else 0
        second = parts[2] if len(parts) > 2 else 0
    except Exception as e:
        raise ValueError(f"Invalid REPORT_SCHEDULE_TIME format '{time_str}'. Expected HH:MM or HH:MM:SS.") from e

    target_today = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    if config["frequency"] == "DAILY":
        if target_today <= now:
            return target_today + timedelta(days=1)
        else:
            return target_today
    else:
        # Default daily fallback
        if target_today <= now:
            return target_today + timedelta(days=1)
        else:
            return target_today


def run_scheduled_workflow(logger):
    """Trigger the existing main workflow and log outcome."""
    logger.info("Scheduled workflow execution started.")
    start_time = datetime.now()
    try:
        report_path = main.main()
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Scheduled workflow succeeded in {duration:.2f} seconds. Report: {report_path}")
        return True, report_path
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Scheduled workflow failed after {duration:.2f} seconds: {e}", exc_info=True)
        return False, None


def has_report_run_today(project_root, schedule_time_str="09:00"):
    """Check if an operational report file has already been generated today at or after the scheduled time."""
    reports_dir = os.path.join(project_root, "reports")
    if not os.path.exists(reports_dir):
        return False
    today_prefix = f"operational_report_{datetime.now().strftime('%Y-%m-%d')}"
    
    try:
        sparts = [int(p) for p in schedule_time_str.split(":")]
        sched_time = datetime.now().replace(hour=sparts[0], minute=sparts[1] if len(sparts) > 1 else 0, second=0, microsecond=0)
    except Exception:
        sched_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    for filename in os.listdir(reports_dir):
        if filename.startswith(today_prefix) and filename.endswith(".html"):
            # Format: operational_report_YYYY-MM-DD_HH-MM-SS.html
            parts = filename.replace(".html", "").split("_")
            if len(parts) >= 4:
                try:
                    time_parts = [int(p) for p in parts[3].split("-")]
                    report_time = datetime.now().replace(hour=time_parts[0], minute=time_parts[1], second=time_parts[2], microsecond=0)
                    if report_time >= sched_time:
                        return True
                except Exception:
                    return True
            else:
                return True
    return False


def start_scheduler(project_root=None, max_runs=None):
    """Main loop for the scheduler."""
    if project_root is None:
        project_root = main.PROJECT_ROOT

    logger, log_file = setup_scheduler_logger(project_root)
    config = get_schedule_config()

    local_tz_name = datetime.now().astimezone().tzname() or "Local Timezone"

    logger.info("=" * 60)
    logger.info("STARTING OPERATIONAL REPORTING SCHEDULER")
    logger.info("=" * 60)
    logger.info(f"Configuration : Frequency={config['frequency']}, Time={config['schedule_time']}")
    if config['interval_seconds']:
        logger.info(f"Interval Override : {config['interval_seconds']} seconds")
    logger.info(f"Local Timezone: {local_tz_name}")
    logger.info(f"Scheduler Log : {log_file}")
    logger.info("=" * 60)

    runs_completed = 0

    # Catch-up check: Verify if today's 09:00 run was missed when starting late
    if config.get("catchup") and config["interval_seconds"] is None and not config["run_once"]:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        try:
            parts = [int(p) for p in config["schedule_time"].split(":")]
            target_today = now.replace(hour=parts[0], minute=parts[1] if len(parts) > 1 else 0, second=0, microsecond=0)
            
            if target_today <= now:
                if not has_report_run_today(project_root, config["schedule_time"]):
                    logger.info(f"Catch-up Mode: Today's ({today_str}) scheduled {config['schedule_time']} run was missed (system offline). Triggering catch-up execution now...")
                    run_scheduled_workflow(logger)
                    runs_completed += 1
                else:
                    logger.info(f"Catch-up Check: Report for today ({today_str}) at/after {config['schedule_time']} already exists. Skipping duplicate catch-up run.")
        except Exception as e:
            logger.warning(f"Catch-up check warning: {e}")

    try:
        while True:
            now = datetime.now()
            next_run = calculate_next_execution(config, now)
            logger.info(f"Next execution scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')} ({local_tz_name})")

            # Wait loop until next execution time
            while True:
                current = datetime.now()
                remaining = (next_run - current).total_seconds()
                if remaining <= 0:
                    break
                # Sleep in 1-second chunks to stay responsive
                sleep_chunk = min(remaining, 1.0)
                time.sleep(sleep_chunk)

            # Trigger workflow
            success, report_path = run_scheduled_workflow(logger)
            runs_completed += 1

            if config["run_once"] or (max_runs is not None and runs_completed >= max_runs):
                logger.info(f"Scheduler run limit reached ({runs_completed} run(s)). Stopping scheduler.")
                break

    except KeyboardInterrupt:
        logger.info("Scheduler received shutdown signal (KeyboardInterrupt). Stopping gracefully.")
    except Exception as e:
        logger.error(f"Scheduler loop error: {e}", exc_info=True)

    return runs_completed


if __name__ == "__main__":
    if "--once" in sys.argv:
        os.environ["REPORT_SCHEDULE_ONCE"] = "true"
    start_scheduler()
