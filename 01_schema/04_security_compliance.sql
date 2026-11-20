-- TODO: Create roles, employees, audit_logs, fraud_alerts, and complaints.
-- ==========================================================
-- PHASE 3B: EMPLOYEES, ROLES, AUDIT LOGS, FRAUD & COMPLAINTS (TABLES 12 - 16)
-- ==========================================================

USE mini_core_banking;

DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS fraud_alerts;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS roles;

-- 12. Roles Table (Role-Based Access Control)
CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name ENUM('Admin', 'Branch_Manager', 'Teller', 'Compliance_Officer') NOT NULL UNIQUE,
    can_approve_loans BOOLEAN DEFAULT FALSE,
    can_freeze_accounts BOOLEAN DEFAULT FALSE,
    can_reverse_txns BOOLEAN DEFAULT FALSE,
    max_approval_limit DECIMAL(15, 2) NOT NULL DEFAULT 50000.00
);

-- 13. Employees Table
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_code VARCHAR(15) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    branch_id INT NOT NULL,
    role_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    hired_at DATE NOT NULL,
    
    CONSTRAINT fk_emp_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id),
    CONSTRAINT fk_emp_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- 14. Audit Logs Table (Tracks sensitive account, KYC & employee changes)
CREATE TABLE audit_logs (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    action_type ENUM('INSERT', 'UPDATE', 'DELETE', 'APPROVAL', 'REVERSAL') NOT NULL,
    old_value TEXT NULL,
    new_value TEXT NULL,
    performed_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM_TRIGGER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Fraud Alerts Table (Automated risk & suspicious activity monitoring)
CREATE TABLE fraud_alerts (
    alert_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_id BIGINT NULL,
    alert_type ENUM('High_Value_Txn', 'Rapid_Velocity', 'Repeated_Failures', 'Dormant_Activity') NOT NULL,
    severity ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    description TEXT NOT NULL,
    alert_status ENUM('Open', 'Under_Review', 'Resolved_Safe', 'Confirmed_Fraud') DEFAULT 'Open',
    reviewed_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    CONSTRAINT fk_fraud_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_fraud_txn FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    CONSTRAINT fk_fraud_emp FOREIGN KEY (reviewed_by) REFERENCES employees(employee_id)
);

-- 16. Customer Complaints Table
CREATE TABLE complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(20) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    transaction_id BIGINT NULL,
    category ENUM('Failed_Transaction', 'Unauthorized_Debit', 'Card_Issue', 'Loan_Query', 'KYC_Delay') NOT NULL,
    description TEXT NOT NULL,
    status ENUM('Open', 'In_Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    assigned_to INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    CONSTRAINT fk_comp_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_comp_txn FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    CONSTRAINT fk_comp_emp FOREIGN KEY (assigned_to) REFERENCES employees(employee_id)
);

CREATE INDEX idx_audit_table_time ON audit_logs(table_name, created_at);
CREATE INDEX idx_fraud_status ON fraud_alerts(alert_status, severity);