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

applicants = []
total_income_from_apps = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Information & Income", expanded=True):
        col_info, col_fin = st.columns([1, 2])
        with col_info:
            name = st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"dob_{i}")
            age = date.today().year - dob.year
            st.write(f"**Age:** {age} Years")
            pan = st.text_input(f"PAN (App {i+1})", key=f"pan_{i}")
        
        with col_fin:
            c1, c2, c3 = st.columns(3)
            with c1:
                npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"npbt_{i}")
                net_sal = st.number_input(f"Net Salary (App {i+1})", value=0.0, key=f"ns_{i}")
            with c2:
                dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dep_{i}")
                rent = st.number_input(f"Rent Income (App {i+1})", value=0.0, key=f"ri_{i}")
            with c3:
                res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", value=True, key=f"res_{i}")
                fut_rent = st.number_input(f"Future Rent (App {i+1})", value=0.0, key=f"fr_{i}")
            
            # CA Income Logic
            f_dep = min(dep, max(0.0, npbt)) if res else dep
            total_income_from_apps += (npbt + f_dep + net_sal + rent + fut_rent)

# PART 3: EXISTING LOAN ANALYZER (FOR INTEREST ADD-BACK)
st.divider()
st.header("2. Existing Loan Analyzer (Term Loan Interest)")
if 'loans' not in st.session_state:
    st.session_state.loans = []

if st.button("➕ Add Existing Loan Details"):
    st.session_state.loans.append({"emi": 0.0, "roi": 9.0, "closure": date(2030, 1, 1), "add_back": True})

total_interest_addback = 0.0
total_existing_emi = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            st.selectbox(f"Loan {idx+1} Type", ["Home Loan", "LAP", "PL/BL", "WCTL"], key=f"lt_{idx}")
            emi = st.number_input(f"Monthly EMI", value=loan['emi'], key=f"le_{idx}")
        with l2:
            roi = st.number_input(f"ROI (%)", value=loan['roi'], key=f"lr_{idx}")
            st.date_input(f"Start Date", key=f"ls_{idx}")
        with l3:
            closure = st.date_input(f"Closure Date", value=loan['closure'], key=f"lc_{idx}")
            add_back = st.checkbox("Add Interest to Profit?", value=loan['add_back'], key=f"lab_{idx}")
        with l4:
            obligate = st.checkbox("Obligate EMI?", value=True, key=f"lob_{idx}")
            
        if obligate and date.today() < closure:
            total_existing_emi += emi
        if add_back and date.today() < closure:
            # Banking calculation for current interest portion
            total_interest_addback += (emi * 12) * 0.5

# PART 4: FINAL ELIGIBILITY & OUTPUT
st.divider()
st.header("3. Bank Policy & Final Eligibility")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
    new_roi = st.number_input("New ROI (%)", value=9.5)
with col_p3:
    new_tenure = st.number_input("New Tenure (Years)", value=14)

# Final Cash Profit = Application Income + Interest Add-back
final_cash_profit = total_income_from_apps + total_interest_addback
monthly_profit = final_cash_profit / 12
max_emi_allowed = (monthly_profit * (foir / 100)) - total_existing_emi

if max_emi_allowed > 0:
    r = (new_roi / 12) / 100
    n = int(new_tenure * 12)
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
    
    # 14-Year Breakdown
    st.write("### 14-Year Principal/Interest Projection")
    res_data = []
    bal = max_loan
    for y in range(2021, 2036):
        y_int = bal * (new_roi / 100)
        y_pri = (max_emi_allowed * 12) - y_int
        bal = max(0, bal - y_pri)
        res_data.append([f"FY {y}-{str(y+1)[2:]}", y_int, y_pri, bal])
    
    df = pd.DataFrame(res_data, columns=["Financial Year", "Interest", "Principal", "Balance"])
    st.table(df.style.format({"Interest": "₹{:,.0f}", "Principal": "₹{:,.0f}", "Balance": "₹{:,.0f}"}))
else:
    st.error("No eligibility based on FOIR and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
