-- ==========================================================
-- PHASE 2: TRANSACTIONS, DOUBLE-ENTRY LEDGER, BENEFICIARIES & CARDS
-- ==========================================================

USE mini_core_banking;

-- Drop in reverse dependency order so the script can be re-run safely
DROP TABLE IF EXISTS transaction_entries;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS cards;
DROP TABLE IF EXISTS beneficiaries;

-- 1. Beneficiaries Table (Saved recipients for fund transfers)
CREATE TABLE beneficiaries (
    beneficiary_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    beneficiary_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(16) NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL,
    bank_name VARCHAR(100) NOT NULL DEFAULT 'Mini Core Bank',
    max_transfer_limit DECIMAL(12, 2) NOT NULL DEFAULT 50000.00,
    is_verified BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_cust_beneficiary UNIQUE (customer_id, account_number),
    CONSTRAINT fk_ben_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 2. Debit Cards Table
CREATE TABLE cards (
    card_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    masked_card_number VARCHAR(19) NOT NULL UNIQUE, -- Format: XXXX-XXXX-XXXX-1234
    card_type ENUM('RuPay Classic', 'Visa Platinum', 'Mastercard Gold') DEFAULT 'RuPay Classic',
    expiry_date DATE NOT NULL,
    daily_atm_limit DECIMAL(10, 2) NOT NULL DEFAULT 25000.00,
    daily_pos_limit DECIMAL(10, 2) NOT NULL DEFAULT 100000.00,
    card_status ENUM('Active', 'Blocked', 'Expired') DEFAULT 'Active',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_card_account FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

-- 3. Transactions Table (Master log of every financial event)
CREATE TABLE transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    txn_reference VARCHAR(30) NOT NULL UNIQUE,      -- e.g., TXN2026112000001
    source_account_id INT NULL,                     -- NULL for cash deposits
    destination_account_id INT NULL,                -- NULL for cash withdrawals
    txn_type ENUM('Deposit', 'Withdrawal', 'Internal_Transfer', 'UPI', 'NEFT', 'IMPS', 'Reversal', 'Loan_EMI') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status ENUM('Success', 'Failed', 'Pending', 'Reversed') DEFAULT 'Pending',
    failure_reason VARCHAR(255) NULL,
    original_txn_id BIGINT NULL,                    -- Links to original transaction if this is a Reversal
    remarks VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_positive_txn_amount CHECK (amount > 0.00),
    CONSTRAINT fk_txn_source FOREIGN KEY (source_account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_txn_dest FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_txn_reversal FOREIGN KEY (original_txn_id) REFERENCES transactions(transaction_id)
);

-- 4. Transaction Entries Table (Double-Entry Accounting Ledger)
CREATE TABLE transaction_entries (
    entry_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    account_id INT NOT NULL,
    entry_type ENUM('DEBIT', 'CREDIT') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    balance_after DECIMAL(15, 2) NOT NULL,          -- Running balance snapshot for statements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_positive_entry_amount CHECK (amount > 0.00),
    CONSTRAINT fk_entry_txn FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    CONSTRAINT fk_entry_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Indexes for fast statement generation & fraud velocity checks
CREATE INDEX idx_txn_source_time ON transactions(source_account_id, created_at);
CREATE INDEX idx_txn_status ON transactions(status);
CREATE INDEX idx_ledger_account_time ON transaction_entries(account_id, created_at);