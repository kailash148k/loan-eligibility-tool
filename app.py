import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# PART 1: BRANDING & JOINT INCOME
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# Initialize global interest add-back variable
total_interest_addback_fy = 0.0

# PART 2: DETAILED EXISTING LOAN ANALYZER (MOVED UP FOR CALCULATION)
st.header("1. Existing Obligations & Interest Analysis")
loan_types = ["Home Loan", "LAP", "PL/BL", "WCTL", "Vehicle Loan"]

if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan Details"):
    st.session_state.loans.append({
        "type": "Home Loan", "emi": 0.0, "roi": 9.0, 
        "start": date(2021, 4, 1), "closure": date(2032, 3, 31), 
        "add_back": True, "obligate": True
    })

existing_loan_summary = []
total_monthly_emi_impact = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.session_state.loans[idx]['type'] = st.selectbox(f"Loan {idx+1} Type", loan_types, key=f"lt_{idx}")
            st.session_state.loans[idx]['emi'] = st.number_input(f"EMI Amount", value=loan['emi'], key=f"le_{idx}")
        with c2:
            st.session_state.loans[idx]['roi'] = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
            st.session_state.loans[idx]['start'] = st.date_input(f"Start Date", value=loan['start'], key=f"ls_{idx}")
        with c3:
            st.session_state.loans[idx]['closure'] = st.date_input(f"Closure Date", value=loan['closure'], key=f"lc_{idx}")
            st.session_state.loans[idx]['add_back'] = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
        with c4:
            st.session_state.loans[idx]['obligate'] = st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        # CALCULATION FOR THIS SPECIFIC LOAN
        today = date.today()
        if st.session_state.loans[idx]['obligate'] and today < st.session_state.loans[idx]['closure']:
            total_monthly_emi_impact += st.session_state.loans[idx]['emi']

        # Generating Interest/Principal Table for THIS loan
        loan_emi = st.session_state.loans[idx]['emi']
        loan_roi = st.session_state.loans[idx]['roi']
        
        # Approximate current interest for Part 1 Add-back
        if st.session_state.loans[idx]['add_back'] and today < st.session_state.loans[idx]['closure']:
            # Banking Method: Simple interest check on declining balance is complex here, 
            # so we use 60% of EMI as interest for the current FY add-back
            total_interest_addback_fy += (loan_emi * 12) * 0.5 

# PART 3: INCOME & CASH PROFIT ANALYSIS
st.divider()
st.header("2. Income & Cash Profit Analysis")
num_apps = st.number_input("Number of Applicants", 1, 10, 2)
app_income = 0.0

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
            st.write(f"**Add-back Interest:** ₹{total_interest_addback_fy/num_apps:,.0f}")
        
        f_dep = min(dep, max(0.0, npbt)) if res else dep
        app_income += (npbt + f_dep + net_sal + rent)

# Total Profit = Business Income + Interest Add-back
grand_total_income = app_income + total_interest_addback_fy

# PART 4: FINAL ELIGIBILITY
st.divider()
st.header("3. New Loan Eligibility Result")
foir = st.slider("FOIR %", 40, 80, 60)
new_roi = st.number_input("New ROI (%)", value=9.5)
new_tenure = st.number_input("New Tenure (Years)", value=14)

monthly_income = grand_total_income / 12
max_emi_allowed = (monthly_income * (foir / 100)) - total_monthly_emi_impact

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    
    st.info(f"Total Existing EMI Obligated: ₹{total_monthly_emi_impact:,.2f}")
    st.info(f"Total Interest Add-back included in Profit: ₹{total_interest_addback_fy:,.2f}")
else:
    st.error("No eligibility found.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376")
