-- TODO: Add EMI calculation and loan disbursement procedures.
-- ==========================================================
-- PHASE 4B: LOAN APPROVAL & EMI SCHEDULE GENERATOR
-- ==========================================================

USE mini_core_banking;

DROP PROCEDURE IF EXISTS sp_approve_and_disburse_loan;
DROP PROCEDURE IF EXISTS sp_pay_loan_emi;

DELIMITER $$

-- 1. APPROVE LOAN, DISBURSE PRINCIPAL & GENERATE EMI SCHEDULE
CREATE PROCEDURE sp_approve_and_disburse_loan(
    IN p_loan_id INT
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_acc_id INT;
    DECLARE v_principal DECIMAL(15, 2);
    DECLARE v_rate DECIMAL(5, 2);
    DECLARE v_months INT;
    DECLARE v_monthly_rate DECIMAL(10, 8);
    DECLARE v_emi DECIMAL(12, 2);
    DECLARE v_bal DECIMAL(15, 2);
    DECLARE v_interest_comp DECIMAL(12, 2);
    DECLARE v_principal_comp DECIMAL(12, 2);
    DECLARE v_new_acc_bal DECIMAL(15, 2);
    DECLARE v_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);
    DECLARE i INT DEFAULT 1;

    START TRANSACTION;

    SELECT status, linked_account_id, principal_amount, interest_rate, tenure_months
    INTO v_status, v_acc_id, v_principal, v_rate, v_months
    FROM loans WHERE loan_id = p_loan_id FOR UPDATE;

    IF v_status != 'Pending' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only Pending loans can be approved.';
    END IF;

    -- Reducing Balance EMI Formula: P * r * (1+r)^n / ((1+r)^n - 1)
    SET v_monthly_rate = (v_rate / 12) / 100;
    SET v_emi = ROUND((v_principal * v_monthly_rate * POW(1 + v_monthly_rate, v_months)) / (POW(1 + v_monthly_rate, v_months) - 1), 2);

    -- Update Loan Record
    UPDATE loans
    SET status = 'Active',
        emi_amount = v_emi,
        outstanding_balance = v_principal,
        approved_at = NOW()
    WHERE loan_id = p_loan_id;

    -- Disburse Principal into Linked Bank Account
    UPDATE accounts SET balance = balance + v_principal WHERE account_id = v_acc_id;
    SELECT balance INTO v_new_acc_bal FROM accounts WHERE account_id = v_acc_id;

    SET v_ref = CONCAT('LN', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));
    INSERT INTO transactions (txn_reference, destination_account_id, txn_type, amount, status, remarks)
    VALUES (v_ref, v_acc_id, 'Deposit', v_principal, 'Success', CONCAT('Loan Disbursement #', p_loan_id));
    SET v_txn_id = LAST_INSERT_ID();

    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, v_acc_id, 'CREDIT', v_principal, v_new_acc_bal);

    -- Generate Monthly EMI Schedule
    SET v_bal = v_principal;
    WHILE i <= v_months DO
        SET v_interest_comp = ROUND(v_bal * v_monthly_rate, 2);
        IF i = v_months THEN
            SET v_principal_comp = v_bal;
            SET v_emi = v_principal_comp + v_interest_comp;
        ELSE
            SET v_principal_comp = v_emi - v_interest_comp;
        END IF;

        INSERT INTO loan_repayments (loan_id, installment_number, due_date, emi_due, principal_component, interest_component)
        VALUES (p_loan_id, i, DATE_ADD(CURDATE(), INTERVAL i MONTH), v_emi, v_principal_comp, v_interest_comp);

        SET v_bal = v_bal - v_principal_comp;
        SET i = i + 1;
    END WHILE;

    COMMIT;
END$$

-- 2. PAY NEXT UPCOMING LOAN EMI
CREATE PROCEDURE sp_pay_loan_emi(
    IN p_loan_id INT
)
BEGIN
    DECLARE v_repay_id BIGINT;
    DECLARE v_emi_due DECIMAL(12, 2);
    DECLARE v_prin_comp DECIMAL(12, 2);
    DECLARE v_acc_id INT;
    DECLARE v_acc_bal DECIMAL(15, 2);
    DECLARE v_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);

    START TRANSACTION;

    SELECT r.repayment_id, r.emi_due, r.principal_component, l.linked_account_id
    INTO v_repay_id, v_emi_due, v_prin_comp, v_acc_id
    FROM loan_repayments r
    JOIN loans l ON r.loan_id = l.loan_id
    WHERE r.loan_id = p_loan_id AND r.payment_status IN ('Upcoming', 'Overdue')
    ORDER BY r.installment_number ASC
    LIMIT 1 FOR UPDATE;

    IF v_repay_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No pending EMI installments found for this loan.';
    END IF;

    SELECT balance INTO v_acc_bal FROM accounts WHERE account_id = v_acc_id FOR UPDATE;
    IF v_acc_bal < v_emi_due THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient account balance to pay EMI.';
    END IF;

    -- Deduct EMI from linked account
    UPDATE accounts SET balance = balance - v_emi_due WHERE account_id = v_acc_id;

    SET v_ref = CONCAT('EMI', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));
    INSERT INTO transactions (txn_reference, source_account_id, txn_type, amount, status, remarks)
    VALUES (v_ref, v_acc_id, 'Loan_EMI', v_emi_due, 'Success', CONCAT('EMI Payment for Loan #', p_loan_id));
    SET v_txn_id = LAST_INSERT_ID();

    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, v_acc_id, 'DEBIT', v_emi_due, v_acc_bal - v_emi_due);

    -- Mark EMI Paid & Reduce Outstanding Principal
    UPDATE loan_repayments
    SET payment_status = 'Paid', amount_paid = v_emi_due, paid_at = NOW(), transaction_id = v_txn_id
    WHERE repayment_id = v_repay_id;

    UPDATE loans
    SET outstanding_balance = GREATEST(0, outstanding_balance - v_prin_comp),
        status = IF(outstanding_balance - v_prin_comp <= 0, 'Closed', 'Active')
    WHERE loan_id = p_loan_id;

    COMMIT;
END$$

DELIMITER ;