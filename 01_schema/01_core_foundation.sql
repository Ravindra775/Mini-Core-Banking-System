-- TODO: Create branches, customers, KYC, account_types, and accounts.
-- ==========================================================
-- PHASE 1: MINI CORE BANKING SYSTEM - DATABASE FOUNDATION
-- ==========================================================

-- 1. Create and select the database
DROP DATABASE IF EXISTS mini_core_banking;
CREATE DATABASE mini_core_banking;
USE mini_core_banking;

-- 2. Branches Table
CREATE TABLE branches (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_code VARCHAR(10) NOT NULL UNIQUE,
    branch_name VARCHAR(100) NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL UNIQUE,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Customers Table
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_cif VARCHAR(15) NOT NULL UNIQUE, -- Customer Information File ID
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    nominee_name VARCHAR(100) NOT NULL,
    nominee_relation VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. KYC Details Table (1-to-1 with Customers)
CREATE TABLE kyc_details (
    kyc_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL UNIQUE,
    masked_pan VARCHAR(10) NOT NULL UNIQUE,     -- Format: ABCDE****F
    masked_gov_id VARCHAR(14) NOT NULL UNIQUE,  -- Format: GOV-ID-123456
    kyc_status ENUM('Pending', 'Verified', 'Rejected') DEFAULT 'Pending',
    risk_category ENUM('Low', 'Medium', 'High') DEFAULT 'Low',
    verified_at TIMESTAMP NULL,
    CONSTRAINT fk_kyc_customer FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 5. Account Types Table (Master rules for Savings/Current)
CREATE TABLE account_types (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name ENUM('Savings', 'Current', 'Salary') NOT NULL UNIQUE,
    min_balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    interest_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    daily_txn_limit DECIMAL(12, 2) NOT NULL DEFAULT 100000.00
);

-- 6. Accounts Table
CREATE TABLE accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(16) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    branch_id INT NOT NULL,
    type_id INT NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    status ENUM('Active', 'Frozen', 'Dormant', 'Closed') DEFAULT 'Active',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL,
    
    -- Data Integrity Rules
    CONSTRAINT chk_non_negative_balance CHECK (balance >= 0.00),
    CONSTRAINT fk_acc_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_acc_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id),
    CONSTRAINT fk_acc_type FOREIGN KEY (type_id) REFERENCES account_types(type_id)
);

-- Index for fast account lookups by customer
CREATE INDEX idx_customer_accounts ON accounts(customer_id);