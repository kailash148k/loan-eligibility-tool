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

# PART 2: PROFILE & FISCAL YEAR SETTINGS
st.sidebar.header("📁 Client File Management")
new_client_name = st.sidebar.text_input("Enter Client Name (e.g. Kailash)")
if st.sidebar.button("💾 Save Profile"):
    if new_client_name:
        st.session_state.client_database[new_client_name] = "Data Saved Locally"
        st.sidebar.success(f"File '{new_client_name}' Saved!")

st.header("1. Assessment Settings")
curr_fy = st.selectbox("Select Current Financial Year (Assessment)", ["FY 2024-25", "FY 2025-26"], index=0)
base_year = int(curr_fy.split(" ")[1].split("-")[0])

# PART 3: DYNAMIC APPLICANT DETAILS (3-YEAR HISTORICAL)
st.divider()
st.header("2. Applicant Details & 3-Year Financials")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=1)

total_avg_cash_profit = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} - 3 Year Financial History", expanded=True):
        col_info, col_years = st.columns([1, 3])
        
        with col_info:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"dob_{i}")
            st.write(f"**Age:** {date.today().year - dob.year} Years")
            avg_method = st.radio(f"Avg Method (App {i+1})", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}")

        # 3-Year Input Table
        years = [f"FY {base_year}-{str(base_year+1)[2:]}", 
                 f"FY {base_year-1}-{str(base_year)[2:]}", 
                 f"FY {base_year-2}-{str(base_year-1)[2:]}"]
        
        y_data = []
        c1, c2, c3 = st.columns(3)
        
        annual_cash_flows = []
        for idx, yr in enumerate(years):
            with [c1, c2, c3][idx]:
                st.markdown(f"**{yr}**")
                npbt = st.number_input(f"NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input(f"Depreciation", key=f"dep_{i}_{idx}", value=0.0)
                res = st.checkbox(f"Restrict Dep", key=f"res_{i}_{idx}", value=True)
                fam_sal = st.number_input(f"Family Salary", key=f"fs_{i}_{idx}", value=0.0)
                rent = st.number_input(f"Rent/Other", key=f"rent_{i}_{idx}", value=0.0)
                
                f_dep = min(dep, max(0.0, npbt)) if res else dep
                cash_flow = npbt + f_dep + fam_sal + rent
                annual_cash_flows.append(cash_flow)
                st.info(f"Cash Profit: ₹{cash_flow:,.0f}")

        # Calculate Average
        if avg_method == "Latest 2 Years":
            avg_profit = sum(annual_cash_flows[:2]) / 2
        else:
            avg_profit = sum(annual_cash_flows) / 3
        
        st.success(f"**Average Cash Profit (App {i+1}): ₹{avg_profit:,.0f}**")
        total_avg_cash_profit += avg_profit

# PART 4: EXISTING LOAN ANALYZER
st.divider()
st.header("3. Existing Loan Analyzer (Interest Add-Back)")
if 'loans' not in st.session_state: st.session_state.loans = []
if st.button("➕ Add Existing Loan"):
    st.session_state.loans.append({"amt": 0.0, "emi": 0.0, "roi": 9.0, "start": date(2021, 4, 1), "closure": date(2030, 3, 31), "add_back": True})

total_interest_addback = 0.0
total_existing_emi = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.number_input(f"Original Loan Amount", key=f"la_{idx}", value=0.0)
            st.selectbox("Type", ["Home", "LAP", "WCTL"], key=f"lt_{idx}")
        with l2:
            st.number_input(f"Monthly EMI", key=f"le_{idx}", value=0.0)
            st.number_input(f"ROI %", key=f"lr_{idx}", value=9.0)
        with l3:
            st.date_input("Start Date", key=f"ls_{idx}")
            st.date_input("Closure Date", key=f"lc_{idx}")
        with l4:
            ab = st.checkbox("Add Int to Profit", key=f"lab_{idx}", value=True)
            ob = st.checkbox("Obligate EMI", key=f"lob_{idx}", value=True)
            
            # Simple Current Year Interest Add-back
            if ab: total_interest_addback += (st.session_state[f"le_{idx}"] * 12) * 0.4
            if ob and date.today() < st.session_state[f"lc_{idx}"]: total_existing_emi += st.session_state[f"le_{idx}"]

# PART 5: FINAL ELIGIBILITY
st.divider()
st.header("4. Bank Policy & Final Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1: foir = st.slider("FOIR %", 40, 80, 60)
with col_p2: n_roi = st.number_input("New ROI %", value=9.5)
with col_p3: n_ten = st.number_input("New Tenure (Yrs)", value=14)

final_monthly_income = ((total_avg_cash_profit + total_interest_addback) / 12)
max_emi = (final_monthly_income * (foir / 100)) - total_existing_emi

if max_emi > 0:
    r = (n_roi / 12) / 100
    n = int(n_ten * 12)
    max_loan = max_emi * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    st.write(f"Based on Average Cash Profit: ₹{total_avg_cash_profit:,.0f}")
else:
    st.error("No eligibility found.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
