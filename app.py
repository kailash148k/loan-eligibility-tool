import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# PART 1: BRANDING
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# PART 2: DYNAMIC APPLICANT DETAILS
st.header("1. Applicant Details & Demographics")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=2)

total_app_income = 0.0
for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Details", expanded=True):
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

# PART 3: EXISTING LOAN INTEREST PROJECTION (THE CORE REQUEST)
st.divider()
st.header("2. Existing Loan Analyzer (Yearly Interest Add-Back)")

if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan"):
    st.session_state.loans.append({"emi": 0.0, "roi": 9.0, "bal": 0.0, "add_back": True})

total_interest_addback_current_yr = 0.0
total_existing_emi_obligation = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"### Loan {idx+1} Analysis")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.selectbox(f"Type", ["Home Loan", "LAP", "PL/BL", "WCTL"], key=f"lt_{idx}")
            cur_bal = st.number_input(f"Current Outstanding Balance", value=loan['bal'], key=f"lb_{idx}")
        with l2:
            emi = st.number_input(f"Monthly EMI", value=loan['emi'], key=f"le_{idx}")
            roi = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
        with l3:
            closure = st.date_input(f"Loan Closure Date", key=f"lc_{idx}")
            add_back = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
        with l4:
            obligate = st.checkbox("Obligate EMI?", value=True, key=f"lob_{idx}")

        # GENERATE 14-YEAR INTEREST SCHEDULE FOR THIS EXISTING LOAN
        if add_back and cur_bal > 0:
            st.write(f"**Interest Add-Back Schedule (Loan {idx+1})**")
            loan_sched = []
            temp_bal = cur_bal
            for y in range(2021, 2036):
                # Calculate yearly interest for add-back
                yr_interest = temp_bal * (roi / 100)
                yr_principal = (emi * 12) - yr_interest
                temp_bal = max(0, temp_bal - yr_principal)
                
                loan_sched.append([f"FY {y}-{str(y+1)[2:]}", yr_interest, temp_bal])
                
                # Add to current year's profit if it's the current year
                if y == date.today().year or (y == 2025 and date.today().year == 2026):
                    total_interest_addback_current_yr += yr_interest

            # Display individual loan schedule
            df_loan = pd.DataFrame(loan_sched, columns=["Financial Year", "Interest to Add-Back", "Remaining Balance"])
            st.dataframe(df_loan.style.format({"Interest to Add-Back": "₹{:,.0f}", "Remaining Balance": "₹{:,.0f}"}), hide_index=True)

        if obligate and date.today() < closure:
            total_existing_emi_obligation += emi

# PART 4: FINAL ELIGIBILITY
st.divider()
st.header("3. Final Eligibility Result")
foir = st.slider("FOIR %", 40, 80, 60)
new_roi = st.number_input("New Loan ROI (%)", value=9.5)
new_tenure = st.number_input("New Loan Tenure (Years)", value=14)

# Final Cash Profit Calculation
final_cash_profit = total_app_income + total_interest_addback_current_yr
monthly_profit = final_cash_profit / 12
max_emi_allowed = (monthly_profit * (foir / 100)) - total_existing_emi_obligation

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
    st.info(f"Current Year Interest Add-Back Included: ₹{total_interest_addback_current_yr:,.0f}")
else:
    st.error("No eligibility based on FOIR and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
