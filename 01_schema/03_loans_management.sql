-- TODO: Create loans and loan_repayments, including EMI schedules.
-- ==========================================================
-- PHASE 3A: LOANS & EMI REPAYMENT SCHEDULES (TABLES 10 - 11)
-- ==========================================================

USE mini_core_banking;

DROP TABLE IF EXISTS loan_repayments;
DROP TABLE IF EXISTS loans;

-- 10. Loans Table
CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_account_number VARCHAR(16) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    linked_account_id INT NOT NULL,                 -- Account where loan is disbursed & EMI is deducted
    loan_type ENUM('Personal', 'Education', 'Home', 'Vehicle') NOT NULL,
    principal_amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,           -- Annual interest rate %
    tenure_months INT NOT NULL,
    emi_amount DECIMAL(12, 2) NOT NULL,
    outstanding_balance DECIMAL(15, 2) NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Active', 'Closed', 'Defaulted') DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    
    CONSTRAINT chk_positive_principal CHECK (principal_amount > 0.00),
    CONSTRAINT fk_loan_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_loan_account FOREIGN KEY (linked_account_id) REFERENCES accounts(account_id)
);

-- 11. Loan Repayments Table (EMI Schedule & Late Fee Tracking)
CREATE TABLE loan_repayments (
    repayment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    installment_number INT NOT NULL,
    due_date DATE NOT NULL,
    emi_due DECIMAL(12, 2) NOT NULL,
    principal_component DECIMAL(12, 2) NOT NULL,
    interest_component DECIMAL(12, 2) NOT NULL,
    late_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount_paid DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('Upcoming', 'Paid', 'Overdue', 'Partially_Paid') DEFAULT 'Upcoming',
    paid_at TIMESTAMP NULL,
    transaction_id BIGINT NULL,
    
    CONSTRAINT uq_loan_installment UNIQUE (loan_id, installment_number),
    CONSTRAINT fk_repay_loan FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE,
    CONSTRAINT fk_repay_txn FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

CREATE INDEX idx_loan_customer ON loans(customer_id);
CREATE INDEX idx_repay_due_status ON loan_repayments(due_date, payment_status);