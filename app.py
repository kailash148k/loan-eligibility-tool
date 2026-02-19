import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Loan Eligibility Master", layout="wide")

# PART 1: BRANDING
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# PART 2: APPLICANT SELECTION
st.header("1. Applicant Details")
num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=1)

total_annual_profit = 0.0

# PART 3: DETAILED INCOME LOOP
for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Details & Financials", expanded=True):
        col_name, col_dob = st.columns(2)
        with col_name:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
        with col_dob:
            dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"dob_{i}")
            age = date.today().year - dob.year
            st.caption(f"Age: {age} Years")
        
        st.write("**Business/Professional Income**")
        c1, c2, c3 = st.columns(3)
        with c1:
            npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"npbt_{i}")
        with c2:
            dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dep_{i}")
        with c3:
            res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", value=True, key=f"res_{i}")
        
        st.write("**Other Income Heads**")
        c4, c5, c6 = st.columns(3)
        with c4:
            net_sal = st.number_input(f"Net Salary (App {i+1})", value=0.0, key=f"ns_{i}")
            rent = st.number_input(f"House Rent Income (App {i+1})", value=0.0, key=f"hr_{i}")
        with c5:
            term_int = st.number_input(f"Interest on Term Loan (App {i+1})", value=0.0, key=f"ti_{i}")
            fam_sal = st.number_input(f"Salary to Family Members (App {i+1})", value=0.0, key=f"fs_{i}")
        with c6:
            fut_rent = st.number_input(f"Future Rental Income (App {i+1})", value=0.0, key=f"fr_{i}")

        # CALCULATION LOGIC
        f_dep = min(dep, max(0.0, npbt)) if res else dep
        # Adding all heads back to cash flow as per banking norms
        app_total_income = npbt + f_dep + net_sal + rent + term_int + fam_sal + fut_rent
        total_annual_profit += app_total_income

# PART 4: OBLIGATIONS & POLICY
st.header("2. Bank Policy & Obligations")
col_obs, col_foir, col_roi, col_ten = st.columns(4)
with col_obs:
    running_emi = st.number_input("Total Monthly Running EMIs", value=0.0)
with col_foir:
    foir = st.slider("FOIR %", 40, 80, 60)
with col_roi:
    roi = st.number_input("Interest Rate (%)", value=9.5)
with col_ten:
    tenure = st.number_input("Tenure (Years)", value=14)

monthly_income = total_annual_profit / 12
max_emi_allowed = (monthly_income * (foir / 100)) - running_emi

# PART 5: RESULTS & SCHEDULE
st.divider()
st.header("3. Final Eligibility Results")

if max_emi_allowed > 0:
    r = (roi / 12) / 100
    n = tenure * 12
    max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)
    
    st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
    
    st.write("### 14-Year Repayment Schedule")
    bal = max_loan
    sched_data = []
    for y in range(1, int(tenure) + 1):
        int_yr = bal * (roi / 100)
        pri_yr = (max_emi_allowed * 12) - int_yr
        bal = max(0, bal - pri_yr)
        sched_data.append([f"Year {y}", int_yr, pri_yr, bal])
    
    df = pd.DataFrame(sched_data, columns=["Year", "Interest Paid", "Principal Paid", "Closing Balance"])
    st.table(df.style.format({"Interest Paid": "₹{:,.0f}", "Principal Paid": "₹{:,.0f}", "Closing Balance": "₹{:,.0f}"}))
else:
    st.error("Based on FOIR and obligations, the applicants are not eligible for a new loan.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
