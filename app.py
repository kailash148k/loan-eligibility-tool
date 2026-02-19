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
client_name = st.sidebar.text_input("Enter Client Name (e.g. Kailash)")
if st.sidebar.button("💾 Save Profile"):
    if client_name:
        st.session_state.client_database[client_name] = "Data Saved"
        st.sidebar.success(f"File '{client_name}' Saved!")

st.header("1. Assessment Settings")
curr_fy = st.selectbox("Select Current Financial Year (Assessment)", ["FY 2024-25", "FY 2025-26"], index=0)
base_year = int(curr_fy.split(" ")[1].split("-")[0])

# PART 3: DYNAMIC APPLICANT DETAILS (3-YEAR HISTORICAL + MANUAL INTEREST)
st.divider()
st.header("2. Applicant Details & 3-Year Financials")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=1)

total_avg_cash_profit = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} - 3 Year Financial History", expanded=True):
        col_info, col_extra = st.columns([1, 1])
        with col_info:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"dob_{i}")
            st.write(f"**Age:** {date.today().year - dob.year} Years")
        with col_extra:
            avg_method = st.radio(f"Avg Method (App {i+1})", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}", horizontal=True)

        # 3-Year Input Table
        years = [f"FY {base_year}-{str(base_year+1)[2:]}", 
                 f"FY {base_year-1}-{str(base_year)[2:]}", 
                 f"FY {base_year-2}-{str(base_year-1)[2:]}"]
        
        c1, c2, c3 = st.columns(3)
        annual_cash_flows = []
        
        for idx, yr in enumerate(years):
            with [c1, c2, c3][idx]:
                st.markdown(f"### {yr}")
                npbt = st.number_input(f"NPBT ({yr})", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input(f"Depreciation ({yr})", key=f"dep_{i}_{idx}", value=0.0)
                res = st.checkbox(f"Restrict Dep to NPBT", key=f"res_{i}_{idx}", value=True)
                
                # MANUAL ADD-BACKS
                int_tl = st.number_input(f"Manual Interest on Term Loan ({yr})", key=f"int_{i}_{idx}", value=0.0)
                fam_sal = st.number_input(f"Family Salary ({yr})", key=f"fs_{i}_{idx}", value=0.0)
                rent_inc = st.number_input(f"Future/Current Rent ({yr})", key=f"rent_{i}_{idx}", value=0.0)
                
                f_dep = min(dep, max(0.0, npbt)) if res else dep
                # Core Banking Cash Flow Logic
                cash_flow = npbt + f_dep + int_tl + fam_sal + rent_inc
                annual_cash_flows.append(cash_flow)
                st.info(f"Yearly Cash Profit: ₹{cash_flow:,.0f}")

        # Calculate Average
        avg_profit = (sum(annual_cash_flows[:2]) / 2) if avg_method == "Latest 2 Years" else (sum(annual_cash_flows) / 3)
        st.success(f"**Average Cash Profit for Eligibility: ₹{avg_profit:,.0f}**")
        total_avg_cash_profit += avg_profit

# PART 4: EXISTING LOAN OBLIGATIONS (SIMPLE MODE)
st.divider()
st.header("3. Current Monthly Obligations")
total_running_emi = st.number_input("Total Monthly EMIs of all Running Loans", value=0.0)

# PART 5: FINAL ELIGIBILITY
st.divider()
st.header("4. Bank Policy & Results")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New Loan Rate (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Loan Tenure (Years)", value=15)

final_monthly_income = (total_avg_cash_profit / 12)
max_emi = (final_monthly_income * (foir / 100)) - total_running_emi

if max_emi > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
else:
    st.error("Based on Average Cash Profit and existing EMIs, there is no current eligibility.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
