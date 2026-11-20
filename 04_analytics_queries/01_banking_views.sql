-- TODO: Add daily summary, dormant account, and loan exposure views.
-- ==========================================================
-- PHASE 5A: ANALYTICAL SQL VIEWS (FOR REPORTING & DASHBOARD)
-- ==========================================================

USE mini_core_banking;

-- 1. Customer 360 Portfolio View (Joins Customers, KYC, Accounts, Branches)
CREATE OR REPLACE VIEW vw_customer_portfolio AS
SELECT 
    c.customer_id,
    c.customer_cif,
    c.full_name,
    c.email,
    c.phone,
    k.kyc_status,
    k.risk_category,
    a.account_id,
    a.account_number,
    t.type_name AS account_type,
    b.branch_name,
    b.city AS branch_city,
    a.balance,
    a.status AS account_status,
    a.opened_at
FROM customers c
JOIN kyc_details k ON c.customer_id = k.customer_id
JOIN accounts a ON c.customer_id = a.customer_id
JOIN account_types t ON a.type_id = t.type_id
JOIN branches b ON a.branch_id = b.branch_id;

-- 2. Branch Performance Summary View
CREATE OR REPLACE VIEW vw_branch_summary AS
SELECT 
    b.branch_id,
    b.branch_code,
    b.branch_name,
    b.city,
    COUNT(DISTINCT a.account_id) AS total_accounts,
    COUNT(DISTINCT a.customer_id) AS total_customers,
    COALESCE(SUM(a.balance), 0.00) AS total_deposits_held,
    ROUND(COALESCE(AVG(a.balance), 0.00), 2) AS avg_account_balance
FROM branches b
LEFT JOIN accounts a ON b.branch_id = a.branch_id AND a.status != 'Closed'
GROUP BY b.branch_id, b.branch_code, b.branch_name, b.city;

-- 3. Active Fraud Alerts Dashboard View
CREATE OR REPLACE VIEW vw_fraud_monitoring AS
SELECT 
    f.alert_id,
    f.created_at AS alert_time,
    f.alert_type,
    f.severity,
    f.alert_status,
    a.account_number,
    c.full_name AS customer_name,
    c.phone AS customer_phone,
    t.txn_reference,
    t.txn_type,
    t.amount AS txn_amount,
    f.description
FROM fraud_alerts f
JOIN accounts a ON f.account_id = a.account_id
JOIN customers c ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON f.transaction_id = t.transaction_id;

-- 4. Loan Exposure & Repayment Health View
CREATE OR REPLACE VIEW vw_loan_portfolio AS
SELECT 
    l.loan_id,
    l.loan_account_number,
    c.customer_cif,
    c.full_name AS borrower_name,
    l.loan_type,
    l.principal_amount,
    l.interest_rate,
    l.tenure_months,
    l.emi_amount,
    l.outstanding_balance,
    l.status AS loan_status,
    COUNT(CASE WHEN r.payment_status = 'Paid' THEN 1 END) AS emis_paid,
    COUNT(CASE WHEN r.payment_status IN ('Upcoming', 'Overdue') THEN 1 END) AS emis_remaining
FROM loans l
JOIN customers c ON l.customer_id = c.customer_id
LEFT JOIN loan_repayments r ON l.loan_id = r.loan_id
GROUP BY 
    l.loan_id, l.loan_account_number, c.customer_cif, c.full_name,
    l.loan_type, l.principal_amount, l.interest_rate, l.tenure_months,
    l.emi_amount, l.outstanding_balance, l.status;