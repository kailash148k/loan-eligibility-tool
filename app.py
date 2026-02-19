import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# PART 1: BRANDING
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

# PART 2: 3-YEAR HISTORICAL FINANCIALS
st.header("1. Applicant Details & 3-Year Financials")
curr_fy = st.selectbox("Select Current Financial Year (Assessment)", ["FY 2024-25", "FY 2025-26"], index=0)
base_year = int(curr_fy.split(" ")[1].split("-")[0])

num_apps = st.number_input("How many applicants (1-10)?", min_value=1, max_value=10, value=1)
total_avg_cash_profit = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} - 3 Year History", expanded=True):
        col_info, col_m = st.columns([1, 1])
        with col_info:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            avg_method = st.radio(f"Avg Method (App {i+1})", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}", horizontal=True)

        years = [f"FY {base_year}-{str(base_year+1)[2:]}", f"FY {base_year-1}-{str(base_year)[2:]}", f"FY {base_year-2}-{str(base_year-1)[2:]}"]
        c1, c2, c3 = st.columns(3)
        annual_cash_flows = []
        
        for idx, yr in enumerate(years):
            with [c1, c2, c3][idx]:
                st.markdown(f"### {yr}")
                npbt = st.number_input(f"NPBT ({yr})", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input(f"Depreciation ({yr})", key=f"dep_{i}_{idx}", value=0.0)
                int_tl_man = st.number_input(f"Manual Interest Add-back ({yr})", key=f"int_{i}_{idx}", value=0.0)
                fam_sal = st.number_input(f"Family Salary ({yr})", key=f"fs_{i}_{idx}", value=0.0)
                curr_rent = st.number_input(f"Current Rent ({yr})", key=f"cr_{i}_{idx}", value=0.0)
                fut_rent = st.number_input(f"Future Rental ({yr})", key=f"fr_{i}_{idx}", value=0.0)
                
                f_dep = min(dep, max(0.0, npbt)) if st.checkbox("Restrict Dep", key=f"re_{i}_{idx}", value=True) else dep
                cash_flow = npbt + f_dep + int_tl_man + fam_sal + curr_rent + fut_rent
                annual_cash_flows.append(cash_flow)
                st.caption(f"Cash Profit: ₹{cash_flow:,.0f}")

        avg_profit = (sum(annual_cash_flows[:2]) / 2) if avg_method == "Latest 2 Years" else (sum(annual_cash_flows) / 3)
        st.success(f"**Average Cash Profit: ₹{avg_profit:,.0f}**")
        total_avg_cash_profit += avg_profit

# PART 3: DETAILED OBLIGATIONS & LOAN ANALYZER
st.divider()
st.header("2. Current Monthly Obligations")
col_obs1, col_obs2 = st.columns(2)
with col_obs1:
    manual_emi = st.number_input("Total Monthly EMIs (Manual Entry)", value=0.0)

if 'loans' not in st.session_state: st.session_state.loans = []
if st.button("➕ Add Detailed Existing Loan"):
    st.session_state.loans.append({"amt": 0.0, "emi": 0.0, "roi": 9.0, "start": date(2021, 4, 1), "closure": date(2030, 3, 31)})

total_detailed_emi = 0.0
total_auto_interest_addback = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"**Detailed Loan {idx+1} Analysis**")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            amt = st.number_input(f"Original Loan Amount", key=f"la_{idx}", value=loan['amt'])
            roi = st.number_input(f"ROI %", key=f"lr_{idx}", value=loan['roi'])
        with l2:
            emi = st.number_input(f"Monthly EMI", key=f"le_{idx}", value=loan['emi'])
            start = st.date_input("Start Date", key=f"ls_{idx}", value=loan['start'])
        with l3:
            closure = st.date_input("Closure Date", key=f"lc_{idx}", value=loan['closure'])
            # RESTORED: Add Interest to Income Toggle
            add_int_to_inc = st.checkbox("Add Interest to Income?", key=f"lab_{idx}", value=True)
        with l4:
            # RESTORED: Obligate EMI Toggle
            is_obligated = st.checkbox("Obligate EMI?", key=f"lob_{idx}", value=True)
            
        if amt > 0 and emi > 0:
            temp_bal = amt
            for y in range(start.year, 2036):
                yr_int = temp_bal * (roi / 100)
                temp_bal = max(0, temp_bal - ((emi * 12) - yr_int))
                # Auto Add-back for the current FY (e.g., 2025)
                if y == base_year and add_int_to_inc:
                    total_auto_interest_addback += yr_int

        if is_obligated and date.today() < closure:
            total_detailed_emi += emi

final_total_emi = manual_emi + total_detailed_emi
st.info(f"Total Monthly Obligation: ₹{final_total_emi:,.0f} | Total Interest Add-back: ₹{total_auto_interest_addback:,.0f}")

# PART 4: FINAL ELIGIBILITY
st.divider()
st.header("3. Bank Policy & Results")
p1, p2, p3 = st.columns(3)
with p1: foir = st.slider("FOIR %", 40, 80, 60)
with p2: n_roi = st.number_input("New Rate %", value=9.5)
with p3: n_ten = st.number_input("New Tenure (Yrs)", value=15)

# Calculation including auto-calculated interest from running loans
final_cash_flow_monthly = ((total_avg_cash_profit + total_auto_interest_addback) / 12)
r_val = (n_roi/12)/100
n_val = n_ten * 12
max_loan = ((final_cash_flow_monthly * (foir / 100)) - final_total_emi) * ((1 - (1 + r_val)**-n_val) / r_val)

if max_loan > 0:
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
else:
    st.error("No eligibility found based on current cash flow and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\n7737306376\nUdaipur, Rajasthan")
