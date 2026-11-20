-- TODO: Add audit trails for balance and KYC changes.
-- ==========================================================
-- PHASE 4C: AUTOMATED AUDIT TRAIL TRIGGERS
-- ==========================================================

USE mini_core_banking;

DROP TRIGGER IF EXISTS trg_audit_account_status;
DROP TRIGGER IF EXISTS trg_audit_kyc_update;
DROP TRIGGER IF EXISTS trg_audit_loan_status;

DELIMITER $$

-- 1. Log any Account Status Change (Active -> Frozen/Dormant/Closed)
CREATE TRIGGER trg_audit_account_status
AFTER UPDATE ON accounts
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (table_name, record_id, action_type, old_value, new_value, performed_by)
        VALUES (
            'accounts',
            NEW.account_id,
            'UPDATE',
            CONCAT('status=', OLD.status),
            CONCAT('status=', NEW.status),
            CURRENT_USER()
        );
    END IF;
END$$

-- 2. Log KYC Verification / Risk Category Changes
CREATE TRIGGER trg_audit_kyc_update
AFTER UPDATE ON kyc_details
FOR EACH ROW
BEGIN
    IF OLD.kyc_status != NEW.kyc_status OR OLD.risk_category != NEW.risk_category THEN
        INSERT INTO audit_logs (table_name, record_id, action_type, old_value, new_value, performed_by)
        VALUES (
            'kyc_details',
            NEW.kyc_id,
            'UPDATE',
            CONCAT('status=', OLD.kyc_status, ', risk=', OLD.risk_category),
            CONCAT('status=', NEW.kyc_status, ', risk=', NEW.risk_category),
            CURRENT_USER()
        );
    END IF;
END$$

-- 3. Log Loan Approval / Rejection / Default
CREATE TRIGGER trg_audit_loan_status
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs (table_name, record_id, action_type, old_value, new_value, performed_by)
        VALUES (
            'loans',
            NEW.loan_id,
            'APPROVAL',
            CONCAT('status=', OLD.status),
            CONCAT('status=', NEW.status),
            CURRENT_USER()
        );
    END IF;
END$$

DELIMITER ;