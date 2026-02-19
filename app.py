import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# PART 1: BRANDING & JOINT INCOME
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

st.header("1. Income & Cash Profit Analysis")
num_apps = st.number_input("Number of Applicants", 1, 10, 2)
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
            fam_sal = st.number_input(f"Family Salary (App {i+1})", value=0.0, key=f"fs_{i}")
        
        f_dep = min(dep, max(0.0, npbt)) if res else dep
        grand_total_income += (npbt + f_dep + net_sal + rent + fut_rent + fam_sal)

# PART 2: DETAILED EXISTING LOAN ANALYZER
st.divider()
st.header("2. Existing Obligations & Property Details")

loan_types = ["Home Loan", "LAP", "PL/BL", "WCTL", "Vehicle Loan"]
prop_types = ["Residential House", "Commercial Building", "Vacant Plot", "Rented Residential", "Rented Commercial"]

if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan"):
    st.session_state.loans.append({
        "type": "Home Loan", "emi": 0.0, "roi": 9.0, 
        "start": date(2022, 4, 1), "closure": date(2032, 3, 31), 
        "add_back": False, "obligate": True
    })

total_monthly_emi_impact = 0.0
total_interest_to_add = 0.0

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
            st.session_state.loans[idx]['start'] = st.date_input(f"1st EMI Date", value=loan['start'], key=f"ls_{idx}")
            st.session_state.loans[idx]['closure'] = st.date_input(f"Loan Closure Date", value=loan['closure'], key=f"lc_{idx}")
        with c4:
            st.session_state.loans[idx]['add_back'] = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
            st.session_state.loans[idx]['obligate'] = st.checkbox("Obligate EMI?", value=loan['obligate'], key=f"lob_{idx}")

        today = date.today()
        if st.session_state.loans[idx]['obligate'] and today < st.session_state.loans[idx]['closure']:
            total_monthly_emi_impact += st.session_state.loans[idx]['emi']
        
        if st.session_state.loans[idx]['add_back'] and today < st.session_state.loans[idx]['closure']:
            # CA Logic: Approx Interest add-back
            total_interest_to_add += (st.session_state.loans[idx]['emi'] * 12) * 0.6 # Assuming 60% of EMI is interest initially

# PART 3: RESULTS
st.divider()
st.header("3. New Loan Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Tenure (Years)", value=14)

monthly_income = (grand_total_income + total_interest_to_add) / 12
max_emi_allowed = (monthly_income * (foir / 100)) - total_monthly_emi_impact

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = new_tenure * 12
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    
    # Yearly Principal/Interest Table
    st.write("### Principal/Interest Projection (FY 2021-2035)")
    res_data = []
    bal = max_loan
    for y in range(2021, 2036):
        y_int = bal * (new_roi / 100)
        y_pri = (max_emi_allowed * 12) - y_int
        bal = max(0, bal - y_pri)
        res_data.append([f"FY {y}-{y+1-2000}", y_int, y_pri, bal])
    
    df = pd.DataFrame(res_data, columns=["Financial Year", "Interest", "Principal", "Balance"])
    st.table(df.style.format("₹{:,.0f}"))
else:
    st.error("No eligibility found.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376")
