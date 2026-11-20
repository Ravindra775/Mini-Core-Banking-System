"""Generate realistic banking test data."""
import random
from datetime import datetime, timedelta
from faker import Faker
from db_config import get_connection

fake = Faker('en_IN')

def generate_data(num_customers=150, num_transfers=1200):
    conn = get_connection()
    cursor = conn.cursor()

    print(f"Generating {num_customers} customers, KYC records, accounts, and cards...")
    account_ids = []

    for i in range(1, num_customers + 1):
        cif = f"CIF{100000 + i}"
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=19, maximum_age=70)
        email = f"user{i}_{fake.user_name()}@example.com"
        phone = f"9{random.randint(100000000, 999999999)}"
        address = fake.address().replace('\n', ', ')
        nominee = fake.name()
        relation = random.choice(['Spouse', 'Father', 'Mother', 'Son', 'Daughter', 'Brother'])

        cursor.execute("""
            INSERT INTO customers (customer_cif, full_name, date_of_birth, email, phone, address, nominee_name, nominee_relation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cif, name, dob, email, phone, address, nominee, relation))
        cust_id = cursor.lastrowid

        # Masked Demo PAN & Gov ID
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
        last_char = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        masked_pan = f"{letters}****{last_char}"
        masked_gov_id = f"GOV-ID-{100000 + i}"
        kyc_status = random.choices(['Verified', 'Pending', 'Rejected'], weights=[85, 10, 5])[0]
        risk = random.choices(['Low', 'Medium', 'High'], weights=[75, 20, 5])[0]
        verified_at = datetime.now() if kyc_status == 'Verified' else None

        cursor.execute("""
            INSERT INTO kyc_details (customer_id, masked_pan, masked_gov_id, kyc_status, risk_category, verified_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cust_id, masked_pan, masked_gov_id, kyc_status, risk, verified_at))

        # Create 1 or 2 accounts per customer
        num_accs = random.choices([1, 2], weights=[70, 30])[0]
        for a_idx in range(num_accs):
            acc_num = f"1001{cust_id:05d}{a_idx + 1:03d}"
            branch_id = random.randint(1, 5)
            type_id = random.choices([1, 2, 3], weights=[65, 20, 15])[0]
            status = random.choices(['Active', 'Dormant', 'Frozen'], weights=[88, 8, 4])[0]
            initial_deposit = round(random.uniform(15000, 250000), 2)

            cursor.execute("""
                INSERT INTO accounts (account_number, customer_id, branch_id, type_id, balance, status)
                VALUES (%s, %s, %s, %s, %s, 'Active')
            """, (acc_num, cust_id, branch_id, type_id, 0.00))
            acc_id = cursor.lastrowid

            # Seed initial deposit via Stored Procedure (creates double-entry ledger!)
            cursor.callproc('sp_deposit_funds', [acc_id, initial_deposit, 'Initial Account Opening Deposit'])

            # Set final account status (triggers audit log if Dormant/Frozen!)
            if status != 'Active':
                cursor.execute("UPDATE accounts SET status = %s WHERE account_id = %s", (status, acc_id))
            else:
                account_ids.append(acc_id)

            # Issue Debit Card for 80% of accounts
            if random.random() < 0.80:
                card_num = f"XXXX-XXXX-XXXX-{random.randint(1000, 9999)}"
                card_type = random.choice(['RuPay Classic', 'Visa Platinum', 'Mastercard Gold'])
                expiry = datetime.now().date() + timedelta(days=random.randint(365, 1825))
                try:
                    cursor.execute("""
                        INSERT INTO cards (account_id, masked_card_number, card_type, expiry_date)
                        VALUES (%s, %s, %s, %s)
                    """, (acc_id, card_num, card_type, expiry))
                except Exception:
                    pass

    conn.commit()
    print(f"✅ Created {num_customers} customers and {len(account_ids)} active accounts.")

    # Generate Beneficiaries
    print("Adding beneficiaries and executing ACID transfers...")
    for acc_id in random.sample(account_ids, min(80, len(account_ids))):
        cursor.execute("SELECT customer_id FROM accounts WHERE account_id = %s", (acc_id,))
        c_id = cursor.fetchone()[0]
        target_acc = random.choice(account_ids)
        if target_acc != acc_id:
            cursor.execute("""
                SELECT a.account_number, c.full_name, b.ifsc_code
                FROM accounts a JOIN customers c ON a.customer_id = c.customer_id
                JOIN branches b ON a.branch_id = b.branch_id
                WHERE a.account_id = %s
            """, (target_acc,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    INSERT IGNORE INTO beneficiaries (customer_id, beneficiary_name, account_number, ifsc_code)
                    VALUES (%s, %s, %s, %s)
                """, (c_id, row[1], row[0], row[2]))

    # Generate Transfers (including some high-value & rapid transfers to trigger fraud alerts)
    channels = ['UPI', 'NEFT', 'IMPS', 'Internal_Transfer']
    success_count = 0
    for t in range(num_transfers):
        src, dest = random.sample(account_ids, 2)
        # Every 60th transfer is high-value (>= 1,00,000) to test Fraud Trigger
        if t % 60 == 0:
            amount = round(random.uniform(105000, 180000), 2)
        else:
            amount = round(random.uniform(250, 18000), 2)
        channel = random.choice(channels)
        try:
            cursor.callproc('sp_transfer_funds', [src, dest, amount, channel, f'{channel} Payment'])
            success_count += 1
        except Exception:
            # Expected when balance/daily limit fails (automatically logged as Failed!)
            pass

    conn.commit()
    print(f"✅ Executed {success_count} successful double-entry transfers.")

    # Generate 25 Loans & Disburse 20 of them
    print("Creating and disbursing sample loans with EMI schedules...")
    for l_idx in range(1, 26):
        acc_id = random.choice(account_ids)
        cursor.execute("SELECT customer_id FROM accounts WHERE account_id = %s", (acc_id,))
        c_id = cursor.fetchone()[0]
        loan_acc = f"LN2026{l_idx:06d}"
        l_type = random.choice(['Personal', 'Education', 'Home', 'Vehicle'])
        principal = random.choice([50000.00, 120000.00, 250000.00, 500000.00])
        rate = random.choice([8.50, 10.25, 11.50, 12.00])
        tenure = random.choice([12, 24, 36])

        cursor.execute("""
            INSERT INTO loans (loan_account_number, customer_id, linked_account_id, loan_type, principal_amount, interest_rate, tenure_months, emi_amount, outstanding_balance, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0.00, %s, 'Pending')
        """, (loan_acc, c_id, acc_id, l_type, principal, rate, tenure, principal))
        loan_id = cursor.lastrowid

        if l_idx <= 20:
            cursor.callproc('sp_approve_and_disburse_loan', [loan_id])
            # Pay 1st EMI on 10 loans
            if l_idx <= 10:
                cursor.callproc('sp_pay_loan_emi', [loan_id])

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 ALL SYNTHETIC BANKING DATA GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_data()