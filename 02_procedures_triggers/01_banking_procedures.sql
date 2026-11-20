-- TODO: Add deposit, withdrawal, ACID transfer, and reversal procedures.
-- ==========================================================
-- PHASE 4A: CORE BANKING STORED PROCEDURES (ACID & DOUBLE-ENTRY)
-- ==========================================================

USE mini_core_banking;

DROP PROCEDURE IF EXISTS sp_deposit_funds;
DROP PROCEDURE IF EXISTS sp_withdraw_funds;
DROP PROCEDURE IF EXISTS sp_transfer_funds;
DROP PROCEDURE IF EXISTS sp_reverse_transaction;

DELIMITER $$

-- 1. DEPOSIT FUNDS PROCEDURE
CREATE PROCEDURE sp_deposit_funds(
    IN p_account_id INT,
    IN p_amount DECIMAL(15, 2),
    IN p_remarks VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_new_balance DECIMAL(15, 2);
    DECLARE v_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Deposit amount must be greater than zero.';
    END IF;

    START TRANSACTION;

    -- Lock the account row
    SELECT status INTO v_status FROM accounts WHERE account_id = p_account_id FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Account does not exist.';
    ELSEIF v_status != 'Active' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Deposit failed: Account is not Active.';
    END IF;

    -- Update balance
    UPDATE accounts SET balance = balance + p_amount WHERE account_id = p_account_id;
    SELECT balance INTO v_new_balance FROM accounts WHERE account_id = p_account_id;

    -- Generate unique reference
    SET v_ref = CONCAT('DEP', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));

    -- Record master transaction
    INSERT INTO transactions (txn_reference, destination_account_id, txn_type, amount, status, remarks)
    VALUES (v_ref, p_account_id, 'Deposit', p_amount, 'Success', p_remarks);
    SET v_txn_id = LAST_INSERT_ID();

    -- Record Double-Entry Credit Ledger
    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, p_account_id, 'CREDIT', p_amount, v_new_balance);

    COMMIT;
END$$

-- 2. WITHDRAW FUNDS PROCEDURE (Logs failed attempts if balance is insufficient)
CREATE PROCEDURE sp_withdraw_funds(
    IN p_account_id INT,
    IN p_amount DECIMAL(15, 2),
    IN p_remarks VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_balance DECIMAL(15, 2);
    DECLARE v_min_bal DECIMAL(12, 2);
    DECLARE v_new_balance DECIMAL(15, 2);
    DECLARE v_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);

    IF p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Withdrawal amount must be greater than zero.';
    END IF;

    SET v_ref = CONCAT('WDR', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));

    START TRANSACTION;

    SELECT a.status, a.balance, t.min_balance
    INTO v_status, v_balance, v_min_bal
    FROM accounts a
    JOIN account_types t ON a.type_id = t.type_id
    WHERE a.account_id = p_account_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Account does not exist.';
    ELSEIF v_status != 'Active' THEN
        INSERT INTO transactions (txn_reference, source_account_id, txn_type, amount, status, failure_reason, remarks)
        VALUES (v_ref, p_account_id, 'Withdrawal', p_amount, 'Failed', CONCAT('Account status is ', v_status), p_remarks);
        COMMIT;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Withdrawal failed: Account is Frozen, Dormant, or Closed.';
    ELSEIF (v_balance - p_amount) < v_min_bal THEN
        INSERT INTO transactions (txn_reference, source_account_id, txn_type, amount, status, failure_reason, remarks)
        VALUES (v_ref, p_account_id, 'Withdrawal', p_amount, 'Failed', 'Insufficient funds / Minimum balance breach', p_remarks);
        COMMIT;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Withdrawal failed: Insufficient funds or minimum balance breach.';
    END IF;

    -- Deduct balance
    UPDATE accounts SET balance = balance - p_amount WHERE account_id = p_account_id;
    SET v_new_balance = v_balance - p_amount;

    -- Record master transaction
    INSERT INTO transactions (txn_reference, source_account_id, txn_type, amount, status, remarks)
    VALUES (v_ref, p_account_id, 'Withdrawal', p_amount, 'Success', p_remarks);
    SET v_txn_id = LAST_INSERT_ID();

    -- Record Double-Entry Debit Ledger
    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, p_account_id, 'DEBIT', p_amount, v_new_balance);

    COMMIT;
