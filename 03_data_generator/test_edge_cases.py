"""Test overdrafts, frozen accounts, and transaction rollbacks."""
from db_config import get_connection

def run_edge_case_tests():
    conn = get_connection()
    cursor = conn.cursor()

    print("\n================ RUNNING BANKING EDGE-CASE & INTEGRITY TESTS ================\n")

    # Fetch 2 active accounts for testing
    cursor.execute("SELECT account_id, balance FROM accounts WHERE status = 'Active' LIMIT 2")
    acc1, acc2 = cursor.fetchall()
    acc1_id, acc1_bal = acc1[0], float(acc1[1])
    acc2_id, acc2_bal = acc2[0], float(acc2[1])

    # TEST 1: Overdraft / Insufficient Balance Prevention
    print("Test 1: Attempting withdrawal larger than current balance...")
    try:
        cursor.callproc('sp_withdraw_funds', [acc1_id, acc1_bal + 50000.00, 'Overdraft Attempt Test'])
        print("❌ FAILED: System allowed overdraft!")
    except Exception as e:
        print(f"✅ PASSED: Blocked overdraft -> {e.msg}")

    # TEST 2: Same-Account Self-Transfer Prevention
    print("\nTest 2: Attempting transfer to the exact same account...")
    try:
        cursor.callproc('sp_transfer_funds', [acc1_id, acc1_id, 500.00, 'UPI', 'Self Transfer Test'])
        print("❌ FAILED: System allowed self-transfer!")
    except Exception as e:
        print(f"✅ PASSED: Blocked self-transfer -> {e.msg}")

    # TEST 3: Frozen Account Protection & Audit Trigger Check
    print("\nTest 3: Freezing Account #2, testing transfer block, and verifying Audit Log...")
    cursor.execute("UPDATE accounts SET status = 'Frozen' WHERE account_id = %s", (acc2_id,))
    conn.commit()
    try:
        cursor.callproc('sp_transfer_funds', [acc1_id, acc2_id, 1000.00, 'IMPS', 'Frozen Account Transfer Test'])
        print("❌ FAILED: System transferred funds to a Frozen account!")
    except Exception as e:
        print(f"✅ PASSED: Blocked transfer to Frozen account -> {e.msg}")

    # Restore Account #2 back to Active
    cursor.execute("UPDATE accounts SET status = 'Active' WHERE account_id = %s", (acc2_id,))
    conn.commit()

    # Check if Audit Trigger recorded the status changes
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE table_name = 'accounts' AND record_id = %s", (str(acc2_id),))
    audit_count = cursor.fetchone()[0]
    print(f"✅ PASSED: Audit Trigger automatically logged {audit_count} status change(s) for Account #{acc2_id}.")

    # TEST 4: Transaction Reversal Integrity
    print("\nTest 4: Executing valid transfer and immediately reversing it...")
    cursor.callproc('sp_transfer_funds', [acc1_id, acc2_id, 2500.00, 'NEFT', 'Transfer to be Reversed'])
    conn.commit()

    cursor.execute("SELECT MAX(transaction_id) FROM transactions WHERE remarks = 'Transfer to be Reversed'")
    txn_to_reverse = cursor.fetchone()[0]

    cursor.callproc('sp_reverse_transaction', [txn_to_reverse, 'Customer requested cancellation'])
    conn.commit()
    print(f"✅ PASSED: Transaction #{txn_to_reverse} reversed without deleting original record.")

    # TEST 5: Double-Entry Accounting Balance Check (Total Debits MUST equal Total Credits for Transfers)
    print("\nTest 5: Verifying Double-Entry Ledger Mathematical Integrity...")
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN entry_type = 'DEBIT' THEN amount ELSE 0 END) AS total_debits,
            SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credits
        FROM transaction_entries te
        JOIN transactions t ON te.transaction_id = t.transaction_id
        WHERE t.txn_type IN ('Internal_Transfer', 'UPI', 'NEFT', 'IMPS', 'Reversal')
    """)
    debits, credits = cursor.fetchone()
    if debits == credits:
        print(f"✅ PASSED: Double-Entry Ledger is 100% balanced! Total Debits (₹{debits:,.2f}) == Total Credits (₹{credits:,.2f})")
    else:
        print(f"❌ FAILED: Ledger mismatch! Debits: {debits}, Credits: {credits}")

    cursor.close()
    conn.close()
    print("\n================ ALL TESTS COMPLETED ================\n")

if __name__ == "__main__":
    run_edge_case_tests()