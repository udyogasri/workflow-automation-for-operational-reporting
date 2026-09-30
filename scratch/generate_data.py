import csv
import os
import random
from datetime import datetime, timedelta

def generate_datasets():
    random.seed(42)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    employees = [
        "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sneha Reddy", "Vikram Singh",
        "Anita Desai", "Ravi Menon", "Kavita Nair", "Suresh Iyer", "Deepa Joshi",
        "Manoj Tiwari", "Pooja Gupta", "Arjun Rao", "Meera Pillai", "Kiran Das",
        "Neha Agarwal", "Sanjay Verma", "Lakshmi Bhat", "Rahul Mishra", "Divya Saxena",
        "Ramesh Pandey", "Swati Kulkarni", "Ashok Mehta", "Geeta Yadav", "Tarun Kapoor",
        "Anjali Singh", "Siddharth Rao", "Bhavna Patel", "Alok Kumar", "Sunita Sharma"
    ]

    start_date = datetime(2026, 9, 1)

    # -------------------------------------------------------------
    # 1. OPERATIONS (1000 valid + 5 invalid/duplicate = 1005 raw)
    # -------------------------------------------------------------
    ops_rows = []
    ops_header = ["record_id", "employee", "team", "date", "department", "status", "quantity", "target", "actual_value", "shift", "notes"]
    ops_teams = ["Team Alpha", "Team Beta", "Team Gamma"]
    ops_depts = ["Manufacturing", "Logistics", "Quality Control"]
    ops_statuses = ["Completed", "In Progress", "Failed"]
    ops_status_weights = [0.78, 0.12, 0.10]
    ops_shifts = ["Morning", "Afternoon", "Night"]

    for i in range(1, 1001):
        rec_id = f"OPS-{i:04d}"
        emp = random.choice(employees)
        team = random.choice(ops_teams)
        date_str = (start_date + timedelta(days=random.randint(0, 29))).strftime("%Y-%m-%d")
        dept = random.choice(ops_depts)
        status = random.choices(ops_statuses, weights=ops_status_weights)[0]
        qty = random.randint(30, 200)
        target = float(random.randint(50, 200))
        if status == "Completed":
            actual = round(target * random.uniform(0.85, 1.25), 1)
        elif status == "In Progress":
            actual = round(target * random.uniform(0.40, 0.70), 1)
        else: # Failed
            actual = round(target * random.uniform(0.10, 0.35), 1)
        shift = random.choice(ops_shifts)
        note = "Standard operations"
        ops_rows.append([rec_id, emp, team, date_str, dept, status, qty, target, actual, shift, note])

    # Add 5 invalid / duplicate rows
    ops_rows.append(["OPS-1001", "Invalid Date Emp", "Team Alpha", "2026/09/31", "Manufacturing", "Completed", 100, 100.0, 100.0, "Morning", "Bad date format"])
    ops_rows.append(["OPS-1002", "Bad Target Emp", "Team Beta", "2026-09-15", "Logistics", "Completed", 100, "INVALID_FLOAT", 100.0, "Afternoon", "Bad float target"])
    ops_rows.append(["OPS-1003", "", "Team Gamma", "2026-09-15", "Quality Control", "Completed", 100, 100.0, 100.0, "Night", "Missing employee"])
    ops_rows.append(["OPS-1004", "Bad Qty Emp", "Team Alpha", "2026-09-15", "Manufacturing", "In Progress", "NOT_AN_INT", 100.0, 50.0, "Morning", "Bad int qty"])
    ops_rows.append(["OPS-0005", "Duplicate ID Emp", "Team Beta", "2026-09-15", "Logistics", "Completed", 100, 100.0, 100.0, "Afternoon", "Duplicate ID"])

    with open(os.path.join(data_dir, "operations.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ops_header)
        writer.writerows(ops_rows)

    # -------------------------------------------------------------
    # 2. SALES (1000 valid + 2 invalid = 1002 raw)
    # -------------------------------------------------------------
    sales_rows = []
    sales_header = ["record_id", "employee", "team", "date", "department", "status", "quantity", "target", "actual_value", "region", "product_category"]
    sales_teams = ["Sales Team A", "Sales Team B", "Sales Team C"]
    sales_depts = ["Retail", "Wholesale", "Online"]
    sales_statuses = ["Closed", "Pipeline", "Lost"]
    sales_status_weights = [0.78, 0.12, 0.10]
    sales_regions = ["North", "South", "East", "West"]
    sales_cats = ["Electronics", "Furniture", "Clothing"]

    for i in range(1, 1001):
        rec_id = f"SLS-{i:04d}"
        emp = random.choice(employees)
        team = random.choice(sales_teams)
        date_str = (start_date + timedelta(days=random.randint(0, 29))).strftime("%Y-%m-%d")
        dept = random.choice(sales_depts)
        status = random.choices(sales_statuses, weights=sales_status_weights)[0]
        qty = random.randint(5, 60)
        target = float(random.randint(10000, 60000))
        if status == "Closed":
            actual = round(target * random.uniform(0.90, 1.30), 2)
        elif status == "Pipeline":
            actual = 0.0
        else: # Lost
            actual = 0.0
        region = random.choice(sales_regions)
        cat = random.choice(sales_cats)
        sales_rows.append([rec_id, emp, team, date_str, dept, status, qty, target, actual, region, cat])

    # Add 2 invalid rows
    sales_rows.append(["SLS-1001", "Invalid Date Emp", "Sales Team A", "invalid-date", "Retail", "Closed", 10, 15000.0, 16000.0, "North", "Electronics"])
    sales_rows.append(["SLS-1002", "Bad Target Emp", "Sales Team B", "2026-09-20", "Wholesale", "Closed", 20, "abc", 20000.0, "South", "Furniture"])

    with open(os.path.join(data_dir, "sales.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(sales_header)
        writer.writerows(sales_rows)

    # -------------------------------------------------------------
    # 3. SUPPORT (1000 valid + 8 invalid/duplicate = 1008 raw)
    # -------------------------------------------------------------
    sup_rows = []
    sup_header = ["record_id", "employee", "team", "date", "department", "status", "tickets_count", "target", "actual_value", "priority", "resolution_time_hrs"]
    sup_teams = ["Support Team 1", "Support Team 2", "Support Team 3"]
    sup_depts = ["Technical Support", "Customer Service", "Billing Support"]
    sup_statuses = ["Resolved", "Pending", "Escalated"]
    sup_status_weights = [0.78, 0.12, 0.10]
    sup_priorities = ["Low", "Medium", "High", "Critical"]

    for i in range(1, 1001):
        rec_id = f"SUP-{i:04d}"
        emp = random.choice(employees)
        team = random.choice(sup_teams)
        date_str = (start_date + timedelta(days=random.randint(0, 29))).strftime("%Y-%m-%d")
        dept = random.choice(sup_depts)
        status = random.choices(sup_statuses, weights=sup_status_weights)[0]
        target = float(random.randint(5, 25))
        if status == "Resolved":
            actual = float(int(target * random.uniform(0.85, 1.25)))
            t_count = int(actual)
            res_time = round(random.uniform(0.5, 3.5), 1)
        elif status == "Pending":
            actual = float(int(target * random.uniform(0.30, 0.60)))
            t_count = int(actual)
            res_time = 0.0
        else: # Escalated
            actual = float(int(target * random.uniform(0.10, 0.30)))
            t_count = int(actual)
            res_time = 0.0
        prio = random.choice(sup_priorities)
        sup_rows.append([rec_id, emp, team, date_str, dept, status, t_count, target, actual, prio, res_time])

    # Add 8 invalid / duplicate rows
    sup_rows.append(["SUP-1001", "Invalid Date Emp", "Support Team 1", "2026-13-45", "Technical Support", "Resolved", 10, 10.0, 10.0, "High", 2.0])
    sup_rows.append(["SUP-1002", "", "Support Team 2", "2026-09-18", "Customer Service", "Resolved", 15, 15.0, 15.0, "Medium", 1.0])
    sup_rows.append(["SUP-1003", "Bad Ticket Count", "Support Team 3", "2026-09-18", "Billing Support", "Pending", "XYZ", 12.0, 5.0, "High", 0.0])
    sup_rows.append(["SUP-1004", "Bad Target Emp", "Support Team 1", "2026-09-18", "Technical Support", "Resolved", 10, "NaN_Value", 10.0, "Low", 1.5])
    sup_rows.append(["SUP-1005", "Bad Date Emp 2", "Support Team 2", "2026-09-99", "Customer Service", "Resolved", 12, 12.0, 12.0, "Medium", 0.8])
    sup_rows.append(["SUP-1006", "Empty Dept Emp", "Support Team 3", "2026-09-18", "", "Billing Support", 10, 10.0, 10.0, "Low", 1.0])
    sup_rows.append(["SUP-1007", "Empty Status Emp", "Support Team 1", "2026-09-18", "Technical Support", "", 10, 10.0, 10.0, "High", 2.0])
    sup_rows.append(["SUP-0010", "Duplicate ID Emp", "Support Team 2", "2026-09-18", "Customer Service", "Resolved", 15, 15.0, 15.0, "Medium", 1.0])

    with open(os.path.join(data_dir, "support.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(sup_header)
        writer.writerows(sup_rows)

    print("Data generation complete!")
    print(f"  operations.csv: {len(ops_rows)} rows (1000 valid, 5 invalid/duplicate)")
    print(f"  sales.csv:      {len(sales_rows)} rows (1000 valid, 2 invalid)")
    print(f"  support.csv:    {len(sup_rows)} rows (1000 valid, 8 invalid/duplicate)")

if __name__ == "__main__":
    generate_datasets()
