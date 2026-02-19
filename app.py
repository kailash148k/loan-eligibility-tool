import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# PART 1: BRANDING
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# PART 2: DYNAMIC APPLICANT DETAILS
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
            with c2:
                dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dep_{i}")
            with c3:
                res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", value=True, key=f"res_{i}")
                sal_rent = st.number_input(f"Salary/Rent (App {i+1})", value=0.0, key=f"sal_{i}")
            
            f_dep = min(dep, max(0.0, npbt)) if res else dep
            total_app_income += (npbt + f_dep + sal_rent)

# PART 3: EXISTING LOAN ANALYZER (FLEXIBLE EMI/TENURE)
st.divider()
st.header("2. Existing Loan Analyzer (Interest Add-Back Logic)")

if 'loans' not in st.session_state:
    st.session_state.loans = []

def add_loan():
    st.session_state.loans.append({
        "type": "Home Loan", "amt": 0.0, "emi": 0.0, "roi": 9.0, 
        "tenure_m": 120, "input_mode": "EMI",
        "start": date(2021, 4, 1), "closure": date(2030, 3, 31), 
        "add_back": True, "obligate": True
    })

if st.button("➕ Add Existing Loan Details"):
    add_loan()

total_interest_addback_fy = 0.0
total_existing_emi_impact = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"### Loan {idx+1} Analysis")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.session_state.loans[idx]['type'] = st.selectbox(f"Type (L{idx})", ["Home Loan", "LAP", "PL/BL", "WCTL"], key=f"lt_{idx}")
            st.session_state.loans[idx]['amt'] = st.number_input(f"Original Loan Amount", value=loan['amt'], key=f"la_{idx}")
            input_mode = st.radio("Input Mode", ["Know EMI", "Know Tenure"], key=f"mode_{idx}", horizontal=True)
        
        with l2:
            st.session_state.loans[idx]['roi'] = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
            if input_mode == "Know EMI":
                st.session_state.loans[idx]['emi'] = st.number_input(f"Monthly EMI", value=loan['emi'], key=f"le_{idx}")
            else:
                tenure_months = st.number_input(f"Original Tenure (Months)", value=loan['tenure_m'], key=f"ltm_{idx}")
                # Calculate EMI if Tenure is provided
                if tenure_months > 0 and st.session_state.loans[idx]['roi'] > 0:
                    r_monthly = (st.session_state.loans[idx]['roi'] / 100) / 12
                    st.session_state.loans[idx]['emi'] = (st.session_state.loans[idx]['amt'] * r_monthly * (1 + r_monthly)**tenure_months) / ((1 + r_monthly)**tenure_months - 1)
                    st.info(f"Calculated EMI: ₹{st.session_state.loans[idx]['emi']:,.0f}")
                else:
                    st.session_state.loans[idx]['emi'] = 0.0

        with l3:
            st.session_state.loans[idx]['start'] = st.date_input(f"Loan Start Date", value=loan['start'], key=f"ls_{idx}")
            st.session_state.loans[idx]['closure'] = st.date_input(f"Loan Closure Date", value=loan['closure'], key=f"lc_{idx}")
        
        with l4:
            st.session_state.loans[idx]['add_back'] = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
            st.session_state.loans[idx]['obligate'] = st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        # CALCULATE HISTORICAL INTEREST
        if st.session_state.loans[idx]['amt'] > 0 and st.session_state.loans[idx]['emi'] > 0:
            st.write(f"**Historical Interest Schedule (Loan {idx+1})**")
            loan_sched = []
            temp_bal = st.session_state.loans[idx]['amt']
            for y in range(st.session_state.loans[idx]['start'].year, 2036):
                yr_interest = temp_bal * (st.session_state.loans[idx]['roi'] / 100)
                yr_principal = max(0, (st.session_state.loans[idx]['emi'] * 12) - yr_interest)
                temp_bal = max(0, temp_bal - yr_principal)
                if y >= 2021:
                    loan_sched.append([f"FY {y}-{str(y+1)[2:]}", yr_interest, temp_bal])
                    if y == 2025 and st.session_state.loans[idx]['add_back']:
                        total_interest_addback_fy += yr_interest
            
            if loan_sched:
                df_loan = pd.DataFrame(loan_sched, columns=["Financial Year", "Interest Paid", "Closing Balance"])
                st.table(df_loan.style.format({"Interest Paid": "₹{:,.0f}", "Closing Balance": "₹{:,.0f}"}))

        if st.session_state.loans[idx]['obligate'] and date.today() < st.session_state.loans[idx]['closure']:
            total_existing_emi_impact += st.session_state.loans[idx]['emi']

# PART 4: FINAL ELIGIBILITY
st.divider()
st.header("3. Bank Policy & Final Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Tenure (Years)", value=14)

final_cash_profit = total_app_income + total_interest_addback_fy
max_emi_allowed = ((final_cash_profit / 12) * (foir / 100)) - total_existing_emi_impact

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
else:
    st.error("No eligibility based on FOIR and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
