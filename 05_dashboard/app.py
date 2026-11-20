"""Streamlit and Plotly dashboard connected to MySQL."""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

# Resolve 03_data_generator path reliably regardless of where Streamlit is launched
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "03_data_generator"))

from db_config import get_connection
st.set_page_config(
    page_title="Mini Core Banking System",
    page_icon="🏦",
    layout="wide"
)

def run_query(query, params=None):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def call_procedure(proc_name, args):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        return True, "Operation completed successfully!"
    except Exception as e:
        conn.rollback()
        msg = getattr(e, 'msg', str(e))
        return False, msg
    finally:
        cursor.close()
        conn.close()

# Sidebar Navigation
st.sidebar.title("🏦 Mini Core Banking")
st.sidebar.caption("SQL-Powered Core Banking & Risk Engine")
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Dashboard",
        "👤 Customer 360 & Statements",
        "💸 Live Banking Simulator",
        "📑 Loans & EMI Management",
        "🚨 Fraud & Audit Center"
    ]
)

# ==========================================================
# PAGE 1: EXECUTIVE DASHBOARD
# ==========================================================
if page == "📊 Executive Dashboard":
    st.title("📊 Core Banking Executive Overview")

    # Top KPI Metrics
    kpi_df = run_query("""
        SELECT 
            (SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE status = 'Active') AS total_deposits,
            (SELECT COUNT(*) FROM accounts WHERE status = 'Active') AS active_accounts,
            (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'Success') AS txn_volume,
            (SELECT COALESCE(SUM(outstanding_balance), 0) FROM loans WHERE status = 'Active') AS loan_book,
            (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Open') AS open_alerts
    """)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Active Deposits", f"₹{kpi_df['total_deposits'][0]:,.2f}")
    c2.metric("Active Accounts", f"{kpi_df['active_accounts'][0]:,}")
    c3.metric("Successful Txn Volume", f"₹{kpi_df['txn_volume'][0]:,.2f}")
    c4.metric("Active Loan Book", f"₹{kpi_df['loan_book'][0]:,.2f}")
    c5.metric("Open Fraud Alerts", f"{kpi_df['open_alerts'][0]}", delta_color="inverse")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Deposits Held by Branch")
        branch_df = run_query("SELECT branch_name, total_deposits_held, total_accounts FROM vw_branch_summary")
        fig_branch = px.bar(
            branch_df,
            x="branch_name",
            y="total_deposits_held",
            color="branch_name",
            text_auto=".2s",
            labels={"branch_name": "Branch", "total_deposits_held": "Deposits (INR)"}
        )
        fig_branch.update_layout(showlegend=False)
        st.plotly_chart(fig_branch, use_container_width=True)

    with col2:
        st.subheader("Transaction Volume by Channel")
        channel_df = run_query("""
            SELECT txn_type, COUNT(*) AS txn_count, SUM(amount) AS total_amount
            FROM transactions
            WHERE status = 'Success'
            GROUP BY txn_type
        """)
        fig_channel = px.pie(
            channel_df,
            names="txn_type",
            values="total_amount",
            hole=0.45
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    st.subheader("Recent Network Transactions")
    recent_txns = run_query("""
        SELECT txn_reference, txn_type, amount, status, failure_reason, remarks, created_at
        FROM transactions
        ORDER BY transaction_id DESC
        LIMIT 15
    """)
    st.dataframe(recent_txns, use_container_width=True)

# ==========================================================
# PAGE 2: CUSTOMER 360 & DOUBLE-ENTRY STATEMENTS
# ==========================================================
elif page == "👤 Customer 360 & Statements":
    st.title("👤 Customer 360 & Double-Entry Ledger Statement")

    portfolio_df = run_query("SELECT * FROM vw_customer_portfolio ORDER BY balance DESC")
    search_term = st.text_input("Search by Customer Name, CIF, or Account Number:")

    if search_term:
        filtered_df = portfolio_df[
            portfolio_df["full_name"].str.contains(search_term, case=False, na=False) |
            portfolio_df["customer_cif"].str.contains(search_term, case=False, na=False) |
            portfolio_df["account_number"].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_df = portfolio_df

    st.dataframe(filtered_df, use_container_width=True)

    st.divider()
    st.subheader("📒 Account Statement (Double-Entry Ledger)")

    acc_options = {
        f"{row['account_number']} — {row['full_name']} (₹{row['balance']:,.2f})": row["account_id"]
        for _, row in portfolio_df.iterrows()
    }
    selected_label = st.selectbox("Select Account to View Ledger Statement:", list(acc_options.keys()))
    selected_acc_id = acc_options[selected_label]

    ledger_df = run_query("""
        SELECT 
            te.entry_id AS 'Entry ID',
            t.txn_reference AS 'Reference',
            t.txn_type AS 'Channel',
            te.entry_type AS 'Type (DR/CR)',
            te.amount AS 'Amount (INR)',
            te.balance_after AS 'Balance After (INR)',
            t.remarks AS 'Remarks',
            te.created_at AS 'Timestamp'
        FROM transaction_entries te
        JOIN transactions t ON te.transaction_id = t.transaction_id
        WHERE te.account_id = %s
        ORDER BY te.entry_id DESC
    """, params=(selected_acc_id,))
    st.dataframe(ledger_df, use_container_width=True)

# ==========================================================
# PAGE 3: LIVE BANKING SIMULATOR (STORED PROCEDURES)
# ==========================================================
elif page == "💸 Live Banking Simulator":
    st.title("💸 Live ACID Banking Simulator")
    st.info("Every action here calls your MySQL Stored Procedures (`sp_deposit_funds`, `sp_withdraw_funds`, `sp_transfer_funds`), enforces ACID constraints, updates the Double-Entry Ledger, and runs real-time Fraud Triggers.")

    active_accs = run_query("""
        SELECT a.account_id, a.account_number, c.full_name, a.balance
        FROM accounts a JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.status = 'Active'
        ORDER BY a.account_id
    """)
    acc_map = {
        f"[{r['account_id']}] {r['account_number']} — {r['full_name']} (₹{r['balance']:,.2f})": r["account_id"]
        for _, r in active_accs.iterrows()
    }

    tab1, tab2, tab3 = st.tabs(["🔄 Fund Transfer (UPI / NEFT / IMPS)", "➕ Cash Deposit", "➖ Cash Withdrawal"])

    with tab1:
        with st.form("transfer_form"):
            src_label = st.selectbox("From Account (Debit)", list(acc_map.keys()), index=0)
            dest_label = st.selectbox("To Account (Credit)", list(acc_map.keys()), index=1)
            channel = st.selectbox("Payment Channel", ["UPI", "NEFT", "IMPS", "Internal_Transfer"])
            amount = st.number_input("Transfer Amount (INR) — Tip: Enter >= 100000 to test Fraud Alert Trigger!", min_value=1.0, value=5000.0, step=500.0)
            remarks = st.text_input("Remarks", value="Live Dashboard Transfer")
            submitted = st.form_submit_button("Execute ACID Transfer")

            if submitted:
                ok, msg = call_procedure("sp_transfer_funds", [acc_map[src_label], acc_map[dest_label], float(amount), channel, remarks])
                if ok:
                    st.success(f"✅ {msg} Double-entry Debit & Credit recorded.")
                else:
                    st.error(f"❌ Transaction Blocked & Rolled Back: {msg}")

    with tab2:
        with st.form("deposit_form"):
            dep_label = st.selectbox("Target Account", list(acc_map.keys()))
            dep_amt = st.number_input("Deposit Amount (INR)", min_value=1.0, value=10000.0, step=1000.0)
            dep_rem = st.text_input("Deposit Remarks", value="Branch Cash Deposit")
            if st.form_submit_button("Deposit Funds"):
                ok, msg = call_procedure("sp_deposit_funds", [acc_map[dep_label], float(dep_amt), dep_rem])
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

    with tab3:
        with st.form("withdraw_form"):
            wdr_label = st.selectbox("Account to Debit", list(acc_map.keys()))
            wdr_amt = st.number_input("Withdrawal Amount (INR)", min_value=1.0, value=2000.0, step=500.0)
            wdr_rem = st.text_input("Withdrawal Remarks", value="ATM Cash Withdrawal")
            if st.form_submit_button("Withdraw Funds"):
                ok, msg = call_procedure("sp_withdraw_funds", [acc_map[wdr_label], float(wdr_amt), wdr_rem])
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

# ==========================================================
# PAGE 4: LOANS & EMI MANAGEMENT
# ==========================================================
elif page == "📑 Loans & EMI Management":
    st.title("📑 Loans & EMI Repayment Management")

    loans_df = run_query("SELECT * FROM vw_loan_portfolio ORDER BY loan_id")
    st.dataframe(loans_df, use_container_width=True)

    st.divider()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Pay Next Monthly EMI")
        active_loans = loans_df[loans_df["loan_status"] == "Active"]
        if not active_loans.empty:
            loan_choices = {
                f"{r['loan_account_number']} — {r['borrower_name']} (EMI: ₹{r['emi_amount']:,.2f})": r["loan_id"]
                for _, r in active_loans.iterrows()
            }
            sel_loan = st.selectbox("Select Active Loan:", list(loan_choices.keys()))
            sel_loan_id = loan_choices[sel_loan]

            if st.button("Deduct & Pay Next EMI"):
                ok, msg = call_procedure("sp_pay_loan_emi", [sel_loan_id])
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        else:
            st.info("No active loans found.")

    with col2:
        if not active_loans.empty:
            st.subheader("EMI Amortization Schedule")
            sched_df = run_query("""
                SELECT installment_number, due_date, emi_due, principal_component, interest_component, payment_status, paid_at
                FROM loan_repayments
                WHERE loan_id = %s
                ORDER BY installment_number
            """, params=(sel_loan_id,))
            st.dataframe(sched_df, use_container_width=True)

# ==========================================================
# PAGE 5: FRAUD MONITORING & AUDIT LOGS
# ==========================================================
elif page == "🚨 Fraud & Audit Center":
    st.title("🚨 Real-Time Fraud Detection & Database Audit Trail")

    tab_f, tab_a = st.tabs(["🚨 Automated Fraud Alerts", "📜 System Audit Logs"])

    with tab_f:
        fraud_df = run_query("SELECT * FROM vw_fraud_monitoring ORDER BY alert_id DESC")
        st.dataframe(fraud_df, use_container_width=True)

        open_alerts = fraud_df[fraud_df["alert_status"] == "Open"]
        if not open_alerts.empty:
            st.subheader("Compliance Officer Action")
            alert_id = st.selectbox("Select Open Alert ID to Review:", open_alerts["alert_id"].tolist())
            new_status = st.selectbox("Update Alert Status:", ["Resolved_Safe", "Confirmed_Fraud", "Under_Review"])
            if st.button("Update Alert Status"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE fraud_alerts SET alert_status = %s, reviewed_by = 4, resolved_at = NOW() WHERE alert_id = %s",
                    (new_status, int(alert_id))
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Alert #{alert_id} marked as {new_status}.")
                st.rerun()

    with tab_a:
        audit_df = run_query("SELECT * FROM audit_logs ORDER BY audit_id DESC LIMIT 50")
        st.dataframe(audit_df, use_container_width=True)