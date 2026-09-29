"""
setup_database.py
Creates the SQLite database and tables using the SQL schema file.
"""

import sqlite3
import os
import sys


def get_project_root():
    """Return the project root directory (parent of scripts/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_database():
    """Create the SQLite database and run the schema SQL."""
    project_root = get_project_root()

    # Paths
    schema_path = os.path.join(project_root, "sql", "schema.sql")
    db_dir = os.path.join(project_root, "database")
    db_path = os.path.join(db_dir, "reporting.db")

    # Create database directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)

    # Read schema SQL
    if not os.path.exists(schema_path):
        print(f"ERROR: Schema file not found at {schema_path}")
        sys.exit(1)

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    print(f"Schema file : {schema_path}")
    print(f"Database    : {db_path}")

    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("Database created and schema applied successfully.")

        # Verify tables were created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {', '.join(tables)}")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to apply schema — {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