END$$

-- 3. ACID FUND TRANSFER PROCEDURE (Double-Entry Debit + Credit)
CREATE PROCEDURE sp_transfer_funds(
    IN p_source_id INT,
    IN p_dest_id INT,
    IN p_amount DECIMAL(15, 2),
    IN p_channel ENUM('Internal_Transfer', 'UPI', 'NEFT', 'IMPS'),
    IN p_remarks VARCHAR(255)
)
BEGIN
    DECLARE v_src_status VARCHAR(20);
    DECLARE v_dest_status VARCHAR(20);
    DECLARE v_src_balance DECIMAL(15, 2);
    DECLARE v_dest_balance DECIMAL(15, 2);
    DECLARE v_min_bal DECIMAL(12, 2);
    DECLARE v_daily_limit DECIMAL(12, 2);
    DECLARE v_today_spent DECIMAL(15, 2);
    DECLARE v_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);

    IF p_source_id = p_dest_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Source and destination accounts cannot be the same.';
    END IF;

    IF p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transfer amount must be greater than zero.';
    END IF;

    SET v_ref = CONCAT('TRF', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));

    START TRANSACTION;

    -- Lock both accounts in consistent ID order to prevent deadlocks
    IF p_source_id < p_dest_id THEN
        SELECT a.status, a.balance, t.min_balance, t.daily_txn_limit
        INTO v_src_status, v_src_balance, v_min_bal, v_daily_limit
        FROM accounts a JOIN account_types t ON a.type_id = t.type_id
        WHERE a.account_id = p_source_id FOR UPDATE;

        SELECT status, balance INTO v_dest_status, v_dest_balance
        FROM accounts WHERE account_id = p_dest_id FOR UPDATE;
    ELSE
        SELECT status, balance INTO v_dest_status, v_dest_balance
        FROM accounts WHERE account_id = p_dest_id FOR UPDATE;

        SELECT a.status, a.balance, t.min_balance, t.daily_txn_limit
        INTO v_src_status, v_src_balance, v_min_bal, v_daily_limit
        FROM accounts a JOIN account_types t ON a.type_id = t.type_id
        WHERE a.account_id = p_source_id FOR UPDATE;
    END IF;

    -- Calculate today's total outgoing successful transfers
    SELECT COALESCE(SUM(amount), 0.00) INTO v_today_spent
    FROM transactions
    WHERE source_account_id = p_source_id
      AND status = 'Success'
      AND DATE(created_at) = CURDATE();

    -- Validation Checks (Log Failed Attempt & Commit Failure Record)
    IF v_src_status IS NULL OR v_dest_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid source or destination account.';
    ELSEIF v_src_status != 'Active' OR v_dest_status != 'Active' THEN
        INSERT INTO transactions (txn_reference, source_account_id, destination_account_id, txn_type, amount, status, failure_reason, remarks)
        VALUES (v_ref, p_source_id, p_dest_id, p_channel, p_amount, 'Failed', 'One or both accounts inactive', p_remarks);
        COMMIT;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transfer failed: Source or destination account is not Active.';
    ELSEIF (v_src_balance - p_amount) < v_min_bal THEN
        INSERT INTO transactions (txn_reference, source_account_id, destination_account_id, txn_type, amount, status, failure_reason, remarks)
        VALUES (v_ref, p_source_id, p_dest_id, p_channel, p_amount, 'Failed', 'Insufficient balance', p_remarks);
        COMMIT;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transfer failed: Insufficient balance.';
    ELSEIF (v_today_spent + p_amount) > v_daily_limit THEN
        INSERT INTO transactions (txn_reference, source_account_id, destination_account_id, txn_type, amount, status, failure_reason, remarks)
        VALUES (v_ref, p_source_id, p_dest_id, p_channel, p_amount, 'Failed', 'Daily transaction limit exceeded', p_remarks);
        COMMIT;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transfer failed: Daily transaction limit exceeded.';
    END IF;

    -- Execute Balance Updates
    UPDATE accounts SET balance = balance - p_amount WHERE account_id = p_source_id;
    UPDATE accounts SET balance = balance + p_amount WHERE account_id = p_dest_id;

    -- Insert Master Transaction
    INSERT INTO transactions (txn_reference, source_account_id, destination_account_id, txn_type, amount, status, remarks)
    VALUES (v_ref, p_source_id, p_dest_id, p_channel, p_amount, 'Success', p_remarks);
    SET v_txn_id = LAST_INSERT_ID();

    -- Insert Balanced Double-Entry Ledger Rows (DEBIT = CREDIT)
    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, p_source_id, 'DEBIT', p_amount, v_src_balance - p_amount);

    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_txn_id, p_dest_id, 'CREDIT', p_amount, v_dest_balance + p_amount);

    COMMIT;
