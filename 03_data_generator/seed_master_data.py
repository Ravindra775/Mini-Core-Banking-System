"""Seed branches, roles, account types, and employees."""
from db_config import get_connection

def seed_master():
    conn = get_connection()
    cursor = conn.cursor()

    print("Seeding Master Data (Branches, Account Types, Roles, Employees)...")

    # 1. Branches
    branches = [
        ('BR001', 'Alwar Main Branch', 'MCBS0000001', 'Alwar', 'Rajasthan'),
        ('BR002', 'Jaipur C-Scheme Branch', 'MCBS0000002', 'Jaipur', 'Rajasthan'),
        ('BR003', 'Delhi Connaught Place', 'MCBS0000003', 'New Delhi', 'Delhi'),
        ('BR004', 'Mumbai Nariman Point', 'MCBS0000004', 'Mumbai', 'Maharashtra'),
        ('BR005', 'Bengaluru MG Road', 'MCBS0000005', 'Bengaluru', 'Karnataka')
    ]
    cursor.executemany("""
        INSERT IGNORE INTO branches (branch_code, branch_name, ifsc_code, city, state)
        VALUES (%s, %s, %s, %s, %s)
    """, branches)

    # 2. Account Types
    account_types = [
        ('Savings', 1000.00, 3.50, 100000.00),
        ('Current', 10000.00, 0.00, 500000.00),
        ('Salary', 0.00, 3.50, 200000.00)
    ]
    cursor.executemany("""
        INSERT IGNORE INTO account_types (type_name, min_balance, interest_rate, daily_txn_limit)
        VALUES (%s, %s, %s, %s)
    """, account_types)

    # 3. Employee Roles
    roles = [
        ('Admin', True, True, True, 10000000.00),
        ('Branch_Manager', True, True, True, 1000000.00),
        ('Teller', False, False, False, 50000.00),
        ('Compliance_Officer', False, True, False, 200000.00)
    ]
    cursor.executemany("""
        INSERT IGNORE INTO roles (role_name, can_approve_loans, can_freeze_accounts, can_reverse_txns, max_approval_limit)
        VALUES (%s, %s, %s, %s, %s)
    """, roles)

    # 4. Employees
    employees = [
        ('EMP001', 'Vikram Rathore', 'vikram.admin@minicorebank.in', 1, 1, '2022-01-15'),
        ('EMP002', 'Ananya Sharma', 'ananya.mgr@minicorebank.in', 1, 2, '2022-06-10'),
        ('EMP003', 'Rohan Verma', 'rohan.teller@minicorebank.in', 1, 3, '2023-03-20'),
        ('EMP004', 'Sneha Nair', 'sneha.compliance@minicorebank.in', 2, 4, '2023-08-01'),
        ('EMP005', 'Kabir Mehta', 'kabir.mgr@minicorebank.in', 3, 2, '2022-11-12')
    ]
    cursor.executemany("""
        INSERT IGNORE INTO employees (emp_code, full_name, email, branch_id, role_id, hired_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, employees)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Master data seeded successfully!")

if __name__ == "__main__":
    seed_master()