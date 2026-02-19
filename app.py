import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="CA Loan Master", layout="wide")

# PART 1: BRANDING & JOINT INCOME
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

st.header("1. Income & Cash Profit Analysis")
num_apps = st.number_input("Number of Applicants", 1, 10, 2)
total_interest_addback = 0.0
grand_total_income = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Income Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"np_{i}")
            net_sal = st.number_input(f"Net Salary (App {i+1})", value=0.0, key=f"ns_{i}")
        with col2:
            dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dp_{i}")
            rent = st.number_input(f"Rental Income (App {i+1})", value=0.0, key=f"ri_{i}")
        with col3:
            res = st.checkbox("Restrict Dep to NPBT", value=True, key=f"re_{i}")
            fut_rent = st.number_input(f"Future Rental (App {i+1})", value=0.0, key=f"fr_{i}")
        
        f_dep = min(dep, max(0.0, npbt)) if res else dep
        grand_total_income += (npbt + f_dep + net_sal + rent + fut_rent)

# PART 2: DETAILED EXISTING LOAN ANALYZER
st.divider()
st.header("2. Existing Obligations & Property Details")

loan_types = ["Home Loan", "LAP", "PL/BL", "WCTL", "Vehicle Loan"]
prop_types = ["Residential House", "Commercial Building", "Vacant Plot", "Rented Residential", "Rented Commercial"]

if 'loans' not in st.session_state:
    st.session_state.loans = []

def add_loan():
    st.session_state.loans.append({
        "type": "Home Loan", "emi": 0.0, "roi": 9.0, "tenure": 120, 
        "start": date(2022, 1, 1), "moratorium": 0, "add_back": False, "obligate": True
    })

if st.button("➕ Add Existing Loan Details"):
    add_loan()

total_running_emi = 0.0
yearly_interest_data = pd.DataFrame(index=[f"FY {y}-{y+1-2000}" for y in range(2021, 2035)])

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.session_state.loans[idx]['type'] = st.selectbox(f"Loan {idx+1} Type", loan_types, key=f"lt_{idx}")
            st.session_state.loans[idx]['prop'] = st.selectbox(f"Property Type", prop_types, key=f"pt_{idx}")
        with c2:
            st.session_state.loans[idx]['emi'] = st.number_input(f"EMI Amount", value=loan['emi'], key=f"le_{idx}")
            st.session_state.loans[idx]['roi'] = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
        with c3:
            st.session_state.loans[idx]['tenure'] = st.number_input(f"Tenure (Months)", value=loan['tenure'], key=f"ltn_{idx}")
            st.session_state.loans[idx]['start'] = st.date_input(f"1st EMI Date", value=loan['start'], key=f"ls_{idx}")
        with c4:
            st.session_state.loans[idx]['add_back'] = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
            st.session_state.loans[idx]['obligate'] = st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        if st.session_state.loans[idx]['obligate']:
            total_running_emi += st.session_state.loans[idx]['emi']

# PART 3: CALCULATION & ELIGIBILITY
st.divider()
st.header("3. New Loan Parameters & Results")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New Loan ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Loan Tenure (Years)", value=14)

# Final Calculation
# As a CA, we add back the interest on existing loans to the profit if selected
monthly_income = (grand_total_income / 12)
max_emi_allowed = (monthly_income * (foir / 100)) - total_running_emi

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = new_tenure * 12
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    
    # Yearly Schedule Table
    st.write("### 14-Year Principal/Interest Projection")
    res_data = []
    bal = max_loan
    for y in range(2022, 2036):
        y_int = bal * (new_roi / 100)
        y_pri = (max_emi_allowed * 12) - y_int
        bal = max(0, bal - y_pri)
        res_data.append([f"FY {y}-{y+1-2000}", y_int, y_pri, bal])
    
    df_final = pd.DataFrame(res_data, columns=["Financial Year", "Interest Paid", "Principal Paid", "Closing Balance"])
    st.table(df_final.style.format({"Interest Paid": "₹{:,.0f}", "Principal Paid": "₹{:,.0f}", "Closing Balance": "₹{:,.0f}"}))
else:
    st.error("No eligibility based on FOIR and Running Obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
