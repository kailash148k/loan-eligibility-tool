import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# INITIALIZE MASTER DATA STORAGE
if 'client_database' not in st.session_state:
    st.session_state.client_database = {}

# PART 1: BRANDING
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# PART 2: PROFILE MANAGEMENT
st.sidebar.header("📁 Client File Management")
new_client_name = st.sidebar.text_input("Enter New Client Name")
if st.sidebar.button("💾 Save/Update Current Profile"):
    if new_client_name:
        # Saving all current inputs to the database
        st.session_state.client_database[new_client_name] = st.session_state.to_dict()
        st.sidebar.success(f"File '{new_client_name}' Saved!")

selected_profile = st.sidebar.selectbox("Load Saved Profile", ["None"] + list(st.session_state.client_database.keys()))
if selected_profile != "None":
    st.sidebar.info(f"Viewing File: {selected_profile}")

# PART 3: DYNAMIC APPLICANT DETAILS
st.header("1. Applicant Details & Financials")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=1)

total_app_income = 0.0
for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Details & Financials", expanded=True):
        col_info, col_fin = st.columns([1, 2])
        with col_info:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"dob_{i}")
            st.write(f"**Age:** {date.today().year - dob.year} Years")
        
        with col_fin:
            c1, c2, c3 = st.columns(3)
            with c1:
                npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"npbt_{i}")
                net_sal = st.number_input(f"Net Salary (App {i+1})", value=0.0, key=f"ns_{i}")
            with c2:
                dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dep_{i}")
                fam_sal = st.number_input(f"Salary to Family (App {i+1})", value=0.0, key=f"fs_{i}")
            with c3:
                res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", value=True, key=f"res_{i}")
                curr_rent = st.number_input(f"Current Rent (App {i+1})", value=0.0, key=f"cr_{i}")
                future_rent = st.number_input(f"Future Rental (App {i+1})", value=0.0, key=f"fr_{i}")
            
            f_dep = min(dep, max(0.0, npbt)) if res else dep
            total_app_income += (npbt + f_dep + net_sal + fam_sal + curr_rent + future_rent)

# PART 4: EXISTING LOAN ANALYZER
st.divider()
st.header("2. Existing Loan Analyzer")

if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan Details"):
    st.session_state.loans.append({
        "type": "Home Loan", "amt": 0.0, "emi": 0.0, "roi": 9.0, 
        "tenure_m": 120, "input_mode": "Know EMI",
        "start": date(2021, 4, 1), "closure": date(2030, 3, 31), 
        "add_back": True, "obligate": True
    })

total_interest_addback_fy = 0.0
total_existing_emi_impact = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"### Loan {idx+1} Analysis")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.selectbox(f"Type (L{idx})", ["Home Loan", "LAP", "PL/BL", "WCTL"], key=f"lt_{idx}")
            st.number_input(f"Original Loan Amount", value=loan['amt'], key=f"la_{idx}")
            mode = st.radio("Input Mode", ["Know EMI", "Know Tenure"], key=f"mode_{idx}", horizontal=True)
        
        with l2:
            st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
            if mode == "Know EMI":
                st.number_input(f"Monthly EMI", value=loan['emi'], key=f"le_{idx}")
            else:
                tm = st.number_input(f"Original Tenure (Months)", value=loan['tenure_m'], key=f"ltm_{idx}")
                # EMI Calculation Logic
                r_m = (st.session_state[f"lr_{idx}"] / 100) / 12
                if tm > 0:
                    calc_emi = (st.session_state[f"la_{idx}"] * r_m * (1 + r_m)**tm) / ((1 + r_m)**tm - 1)
                    st.session_state[f"le_{idx}"] = calc_emi
                    st.info(f"Calculated EMI: ₹{calc_emi:,.0f}")

        with l3:
            st.date_input(f"Loan Start Date", value=loan['start'], key=f"ls_{idx}")
            st.date_input(f"Loan Closure Date", value=loan['closure'], key=f"lc_{idx}")
        
        with l4:
            st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
            st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        # Yearly Schedule & Add-Back Calculation
        if st.session_state[f"la_{idx}"] > 0:
            loan_sched = []
            temp_bal = st.session_state[f"la_{idx}"]
            for y in range(st.session_state[f"ls_{idx}"].year, 2036):
                yr_int = temp_bal * (st.session_state[f"lr_{idx}"] / 100)
                yr_pri = max(0, (st.session_state[f"le_{idx}"] * 12) - yr_int)
                temp_bal = max(0, temp_bal - yr_pri)
                if y >= 2021:
                    loan_sched.append([f"FY {y}-{str(y+1)[2:]}", yr_int, temp_bal])
                    if y == 2025 and st.session_state[f"lab_{idx}"]:
                        total_interest_addback_fy += yr_int
            
            if st.checkbox(f"Show Schedule for Loan {idx+1}", key=f"show_{idx}"):
                df_loan = pd.DataFrame(loan_sched, columns=["Financial Year", "Interest Paid", "Closing Balance"])
                st.table(df_loan.style.format({"Interest Paid": "₹{:,.0f}", "Closing Balance": "₹{:,.0f}"}))

        if st.session_state[f"lob_{idx}"] and date.today() < st.session_state[f"lc_{idx}"]:
            total_existing_emi_impact += st.session_state[f"le_{idx}"]

# PART 5: FINAL ELIGIBILITY
st.divider()
st.header("3. Bank Policy & Final Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New Loan ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Tenure (Years)", value=14)

final_cash_profit = total_app_income + total_interest_addback_fy
max_emi_allowed = ((final_cash_profit / 12) * (foir / 100)) - total_existing_emi_impact

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
    st.info(f"Total Yearly Cash Flow for Eligibility: ₹{final_cash_profit:,.0f}")
else:
    st.error("No eligibility based on FOIR and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
