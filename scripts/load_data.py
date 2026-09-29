"""
load_data.py
Reads CSV files, validates data, and loads valid records into the SQLite database.
Logs invalid records and errors without crashing.
"""

import csv
import sqlite3
import os
import sys
import logging
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def get_project_root():
    """Return the project root directory (parent of scripts/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Define expected columns for each CSV / table
TABLE_CONFIGS = {
    "operations": {
        "csv_file": "operations.csv",
        "required_columns": [
            "record_id", "employee", "team", "date", "department",
            "status", "quantity", "target", "actual_value",
        ],
        "optional_columns": ["shift", "notes"],
        "integer_columns": ["quantity"],
        "float_columns": ["target", "actual_value"],
        "date_columns": ["date"],
        "insert_sql": (
            "INSERT OR IGNORE INTO operations "
            "(record_id, employee, team, date, department, status, "
            "quantity, target, actual_value, shift, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        "column_order": [
            "record_id", "employee", "team", "date", "department",
            "status", "quantity", "target", "actual_value", "shift", "notes",
        ],
    },
    "sales": {
        "csv_file": "sales.csv",
        "required_columns": [
            "record_id", "employee", "team", "date", "department",
            "status", "quantity", "target", "actual_value",
        ],
        "optional_columns": ["region", "product_category"],
        "integer_columns": ["quantity"],
        "float_columns": ["target", "actual_value"],
        "date_columns": ["date"],
        "insert_sql": (
            "INSERT OR IGNORE INTO sales "
            "(record_id, employee, team, date, department, status, "
            "quantity, target, actual_value, region, product_category) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        "column_order": [
            "record_id", "employee", "team", "date", "department",
            "status", "quantity", "target", "actual_value",
            "region", "product_category",
        ],
    },
    "support": {
        "csv_file": "support.csv",
        "required_columns": [
            "record_id", "employee", "team", "date", "department",
            "status", "tickets_count", "target", "actual_value",
        ],
        "optional_columns": ["priority", "resolution_time_hrs"],
        "integer_columns": ["tickets_count"],
        "float_columns": ["target", "actual_value", "resolution_time_hrs"],
        "date_columns": ["date"],
        "insert_sql": (
            "INSERT OR IGNORE INTO support "
            "(record_id, employee, team, date, department, status, "
            "tickets_count, target, actual_value, priority, resolution_time_hrs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        "column_order": [
            "record_id", "employee", "team", "date", "department",
            "status", "tickets_count", "target", "actual_value",
            "priority", "resolution_time_hrs",
        ],
    },
}


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

def setup_logger(project_root):
    """Configure logging to file and console."""
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"load_data_{timestamp}.log")

    logger = logging.getLogger("load_data")
    logger.setLevel(logging.DEBUG)

    # File handler -- full detail
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

    # Console handler -- info and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(f"Log file: {log_file}")
    return logger


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_columns(header, required_columns, table_name, logger):
    """Check that all required columns exist in the CSV header."""
    missing = [c for c in required_columns if c not in header]
    if missing:
        logger.error(
            f"[{table_name}] Missing required columns: {missing}"
        )
        return False
    return True


def validate_date(value, field, row_id, table_name, logger):
    """Validate a date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        logger.warning(
            f"[{table_name}] Row {row_id}: Invalid date '{value}' in column '{field}'"
        )
        return False


def validate_integer(value, field, row_id, table_name, logger):
    """Validate and convert a value to int."""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        logger.warning(
            f"[{table_name}] Row {row_id}: Invalid integer '{value}' in column '{field}'"
        )
        return False


