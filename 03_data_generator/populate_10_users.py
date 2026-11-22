import random
from datetime import date, timedelta
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="banking_user",
        password="Bank@1234",
        database="mini_core_banking",
        use_pure=True
    )

def seed_10_users():
    conn = get_connection()
    cursor = conn.cursor()

    print("1. Seeding Branches, Account Types & Roles...")
    cursor.executemany("""
        INSERT IGNORE INTO branches (branch_code, branch_name, ifsc_code, city, state)
        VALUES (%s, %s, %s, %s, %s)
    """, [
        ("BR001", "Alwar Main Branch", "MCBK0000001", "Alwar", "Rajasthan"),
        ("BR002", "Jaipur C-Scheme Branch", "MCBK0000002", "Jaipur", "Rajasthan"),
        ("BR003", "Gurugram Cyber City Branch", "MCBK0000003", "Gurugram", "Haryana"),
    ])

    cursor.executemany("""
        INSERT IGNORE INTO account_types (type_name, min_balance, interest_rate, daily_txn_limit)
        VALUES (%s, %s, %s, %s)
    """, [
        ("Savings", 2000.00, 3.50, 200000.00),
        ("Current", 10000.00, 0.00, 1000000.00),
        ("Salary", 0.00, 3.75, 300000.00),
    ])

    cursor.executemany("""
        INSERT IGNORE INTO roles (role_name, can_approve_loans, can_freeze_accounts, can_reverse_txns, max_approval_limit)
        VALUES (%s, %s, %s, %s, %s)
    """, [
        ("Admin", True, True, True, 10000000.00),
        ("Branch_Manager", True, True, True, 2500000.00),
        ("Teller", False, False, False, 100000.00),
        ("Compliance_Officer", False, True, True, 0.00),
    ])

    cursor.executemany("""
        INSERT IGNORE INTO employees (emp_code, full_name, email, branch_id, role_id, is_active, hired_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, [
        ("EMP101", "Rajeshwari Rathore", "rajeshwari.r@corebank.in", 1, 2, True, "2022-04-15"),
        ("EMP102", "Vikramaditya Singh", "vikram.s@corebank.in", 2, 3, True, "2023-08-01"),
        ("EMP103", "Nandini Menon", "nandini.m@corebank.in", 3, 4, True, "2021-11-10"),
        ("EMP104", "Arjun Deshmukh", "arjun.d@corebank.in", 1, 4, True, "2022-01-20"),
    ])
    conn.commit()

    print("2. Creating 10 Synthetic Customers & Verified KYC Profiles...")
    users = [
        ("CIF1001", "Aarav Sharma", "1996-05-14", "aarav.sharma@example.in", "9829011001", "Scheme No 2, Alwar, Rajasthan", "Sunita Sharma", "Mother", "ABCPS1234A", "XXXX-XXXX-4101", "Low", 1, 1, 85000.00),
        ("CIF1002", "Priya Verma", "1998-09-22", "priya.verma@example.in", "9829011002", "Malviya Nagar, Jaipur, Rajasthan", "Rakesh Verma", "Father", "BCHPV5678B", "XXXX-XXXX-4102", "Low", 2, 3, 142000.00),
        ("CIF1003", "Rohan Kulkarni", "1991-02-11", "rohan.k@example.in", "9829011003", "DLF Phase 3, Gurugram, Haryana", "Sneha Kulkarni", "Spouse", "DEFPR9012C", "XXXX-XXXX-4103", "Medium", 3, 2, 460000.00),
        ("CIF1004", "Ananya Nair", "2000-11-30", "ananya.nair@example.in", "9829011004", "Vaishali Nagar, Jaipur, Rajasthan", "Mohan Nair", "Father", "GHIPN3456D", "XXXX-XXXX-4104", "Low", 2, 1, 54000.00),
        ("CIF1005", "Kabir Malhotra", "1989-07-19", "kabir.m@example.in", "9829011005", "Sector 45, Gurugram, Haryana", "Meera Malhotra", "Spouse", "JKLPM7890E", "XXXX-XXXX-4105", "High", 3, 2, 620000.00),
        ("CIF1006", "Sneha Choudhary", "1997-03-08", "sneha.c@example.in", "9829011006", "Lajpat Nagar, Alwar, Rajasthan", "Harish Choudhary", "Father", "MNOPC2345F", "XXXX-XXXX-4106", "Low", 1, 3, 98500.00),
        ("CIF1007", "Devansh Joshi", "1994-12-25", "devansh.j@example.in", "9829011007", "C-Scheme, Jaipur, Rajasthan", "Kavita Joshi", "Mother", "PQRPJ6789G", "XXXX-XXXX-4107", "Low", 2, 1, 115000.00),
        ("CIF1008", "Meera Krishnan", "1993-08-17", "meera.k@example.in", "9829011008", "Sushant Lok, Gurugram, Haryana", "Suresh Krishnan", "Father", "STUPK1122H", "XXXX-XXXX-4108", "Medium", 3, 3, 210000.00),
        ("CIF1009", "Yashvardhan Singh", "1999-01-05", "yash.singh@example.in", "9829011009", "Moti Doongri, Alwar, Rajasthan", "Rajendra Singh", "Father", "VWXPS3344J", "XXXX-XXXX-4109", "Low", 1, 1, 47500.00),
        ("CIF1010", "Tanya Agarwal", "1995-06-28", "tanya.a@example.in", "9829011010", "Raja Park, Jaipur, Rajasthan", "Deepak Agarwal", "Father", "YZAPA5566K", "XXXX-XXXX-4110", "Low", 2, 2, 335000.00),
    ]

    account_ids = []
    for idx, u in enumerate(users, start=1):
        cif, name, dob, email, phone, addr, nom, rel, pan, gov, risk, branch_id, type_id, init_bal = u
        cursor.execute("""
            INSERT IGNORE INTO customers (customer_cif, full_name, date_of_birth, email, phone, address, nominee_name, nominee_relation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cif, name, dob, email, phone, addr, nom, rel))
        conn.commit()

        cursor.execute("SELECT customer_id FROM customers WHERE customer_cif = %s", (cif,))
        cust_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT IGNORE INTO kyc_details (customer_id, masked_pan, masked_gov_id, kyc_status, risk_category, verified_at)
            VALUES (%s, %s, %s, 'Verified', %s, NOW())
        """, (cust_id, pan, gov, risk))

        acc_num = f"1001000{idx:02d}001"
        cursor.execute("SELECT account_id FROM accounts WHERE account_number = %s", (acc_num,))
        existing_acc = cursor.fetchone()

        if not existing_acc:
            cursor.execute("""
                INSERT INTO accounts (account_number, customer_id, branch_id, type_id, balance, status)
                VALUES (%s, %s, %s, %s, 0.00, 'Active')
            """, (acc_num, cust_id, branch_id, type_id))
            conn.commit()
            acc_id = cursor.lastrowid
            # Deposit opening balance via ACID stored procedure
            cursor.callproc("sp_deposit_funds", [acc_id, init_bal, "Initial Account Opening Deposit"])
            conn.commit()
        else:
            acc_id = existing_acc[0]

        account_ids.append(acc_id)

    print("3. Executing 18 Sample UPI / NEFT / IMPS Transfers (including 1 High-Value Alert)...")
    transfers = [
        (account_ids[0], account_ids[1], 4500.00, "UPI", "Rent Split Payment"),
        (account_ids[1], account_ids[3], 12500.00, "IMPS", "Freelance Design Settlement"),
        (account_ids[2], account_ids[4], 48000.00, "NEFT", "Vendor Invoice #409"),
        (account_ids[4], account_ids[9], 135000.00, "NEFT", "Equipment Purchase (High-Value Trigger Test)"),
        (account_ids[5], account_ids[0], 3200.00, "UPI", "Dinner & Travel Reimbursement"),
        (account_ids[6], account_ids[7], 18500.00, "IMPS", "Consultancy Retainer"),
        (account_ids[7], account_ids[2], 25000.00, "NEFT", "Quarterly Subscription"),
        (account_ids[8], account_ids[5], 1800.00, "UPI", "Book Purchase"),
        (account_ids[9], account_ids[6], 31000.00, "NEFT", "Supplier Advance"),
        (account_ids[2], account_ids[0], 15000.00, "IMPS", "Project Bonus"),
        (account_ids[3], account_ids[8], 2750.00, "UPI", "Utility Share"),
        (account_ids[4], account_ids[1], 22000.00, "NEFT", "Consulting Fee"),
    ]

    for src, dst, amt, ch, rem in transfers:
        try:
            cursor.callproc("sp_transfer_funds", [src, dst, amt, ch, rem])
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Skipped transfer ({src}->{dst}): {e}")

    print("4. Creating 3 Active Loans & EMI Schedules...")
    sample_loans = [
        ("LN20260001", 1, account_ids[0], "Personal", 150000.00, 11.50, 12, 13292.00),
        ("LN20260002", 3, account_ids[2], "Vehicle", 500000.00, 9.25, 24, 22902.00),
        ("LN20260003", 7, account_ids[6], "Education", 300000.00, 8.50, 18, 17805.00),
    ]
    for l_num, c_id, a_id, l_type, prin, rate, tenure, emi in sample_loans:
        cursor.execute("SELECT loan_id FROM loans WHERE loan_account_number = %s", (l_num,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO loans (loan_account_number, customer_id, linked_account_id, loan_type, principal_amount, interest_rate, tenure_months, emi_amount, outstanding_balance, status, approved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active', NOW())
            """, (l_num, c_id, a_id, l_type, prin, rate, tenure, emi, prin))
            conn.commit()
            loan_id = cursor.lastrowid

            # Generate first 6 monthly installments
            rem_bal = prin
            monthly_r = (rate / 100.0) / 12.0
            for m in range(1, 7):
                interest_part = round(rem_bal * monthly_r, 2)
                principal_part = round(emi - interest_part, 2)
                rem_bal = max(0.0, round(rem_bal - principal_part, 2))
                due_dt = date.today() + timedelta(days=30 * (m - 1))
                cursor.execute("""
                    INSERT INTO loan_repayments (loan_id, installment_number, due_date, emi_due, principal_component, interest_component, late_fee, amount_paid, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, 0.00, 0.00, 'Upcoming')
                """, (loan_id, m, due_dt, emi, principal_part, interest_part))
            conn.commit()

    cursor.close()
    conn.close()
    print("✅ Done! 10 synthetic users, accounts, ledger entries, loans, and fraud alerts are ready.")

if __name__ == "__main__":
    seed_10_users()