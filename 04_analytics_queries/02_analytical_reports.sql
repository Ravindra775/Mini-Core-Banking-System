-- TODO: Add analytical reports using CTEs, window functions, joins, and subqueries.
-- ==========================================================
-- PHASE 5B: INTERVIEW-READY ANALYTICAL QUERIES (CTEs, WINDOW FUNCTIONS)
-- ==========================================================

USE mini_core_banking;

-- QUERY 1: Top 3 Richest Customers Per Branch (Window Function: DENSE_RANK)
WITH RankedCustomers AS (
    SELECT 
        b.branch_name,
        c.customer_cif,
        c.full_name,
        a.account_number,
        a.balance,
        DENSE_RANK() OVER (PARTITION BY b.branch_id ORDER BY a.balance DESC) AS branch_rank
    FROM accounts a
    JOIN customers c ON a.customer_id = c.customer_id
    JOIN branches b ON a.branch_id = b.branch_id
    WHERE a.status = 'Active'
)
SELECT * FROM RankedCustomers WHERE branch_rank <= 3;

-- QUERY 2: Customers Holding Above-Average Bank Balance (Subquery)
SELECT 
    c.customer_cif,
    c.full_name,
    a.account_number,
    t.type_name,
    a.balance,
    ROUND(a.balance - (SELECT AVG(balance) FROM accounts WHERE status = 'Active'), 2) AS above_avg_by
FROM accounts a
JOIN customers c ON a.customer_id = c.customer_id
JOIN account_types t ON a.type_id = t.type_id
WHERE a.status = 'Active'
  AND a.balance > (SELECT AVG(balance) FROM accounts WHERE status = 'Active')
ORDER BY a.balance DESC;

-- QUERY 3: Transaction Channel Success vs Failure Rate Breakdown (Conditional Aggregation)
SELECT 
    txn_type,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) AS successful_txns,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_txns,
    SUM(CASE WHEN status = 'Reversed' THEN 1 ELSE 0 END) AS reversed_txns,
    ROUND(SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
    COALESCE(SUM(CASE WHEN status = 'Success' THEN amount ELSE 0 END), 0.00) AS total_volume_inr
FROM transactions
GROUP BY txn_type
ORDER BY total_volume_inr DESC;

-- QUERY 4: Account Statement with Running Balance Verification (Window Function: SUM OVER)
SELECT 
    te.entry_id,
    t.txn_reference,
    t.txn_type,
    te.entry_type,
    te.amount,
    te.balance_after AS ledger_snapshot_balance,
    SUM(CASE WHEN te.entry_type = 'CREDIT' THEN te.amount ELSE -te.amount END) 
        OVER (PARTITION BY te.account_id ORDER BY te.entry_id) AS recalculated_running_balance,
    te.created_at
FROM transaction_entries te
JOIN transactions t ON te.transaction_id = t.transaction_id
WHERE te.account_id = 1
ORDER BY te.entry_id ASC;

-- QUERY 5: Dormant & Frozen Accounts Requiring Compliance Follow-Up
SELECT 
    a.account_number,
    c.customer_cif,
    c.full_name,
    c.phone,
    k.kyc_status,
    k.risk_category,
    a.status AS account_status,
    a.balance,
    b.branch_name
FROM accounts a
JOIN customers c ON a.customer_id = c.customer_id
JOIN kyc_details k ON c.customer_id = k.customer_id
JOIN branches b ON a.branch_id = b.branch_id
WHERE a.status IN ('Dormant', 'Frozen')
ORDER BY a.balance DESC;

-- QUERY 6: High-Risk Customers with Active Loans and Open Fraud Alerts (Multi-Join CTE)
WITH FraudCounts AS (
    SELECT account_id, COUNT(*) AS open_alerts
    FROM fraud_alerts
    WHERE alert_status = 'Open'
    GROUP BY account_id
)
SELECT 
    c.customer_cif,
    c.full_name,
    k.risk_category,
    a.account_number,
    a.balance,
    COALESCE(fc.open_alerts, 0) AS open_fraud_alerts,
    COUNT(l.loan_id) AS active_loans,
    COALESCE(SUM(l.outstanding_balance), 0.00) AS total_loan_debt
FROM customers c
JOIN kyc_details k ON c.customer_id = k.customer_id
JOIN accounts a ON c.customer_id = a.customer_id
LEFT JOIN FraudCounts fc ON a.account_id = fc.account_id
LEFT JOIN loans l ON c.customer_id = l.customer_id AND l.status = 'Active'
WHERE k.risk_category = 'High' OR fc.open_alerts > 0
GROUP BY c.customer_cif, c.full_name, k.risk_category, a.account_number, a.balance, fc.open_alerts
ORDER BY open_fraud_alerts DESC, total_loan_debt DESC;