def validate_float(value, field, row_id, table_name, logger):
    """Validate and convert a value to float."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        logger.warning(
            f"[{table_name}] Row {row_id}: Invalid float '{value}' in column '{field}'"
        )
        return False


def validate_row(row, config, table_name, logger):
    """
    Validate a single CSV row. Returns (is_valid, reason) tuple.
    """
    row_id = row.get("record_id", "UNKNOWN")

    # Check required fields are not empty
    for col in config["required_columns"]:
        value = row.get(col, "").strip()
        if not value:
            logger.warning(
                f"[{table_name}] Row {row_id}: Empty required field '{col}'"
            )
            return False, f"Empty required field '{col}'"

    # Validate dates
    for col in config["date_columns"]:
        if not validate_date(row[col].strip(), col, row_id, table_name, logger):
            return False, f"Invalid date in '{col}'"

    # Validate integers
    for col in config["integer_columns"]:
        if not validate_integer(row[col].strip(), col, row_id, table_name, logger):
            return False, f"Invalid integer in '{col}'"

    # Validate floats
    for col in config["float_columns"]:
        value = row.get(col, "").strip()
        # Optional float columns may be empty
        if col in config["optional_columns"] and not value:
            continue
        if not validate_float(value, col, row_id, table_name, logger):
            return False, f"Invalid float in '{col}'"

    return True, None


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csv_to_table(table_name, config, data_dir, conn, logger):
    """Read a CSV, validate rows, and insert valid records into SQLite."""
    csv_path = os.path.join(data_dir, config["csv_file"])

    if not os.path.exists(csv_path):
        logger.error(f"[{table_name}] CSV file not found: {csv_path}")
        return

    logger.info(f"[{table_name}] Loading {csv_path}")

    valid_count = 0
    invalid_count = 0
    duplicate_count = 0
    seen_ids = set()

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames

        if header is None:
            logger.error(f"[{table_name}] CSV file is empty or has no header.")
            return

        # Strip whitespace from header names
        header = [h.strip() for h in header]

        # Validate columns
        all_expected = config["required_columns"] + config["optional_columns"]
        if not validate_columns(header, config["required_columns"], table_name, logger):
            logger.error(f"[{table_name}] Skipping file due to missing columns.")
            return

        for row_num, row in enumerate(reader, start=2):
            # Strip whitespace from keys and values
            row = {k.strip(): (v.strip() if v else "") for k, v in row.items()}

            record_id = row.get("record_id", "").strip()

            # Check for duplicate IDs within the file
            if record_id in seen_ids:
                logger.warning(
                    f"[{table_name}] Row {row_num}: Duplicate record_id '{record_id}' -- skipping."
                )
                duplicate_count += 1
                invalid_count += 1
                continue
            seen_ids.add(record_id)

            # Validate row
            is_valid, reason = validate_row(row, config, table_name, logger)
            if not is_valid:
                invalid_count += 1
                continue

            # Build row tuple in the correct column order, converting types
            values = []
            for col in config["column_order"]:
                raw = row.get(col, "")
                if col in config["integer_columns"]:
                    values.append(int(raw))
                elif col in config["float_columns"]:
                    values.append(float(raw) if raw else None)
                else:
                    values.append(raw if raw else None)

            try:
                conn.execute(config["insert_sql"], tuple(values))
                valid_count += 1
            except sqlite3.IntegrityError as e:
                logger.warning(
                    f"[{table_name}] Row {row_num}: DB integrity error -- {e}"
                )
                invalid_count += 1
            except sqlite3.Error as e:
                logger.error(
                    f"[{table_name}] Row {row_num}: DB error -- {e}"
                )
                invalid_count += 1

    conn.commit()

    logger.info(
        f"[{table_name}] Done -- {valid_count} inserted, "
        f"{invalid_count} invalid, {duplicate_count} duplicates."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    project_root = get_project_root()
    logger = setup_logger(project_root)

    data_dir = os.path.join(project_root, "data")
    db_path = os.path.join(project_root, "database", "reporting.db")

    if not os.path.exists(db_path):
        logger.error(
            f"Database not found at {db_path}. "
            "Run setup_database.py first."
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Starting data load process")
    logger.info("=" * 60)

    conn = sqlite3.connect(db_path)

    try:
        for table_name, config in TABLE_CONFIGS.items():
            load_csv_to_table(table_name, config, data_dir, conn, logger)

        # Summary: row counts in each table
        logger.info("-" * 60)
        logger.info("DATABASE SUMMARY")
        logger.info("-" * 60)
        for table_name in TABLE_CONFIGS:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table_name:15s} : {count} rows")
        logger.info("-" * 60)

    finally:
        conn.close()

    logger.info("Data load process completed.")


if __name__ == "__main__":
    main()
