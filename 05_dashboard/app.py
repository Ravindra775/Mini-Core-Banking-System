import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import mysql.connector

st.set_page_config(
    page_title="CoreBank Pro — Fintech Engine",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# CUSTOM FINTECH CSS (DARK OBSIDIAN + CORAL ORANGE THEME)
# ==========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main & Sidebar Backgrounds */
.stApp {
    background-color: #0E0E10;
    color: #F4F4F5;
}
section[data-testid="stSidebar"] {
    background-color: #131316;
    border-right: 1px solid #222226;
}

/* Top Brand Badge */
.brand-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 4px 18px 4px;
    border-bottom: 1px solid #222226;
    margin-bottom: 16px;
}
.brand-logo {
    background: linear-gradient(135deg, #FF6B35, #FF3D00);
    color: white;
    font-weight: 700;
    font-size: 16px;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.brand-title {
    font-size: 18px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.3px;
}

/* Hero Orange Gradient Card */
.kpi-card-orange {
    background: linear-gradient(135deg, #FF642E 0%, #E63E00 100%);
    border-radius: 18px;
    padding: 22px;
    color: #FFFFFF;
    box-shadow: 0 12px 28px rgba(255, 90, 38, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.15);
    height: 175px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

/* Dark Glass KPI Cards */
.kpi-card-dark {
    background: linear-gradient(180deg, #1A1A1E 0%, #141417 100%);
    border-radius: 18px;
    padding: 22px;
    color: #FFFFFF;
    border: 1px solid #26262B;
    height: 175px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card-top {
    display: flex;
    align-items: center;
    gap: 12px;
}
.card-icon-white {
    background: #FFFFFF;
    color: #FF5A26;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: bold;
}
.card-icon-dark {
    background: #FFFFFF;
    color: #141417;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: bold;
}
.card-title {
    font-size: 15px;
    font-weight: 600;
    line-height: 1.2;
}
.card-subtitle {
    font-size: 12px;
    opacity: 0.72;
}
.card-value-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
}
.card-amount {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.6px;
}
.badge-white {
    background: #FFFFFF;
    color: #E63E00;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
}
.badge-green {
    background: rgba(34, 197, 94, 0.15);
    color: #4ADE80;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
}
.badge-amber {
    background: rgba(251, 146, 60, 0.15);
    color: #FB923C;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 999px;
}
.card-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 10px;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    opacity: 0.85;
}

/* Section Containers */
.panel-box {
    background: #141417;
    border: 1px solid #242429;
    border-radius: 18px;
    padding: 20px;
    margin-top: 10px;
}
.wallet-mini-card {
    background: #1B1B1F;
    border: 1px solid #2A2A30;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.wallet-mini-title {
    font-size: 13px;
    color: #A1A1AA;
    font-weight: 600;
    margin-bottom: 4px;
}
.wallet-mini-amt {
    font-size: 19px;
    font-weight: 700;
    color: #FFFFFF;
}
.wallet-mini-sub {
    font-size: 11px;
    color: #71717A;
    margin-top: 2px;
}
.status-active {
    color: #FF642E;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# DATABASE CONNECTION (VERIFIED PURE-PYTHON MYSQL)
# ==========================================================
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="banking_user",
        password="Bank@1234",
        database="mini_core_banking",
        use_pure=True
    )

def run_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows)

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

# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================
with st.sidebar:
    st.markdown("""
        <div class="brand-header">
            <div class="brand-logo">⚡</div>
            <div>
                <div class="brand-title">CoreBank Pro</div>
                <div style="font-size:11px; color:#71717A;">ACID Ledger & Risk Engine</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "MAIN MENU",
        [
            "📊 Overview",
            "👤 Customer 360 & Ledger",
            "💸 Live Banking Simulator",
            "📑 Loans & EMI Schedule",
            "🚨 Fraud & Audit Center"
        ]
    )

    st.markdown("---")
    st.markdown("""
        <div style="background:#1A1A1E; border:1px solid #27272A; border-radius:14px; padding:14px;">
            <div style="font-size:13px; font-weight:600; color:#FFF;">🛡️ ACID & Fraud Guard</div>
            <div style="font-size:11px; color:#A1A1AA; margin-top:4px;">
                Row-level locking (FOR UPDATE) & real-time velocity triggers active.
            </div>
        </div>
    """, unsafe_allow_html=True)

try:
    # ==========================================================
    # PAGE 1: FINTECH EXECUTIVE OVERVIEW
    # ==========================================================
    if page == "📊 Overview":
        st.markdown("<h2 style='margin-bottom:0px;'>Overview</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#A1A1AA; font-size:13px; margin-top:2px;'>Real-time summary of core banking liquidity, loan book, and double-entry volume</p>", unsafe_allow_html=True)

        kpi_df = run_query("""
            SELECT 
                (SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE status = 'Active') AS total_deposits,
                (SELECT COUNT(*) FROM accounts WHERE status = 'Active') AS active_accounts,
                (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'Success') AS txn_volume,
                (SELECT COALESCE(SUM(outstanding_balance), 0) FROM loans WHERE status = 'Active') AS loan_book,
                (SELECT COUNT(*) FROM fraud_alerts WHERE alert_status = 'Open') AS open_alerts
        """)

        total_dep = float(kpi_df["total_deposits"][0])
        active_accs = int(kpi_df["active_accounts"][0])
        txn_vol = float(kpi_df["txn_volume"][0])
        loan_book = float(kpi_df["loan_book"][0])
        open_alerts = int(kpi_df["open_alerts"][0])

        # Row 1: 3 Premium Hero Cards (Matches Reference Design)
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
                <div class="kpi-card-orange">
                    <div class="card-top">
                        <div class="card-icon-white">💼</div>
                        <div>
                            <div class="card-title">Total Active Liquidity</div>
                            <div class="card-subtitle">Core Deposit Pool & Accounts</div>
                        </div>
                    </div>
                    <div class="card-value-row">
                        <div class="card-amount">₹{total_dep:,.2f}</div>
                        <div class="badge-white">{active_accs} Active ↑</div>
                    </div>
                    <div class="card-footer">
                        <span>Double-entry verified</span>
                        <span>→</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="kpi-card-dark">
                    <div class="card-top">
                        <div class="card-icon-dark">💳</div>
                        <div>
                            <div class="card-title">Processed Txn Volume</div>
                            <div class="card-subtitle">UPI, NEFT, IMPS & Cash</div>
                        </div>
                    </div>
                    <div class="card-value-row">
                        <div class="card-amount">₹{txn_vol:,.2f}</div>
                        <div class="badge-green">+ACID Safe</div>
                    </div>
                    <div class="card-footer">
                        <span>View ledger flow</span>
                        <span>→</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
                <div class="kpi-card-dark">
                    <div class="card-top">
                        <div class="card-icon-dark">📈</div>
                        <div>
                            <div class="card-title">Active Loan Portfolio</div>
                            <div class="card-subtitle">Principal Outstanding & Risk</div>
                        </div>
                    </div>
                    <div class="card-value-row">
                        <div class="card-amount">₹{loan_book:,.2f}</div>
                        <div class="badge-amber">{open_alerts} Fraud Alerts</div>
                    </div>
                    <div class="card-footer">
                        <span>Analyze exposure</span>
                        <span>→</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

        # Row 2: Left (Account Tiers 2x2 Grid) + Right (Cash Flow Highlight Bar Chart)
        left_col, right_col = st.columns([1.05, 1.35])

        with left_col:
            st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:16px; font-weight:600;'>Account Tiers & Vaults</div><div style='font-size:12px; color:#71717A; margin-bottom:14px;'>Live balances grouped by product tier</div>", unsafe_allow_html=True)

            tier_df = run_query("""
                SELECT at.type_name, COUNT(a.account_id) AS cnt, COALESCE(SUM(a.balance), 0) AS bal, at.interest_rate
                FROM account_types at
                LEFT JOIN accounts a ON at.type_id = a.type_id AND a.status = 'Active'
                GROUP BY at.type_id, at.type_name, at.interest_rate
                ORDER BY at.type_id
            """)

            icons = {"Savings": "🇮🇳 Savings Vault", "Current": "🏢 Current Corporate", "Salary": "💼 Salary Express"}
            w1, w2 = st.columns(2)
            for idx, row in tier_df.iterrows():
                target_col = w1 if idx % 2 == 0 else w2
                label = icons.get(row["type_name"], row["type_name"])
                with target_col:
                    st.markdown(f"""
                        <div class="wallet-mini-card">
                            <div class="wallet-mini-title">{label}</div>
                            <div class="wallet-mini-amt">₹{float(row['bal']):,.2f}</div>
                            <div class="wallet-mini-sub">{int(row['cnt'])} Accounts • {row['interest_rate']}% p.a.</div>
                            <div class="status-active">● Active</div>
                        </div>
                    """, unsafe_allow_html=True)

            with w2:
                st.markdown(f"""
                    <div class="wallet-mini-card">
                        <div class="wallet-mini-title">🛡️ Fraud Shield</div>
                        <div class="wallet-mini-amt">{open_alerts} Open</div>
                        <div class="wallet-mini-sub">Threshold: ₹1,00,000+</div>
                        <div class="status-active" style="color:#4ADE80;">● Trigger Armed</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
            st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:13px; color:#A1A1AA;'>Cash Flow by Payment Channel</div><div style='font-size:26px; font-weight:700; margin-bottom:6px;'>₹{txn_vol:,.2f}</div>", unsafe_allow_html=True)

            channel_df = run_query("""
                SELECT txn_type, SUM(amount) AS total_amount
                FROM transactions
                WHERE status = 'Success'
                GROUP BY txn_type
                ORDER BY total_amount DESC
            """)

            if not channel_df.empty:
                channel_df["total_amount"] = channel_df["total_amount"].astype(float)
                max_val = channel_df["total_amount"].max()
                bar_colors = [
                    "#FF5A26" if val == max_val else "#2A2A30"
                    for val in channel_df["total_amount"]
                ]

                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=channel_df["txn_type"],
                            y=channel_df["total_amount"],
                            marker=dict(
                                color=bar_colors,
                                cornerradius=12
                            ),
                            hovertemplate="<b>%{x}</b><br>Volume: ₹%{y:,.2f}<extra></extra>"
                        )
                    ]
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=265,
                    xaxis=dict(showgrid=False, color="#A1A1AA"),
                    yaxis=dict(showgrid=True, gridcolor="#222226", color="#71717A")
                )
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Row 3: Recent Activities Table
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px; font-weight:600; margin-bottom:8px;'>Recent Activities</div>", unsafe_allow_html=True)
        recent_txns = run_query("""
            SELECT 
                txn_reference AS 'Reference ID',
                txn_type AS 'Channel',
                amount AS 'Amount (INR)',
                status AS 'Status',
                remarks AS 'Activity / Remarks',
                created_at AS 'Timestamp'
            FROM transactions
            ORDER BY transaction_id DESC
            LIMIT 10
        """)
        st.dataframe(recent_txns, use_container_width=True, hide_index=True)

    # ==========================================================
    # PAGE 2: CUSTOMER 360 & DOUBLE-ENTRY LEDGER
    # ==========================================================
    elif page == "👤 Customer 360 & Ledger":
        st.title("👤 Customer 360 & Double-Entry Ledger")
        portfolio_df = run_query("SELECT * FROM vw_customer_portfolio ORDER BY balance DESC")
        search_term = st.text_input("Search Customer Name, CIF, or Account Number:")
        if search_term:
            filtered_df = portfolio_df[
                portfolio_df["full_name"].str.contains(search_term, case=False, na=False) |
                portfolio_df["customer_cif"].str.contains(search_term, case=False, na=False) |
                portfolio_df["account_number"].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = portfolio_df

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("📒 Account Statement (Double-Entry Ledger)")

        if not portfolio_df.empty:
            acc_options = {
                f"{row['account_number']} — {row['full_name']} (₹{float(row['balance']):,.2f})": row["account_id"]
                for _, row in portfolio_df.iterrows()
            }
            selected_label = st.selectbox("Select Account:", list(acc_options.keys()))
            selected_acc_id = int(acc_options[selected_label])

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
            st.dataframe(ledger_df, use_container_width=True, hide_index=True)

    # ==========================================================
    # PAGE 3: LIVE BANKING SIMULATOR
    # ==========================================================
    elif page == "💸 Live Banking Simulator":
        st.title("💸 Live ACID Banking Simulator")
        active_accs = run_query("""
            SELECT a.account_id, a.account_number, c.full_name, a.balance
            FROM accounts a JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.status = 'Active'
            ORDER BY a.account_id
        """)
        acc_map = {
            f"[{r['account_id']}] {r['account_number']} — {r['full_name']} (₹{float(r['balance']):,.2f})": int(r["account_id"])
            for _, r in active_accs.iterrows()
        }

        tab1, tab2, tab3 = st.tabs(["🔄 Fund Transfer", "➕ Cash Deposit", "➖ Cash Withdrawal"])

        with tab1:
            with st.form("transfer_form"):
                src_label = st.selectbox("From Account (Debit)", list(acc_map.keys()), index=0)
                dest_label = st.selectbox("To Account (Credit)", list(acc_map.keys()), index=1)
                channel = st.selectbox("Payment Channel", ["UPI", "NEFT", "IMPS", "Internal_Transfer"])
                amount = st.number_input("Transfer Amount (INR) — Tip: >= 100000 triggers Fraud Alert", min_value=1.0, value=5000.0, step=500.0)
                remarks = st.text_input("Remarks", value="Live Fintech Transfer")
                if st.form_submit_button("Execute ACID Transfer"):
                    ok, msg = call_procedure("sp_transfer_funds", [acc_map[src_label], acc_map[dest_label], float(amount), channel, remarks])
                    if ok:
                        st.success(f"✅ {msg} Double-entry Debit & Credit recorded.")
                    else:
                        st.error(f"❌ Rolled Back: {msg}")

        with tab2:
            with st.form("deposit_form"):
                dep_label = st.selectbox("Target Account", list(acc_map.keys()))
                dep_amt = st.number_input("Deposit Amount (INR)", min_value=1.0, value=10000.0, step=1000.0)
                dep_rem = st.text_input("Deposit Remarks", value="Branch Cash Deposit")
                if st.form_submit_button("Deposit Funds"):
                    ok, msg = call_procedure("sp_deposit_funds", [acc_map[dep_label], float(dep_amt), dep_rem])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

        with tab3:
            with st.form("withdraw_form"):
                wdr_label = st.selectbox("Account to Debit", list(acc_map.keys()))
                wdr_amt = st.number_input("Withdrawal Amount (INR)", min_value=1.0, value=2000.0, step=500.0)
                wdr_rem = st.text_input("Withdrawal Remarks", value="ATM Cash Withdrawal")
                if st.form_submit_button("Withdraw Funds"):
                    ok, msg = call_procedure("sp_withdraw_funds", [acc_map[wdr_label], float(wdr_amt), wdr_rem])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    # ==========================================================
    # PAGE 4: LOANS & EMI SCHEDULE
    # ==========================================================
    elif page == "📑 Loans & EMI Schedule":
        st.title("📑 Loans & EMI Repayment Management")
        loans_df = run_query("SELECT * FROM vw_loan_portfolio ORDER BY loan_id")
        st.dataframe(loans_df, use_container_width=True, hide_index=True)

        st.divider()
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Pay Next Monthly EMI")
            if not loans_df.empty:
                active_loans = loans_df[loans_df["loan_status"] == "Active"]
                if not active_loans.empty:
                    loan_choices = {
                        f"{r['loan_account_number']} — {r['borrower_name']} (EMI: ₹{float(r['emi_amount']):,.2f})": int(r["loan_id"])
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
        with col2:
            if not loans_df.empty and not active_loans.empty:
                st.subheader("EMI Amortization Schedule")
                sched_df = run_query("""
                    SELECT installment_number, due_date, emi_due, principal_component, interest_component, payment_status, paid_at
                    FROM loan_repayments WHERE loan_id = %s ORDER BY installment_number
                """, params=(sel_loan_id,))
                st.dataframe(sched_df, use_container_width=True, hide_index=True)

    # ==========================================================
    # PAGE 5: FRAUD & AUDIT CENTER
    # ==========================================================
    elif page == "🚨 Fraud & Audit Center":
        st.title("🚨 Real-Time Fraud Detection & Audit Trail")
        tab_f, tab_a = st.tabs(["🚨 Automated Fraud Alerts", "📜 System Audit Logs"])

        with tab_f:
            fraud_df = run_query("SELECT * FROM vw_fraud_monitoring ORDER BY alert_id DESC")
            st.dataframe(fraud_df, use_container_width=True, hide_index=True)

            if not fraud_df.empty:
                open_alerts = fraud_df[fraud_df["alert_status"] == "Open"]
                if not open_alerts.empty:
                    st.subheader("Compliance Officer Review")
                    alert_id = st.selectbox("Open Alert ID:", open_alerts["alert_id"].tolist())
                    new_status = st.selectbox("Resolution Status:", ["Resolved_Safe", "Confirmed_Fraud", "Under_Review"])
                    if st.button("Update Alert"):
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE fraud_alerts SET alert_status = %s, reviewed_by = 4, resolved_at = NOW() WHERE alert_id = %s",
                            (new_status, int(alert_id))
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"✅ Alert #{alert_id} updated.")
                        st.rerun()

        with tab_a:
            audit_df = run_query("SELECT * FROM audit_logs ORDER BY audit_id DESC LIMIT 50")
            st.dataframe(audit_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Database Connection Error: {e}")