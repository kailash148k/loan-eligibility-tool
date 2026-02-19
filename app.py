import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# --- PART 1: BRANDING ---
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# --- PART 2: DYNAMIC APPLICANT DETAILS ---
st.header("1. Applicant Details & Demographics")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=2)

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
            with c2:
                dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dep_{i}")
            with c3:
                res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", value=True, key=f"res_{i}")
            
            f_dep = min(dep, max(0.0, npbt)) if res else dep
            total_app_income += (npbt + f_dep)

# --- PART 3: EXISTING LOAN INTEREST ADD-BACK (14-YEAR SCHEDULE) ---
st.divider()
st.header("2. Existing Loan Analyzer (Yearly Interest Add-Back)")

if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan"):
    # Fix: Initializing all keys to avoid KeyError
    st.session_state.loans.append({
        "type": "Home Loan", 
        "bal": 0.0, 
        "emi": 0.0, 
        "roi": 9.0, 
        "closure": date(2030, 1, 1),
        "add_back": True,
        "obligate": True
    })

total_interest_addback_fy = 0.0
total_existing_emi_impact = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"### Loan {idx+1} Analysis")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.session_state.loans[idx]['type'] = st.selectbox(f"Type (Loan {idx+1})", ["Home Loan", "LAP", "PL/BL", "WCTL"], key=f"lt_{idx}")
            st.session_state.loans[idx]['bal'] = st.number_input(f"Current Outstanding Balance", value=loan['bal'], key=f"lb_{idx}")
        with l2:
            st.session_state.loans[idx]['emi'] = st.number_input(f"Monthly EMI", value=loan['emi'], key=f"le_{idx}")
            st.session_state.loans[idx]['roi'] = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
        with l3:
            st.session_state.loans[idx]['closure'] = st.date_input(f"Loan Closure Date", value=loan['closure'], key=f"lc_{idx}")
            st.session_state.loans[idx]['add_back'] = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
        with l4:
            st.session_state.loans[idx]['obligate'] = st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        # GENERATE 14-YEAR INTEREST SCHEDULE FOR THIS EXISTING LOAN
        if st.session_state.loans[idx]['add_back'] and st.session_state.loans[idx]['bal'] > 0:
            st.write(f"**FY 2021-2035 Interest Add-Back Schedule (Loan {idx+1})**")
            loan_sched = []
            temp_bal = st.session_state.loans[idx]['bal']
            loan_roi = st.session_state.loans[idx]['roi']
            loan_emi = st.session_state.loans[idx]['emi']
            
            for y in range(2021, 2036):
                yr_interest = temp_bal * (loan_roi / 100)
                yr_principal = max(0, (loan_emi * 12) - yr_interest)
                temp_bal = max(0, temp_bal - yr_principal)
                
                loan_sched.append([f"FY {y}-{str(y+1)[2:]}", yr_interest, temp_bal])
                
                # Add to total if this is the current financial year (2025-26)
                if y == 2025:
                    total_interest_addback_fy += yr_interest

            df_loan = pd.DataFrame(loan_sched, columns=["Financial Year", "Interest to Add-Back", "Remaining Balance"])
            st.table(df_loan.style.format({"Interest to Add-Back": "₹{:,.0f}", "Remaining Balance": "₹{:,.0f}"}))

        if st.session_state.loans[idx]['obligate'] and date.today() < st.session_state.loans[idx]['closure']:
            total_existing_emi_impact += st.session_state.loans[idx]['emi']

# --- PART 4: FINAL ELIGIBILITY ---
st.divider()
st.header("3. Bank Policy & Final Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New Loan ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Loan Tenure (Years)", value=14)

# Final Calculation
final_cash_profit = total_app_income + total_interest_addback_fy
monthly_profit = final_cash_profit / 12
max_emi_allowed = (monthly_profit * (foir / 100)) - total_existing_emi_impact

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
    st.info(f"Total Yearly Interest Add-Back from Existing Loans: ₹{total_interest_addback_fy:,.0f}")
else:
    st.error("No eligibility found based on FOIR and Obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
