-- TODO: Add velocity, high-value, and failed-attempt fraud alerts.
-- ==========================================================
-- PHASE 4D: REAL-TIME FRAUD & RISK MONITORING TRIGGERS
-- ==========================================================

USE mini_core_banking;

DROP TRIGGER IF EXISTS trg_fraud_monitor_transactions;

DELIMITER $$

CREATE TRIGGER trg_fraud_monitor_transactions
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_recent_txn_count INT DEFAULT 0;
    DECLARE v_recent_fail_count INT DEFAULT 0;

    -- Rule 1: High-Value Single Outgoing Transaction (>= 1,00,000 INR)
    IF NEW.source_account_id IS NOT NULL AND NEW.status = 'Success' AND NEW.amount >= 100000.00 THEN
        INSERT INTO fraud_alerts (account_id, transaction_id, alert_type, severity, description)
        VALUES (
            NEW.source_account_id,
            NEW.transaction_id,
            'High_Value_Txn',
            'High',
            CONCAT('High-value outgoing transaction of INR ', NEW.amount, ' via ', NEW.txn_type)
        );
    END IF;

    -- Rule 2: Rapid Velocity Check (3 or more successful outgoing txns within 10 minutes)
    IF NEW.source_account_id IS NOT NULL AND NEW.status = 'Success' THEN
        SELECT COUNT(*) INTO v_recent_txn_count
        FROM transactions
        WHERE source_account_id = NEW.source_account_id
          AND status = 'Success'
          AND created_at >= DATE_SUB(NEW.created_at, INTERVAL 10 MINUTE);

        IF v_recent_txn_count >= 3 THEN
            INSERT INTO fraud_alerts (account_id, transaction_id, alert_type, severity, description)
            VALUES (
                NEW.source_account_id,
                NEW.transaction_id,
                'Rapid_Velocity',
                'Critical',
                CONCAT('Rapid velocity detected: ', v_recent_txn_count, ' outgoing transactions within 10 minutes.')
            );
        END IF;
    END IF;

    -- Rule 3: Repeated Failed Attempts (3 or more failed txns within 15 minutes)
    IF NEW.source_account_id IS NOT NULL AND NEW.status = 'Failed' THEN
        SELECT COUNT(*) INTO v_recent_fail_count
        FROM transactions
        WHERE source_account_id = NEW.source_account_id
          AND status = 'Failed'
          AND created_at >= DATE_SUB(NEW.created_at, INTERVAL 15 MINUTE);

        IF v_recent_fail_count >= 3 THEN
            INSERT INTO fraud_alerts (account_id, transaction_id, alert_type, severity, description)
            VALUES (
                NEW.source_account_id,
                NEW.transaction_id,
                'Repeated_Failures',
                'High',
                CONCAT('Suspicious activity: ', v_recent_fail_count, ' consecutive failed transactions in 15 minutes.')
            );
        END IF;
    END IF;
END$$

DELIMITER ;