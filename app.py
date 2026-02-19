import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CA Loan Master Pro", layout="wide")

# --- DATABASE INITIALIZATION ---
if 'db' not in st.session_state:
    st.session_state.db = {}

# --- PART 1: BRANDING & SIDEBAR SAVING ---
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

st.sidebar.header("📁 Client Profile Management")
client_name = st.sidebar.text_input("Customer Name", placeholder="e.g. Kailash Mali")

if st.sidebar.button("💾 Save Customer Profile"):
    if client_name:
        # Saving all session state for this client
        st.session_state.db[client_name] = {k: v for k, v in st.session_state.items() if k != 'db'}
        st.sidebar.success(f"Profile for '{client_name}' saved!")
    else:
        st.sidebar.error("Please enter a name first.")

saved_profiles = list(st.session_state.db.keys())
selected_profile = st.sidebar.selectbox("📂 Load Saved Profile", ["-- Select --"] + saved_profiles)

if st.sidebar.button("🔄 Load Profile"):
    if selected_profile != "-- Select --":
        profile_data = st.session_state.db[selected_profile]
        for k, v in profile_data.items():
            st.session_state[k] = v
        st.rerun()

# --- PART 2: 3-YEAR FINANCIALS & INDIVIDUAL FOIR ---
st.header("1. Applicant Details & 3-Year Financials")
curr_fy = st.selectbox("Current Assessment FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
base_year = int(curr_fy.split(" ")[1].split("-")[0])

num_apps = st.number_input("How many applicants (1-10)?", 1, 10, 1, key="num_apps")
total_emi_capacity = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} - Financials & FOIR", expanded=True):
        col_name, col_foir = st.columns([2, 1])
        with col_name:
            st.text_input(f"Name (App {i+1})", key=f"name_{i}")
            avg_m = st.radio(f"Avg Method (App {i+1})", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}", horizontal=True)
        with col_foir:
            app_foir = st.number_input(f"FOIR % (App {i+1})", 10, 100, 60, key=f"foir_{i}")

        years = [f"FY {base_year}-{str(base_year+1)[2:]}", f"FY {base_year-1}-{str(base_year)[2:]}", f"FY {base_year-2}-{str(base_year-1)[2:]}"]
        c1, c2, c3 = st.columns(3)
        annual_cash_flows = []
        
        for idx, yr in enumerate(years):
            with [c1, c2, c3][idx]:
                st.markdown(f"### {yr}")
                npbt = st.number_input(f"NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input(f"Depreciation", key=f"dep_{i}_{idx}", value=0.0)
                int_tl_man = st.number_input(f"Manual Int Add-back", key=f"int_{i}_{idx}", value=0.0)
                fam_sal = st.number_input(f"Family Salary", key=f"fs_{i}_{idx}", value=0.0)
                curr_rent = st.number_input(f"Current Rent", key=f"cr_{i}_{idx}", value=0.0)
                fut_rent = st.number_input(f"Future Rent", key=f"fr_{i}_{idx}", value=0.0)
                
                f_dep = min(dep, max(0.0, npbt)) if st.checkbox("Restrict Dep", key=f"re_{i}_{idx}", value=True) else dep
                cash_flow = npbt + f_dep + int_tl_man + fam_sal + curr_rent + fut_rent
                annual_cash_flows.append(cash_flow)

        avg_profit = (sum(annual_cash_flows[:2])/2) if avg_m == "Latest 2 Years" else (sum(annual_cash_flows)/3)
        cap = (avg_profit / 12) * (app_foir / 100)
        total_emi_capacity += cap
        st.success(f"Monthly EMI Capacity for App {i+1}: ₹{cap:,.0f}")

# --- PART 3: OBLIGATIONS & INTEREST ADD-BACK ---
st.divider()
st.header("2. Current Monthly Obligations & Detailed Loan Analysis")
manual_emi = st.number_input("Manual Total EMI Entry (Non-detailed)", value=0.0, key="manual_emi")

if 'loans' not in st.session_state: 
    st.session_state.loans = []

def add_loan():
    # FIX: Explicitly initialize all keys including 'start' to prevent KeyError
    st.session_state.loans.append({
        "amt": 0.0, 
        "emi": 0.0, 
        "roi": 9.0, 
        "start": date(2021, 4, 1), 
        "closure": date(2030, 3, 31),
        "add_int": True,
        "obligate": True
    })

if st.button("➕ Add Detailed Loan"):
    add_loan()

total_detailed_emi = 0.0
total_auto_interest_addback = 0.0

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.write(f"**Detailed Loan {idx+1}**")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            amt = st.number_input(f"Original Loan Amount", key=f"la_{idx}", value=loan['amt'])
            roi = st.number_input(f"ROI %", key=f"lr_{idx}", value=loan['roi'])
        with l2:
            emi = st.number_input(f"Monthly EMI", key=f"le_{idx}", value=loan['emi'])
            start_dt = st.date_input("Start Date", key=f"ls_{idx}", value=loan['start'])
        with l3:
            closure_dt = st.date_input("Closure Date", key=f"lc_{idx}", value=loan['closure'])
            add_int_check = st.checkbox("Add Interest to Income?", key=f"lab_{idx}", value=loan['add_int'])
        with l4:
            obligate_check = st.checkbox("Obligate EMI?", key=f"lob_{idx}", value=loan['obligate'])

        if amt > 0 and emi > 0:
            temp_bal = amt
            for y in range(start_dt.year, 2036):
                yr_int = temp_bal * (roi / 100)
                temp_bal = max(0, temp_bal - ((emi * 12) - yr_int))
                if y == base_year and add_int_check:
                    total_auto_interest_addback += yr_int

        if obligate_check and date.today() < closure_dt:
            total_detailed_emi += emi

total_emi_load = manual_emi + total_detailed_emi
# Convert yearly interest add-back to monthly and apply a standard 60% FOIR for the add-back capacity
monthly_addback_cap = (total_auto_interest_addback / 12) * 0.60

# --- PART 4: FINAL ELIGIBILITY ---
st.divider()
st.header("3. Bank Policy & Results")
p1, p2, p3 = st.columns(3)
with p1: n_roi = st.number_input("New Rate %", value=9.5, key="n_roi")
with p2: n_ten = st.number_input("New Tenure (Yrs)", value=15, key="n_ten")

# Combine base capacity + interest add-back capacity - current obligations
max_new_emi = (total_emi_capacity + monthly_addback_cap) - total_emi_load



if max_new_emi > 0:
    r_rate = (n_roi/12)/100
    n_months = n_ten * 12
    max_loan = max_new_emi * ((1 - (1 + r_rate)**-n_months) / r_rate)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    st.info(f"Total Yearly Int. Add-back from Running Loans: ₹{total_auto_interest_addback:,.0f}")
else:
    st.error("No eligibility found based on FOIR and obligations.")

st.sidebar.markdown(f"**CA KAILASH MALI**\nUdaipur, Rajasthan")