END$$

-- 4. TRANSACTION REVERSAL PROCEDURE (Never deletes original record)
CREATE PROCEDURE sp_reverse_transaction(
    IN p_original_txn_id BIGINT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE v_src_id INT;
    DECLARE v_dest_id INT;
    DECLARE v_amount DECIMAL(15, 2);
    DECLARE v_status VARCHAR(20);
    DECLARE v_txn_type VARCHAR(30);
    DECLARE v_src_bal DECIMAL(15, 2);
    DECLARE v_dest_bal DECIMAL(15, 2);
    DECLARE v_rev_txn_id BIGINT;
    DECLARE v_ref VARCHAR(30);

    START TRANSACTION;

    SELECT source_account_id, destination_account_id, amount, status, txn_type
    INTO v_src_id, v_dest_id, v_amount, v_status, v_txn_type
    FROM transactions WHERE transaction_id = p_original_txn_id FOR UPDATE;

    IF v_status != 'Success' OR v_src_id IS NULL OR v_dest_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only completed account-to-account transfers can be reversed.';
    END IF;

    SELECT balance INTO v_dest_bal FROM accounts WHERE account_id = v_dest_id FOR UPDATE;
    SELECT balance INTO v_src_bal FROM accounts WHERE account_id = v_src_id FOR UPDATE;

    IF v_dest_bal < v_amount THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Reversal failed: Recipient has insufficient balance to return funds.';
    END IF;

    -- Reverse balances
    UPDATE accounts SET balance = balance - v_amount WHERE account_id = v_dest_id;
    UPDATE accounts SET balance = balance + v_amount WHERE account_id = v_src_id;

    -- Mark original transaction as Reversed
    UPDATE transactions SET status = 'Reversed' WHERE transaction_id = p_original_txn_id;

    -- Insert new Reversal Transaction linked to original
    SET v_ref = CONCAT('REV', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(FLOOR(RAND() * 9999), 4, '0'));
    INSERT INTO transactions (txn_reference, source_account_id, destination_account_id, txn_type, amount, status, original_txn_id, remarks)
    VALUES (v_ref, v_dest_id, v_src_id, 'Reversal', v_amount, 'Success', p_original_txn_id, p_reason);
    SET v_rev_txn_id = LAST_INSERT_ID();

    -- Double-entry reversal ledger
    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_rev_txn_id, v_dest_id, 'DEBIT', v_amount, v_dest_bal - v_amount);

    INSERT INTO transaction_entries (transaction_id, account_id, entry_type, amount, balance_after)
    VALUES (v_rev_txn_id, v_src_id, 'CREDIT', v_amount, v_src_bal + v_amount);

    COMMIT;
END$$

DELIMITER ;