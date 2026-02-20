import streamlit as st
import pandas as pd
from datetime import date
import json
import os
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Loan Master Pro", layout="wide", page_icon="⚖️")

# --- PERMANENT STORAGE LOGIC ---
DB_FILE = "client_database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- PART 1: BRANDING & SIDEBAR ---
st.title("⚖️ Loan Eligibility Assessment Tool")
st.markdown("#### CA KAILASH MALI | 7737306376 | Udaipur")

st.sidebar.header("📁 Client Profile Management")

if st.sidebar.button("🆕 Start New Assessment (Reset)"):
    current_db = st.session_state.db
    st.session_state.clear()
    st.session_state.db = current_db
    st.rerun()

st.sidebar.divider()
client_name = st.sidebar.text_input("Customer Name", placeholder="e.g. Rajesh Kumar")

if st.sidebar.button("💾 Save Customer Profile"):
    if client_name:
        current_data = {k: v for k, v in st.session_state.items() if k != 'db'}
        st.session_state.db[client_name] = current_data
        save_db(st.session_state.db)
        st.sidebar.success(f"Profile '{client_name}' saved!")
    else:
        st.sidebar.error("Enter a name to save.")

saved_profiles = list(st.session_state.db.keys())
selected_profile = st.sidebar.selectbox("📂 Load Saved Profile", ["-- Select --"] + saved_profiles)

if st.sidebar.button("🔄 Load Profile"):
    if selected_profile != "-- Select --":
        profile_data = st.session_state.db[selected_profile]
        current_db = st.session_state.db
        st.session_state.clear()
        st.session_state.db = current_db
        for k, v in profile_data.items():
            if isinstance(v, str) and len(v) == 10 and v.count("-") == 2:
                try: st.session_state[k] = date.fromisoformat(v)
                except: st.session_state[k] = v
            else: st.session_state[k] = v
        st.rerun()

# --- PART 2: APPLICANT FINANCIALS ---
st.header("1. Applicant Details & 3-Year Financials")
curr_fy = st.selectbox("Current Assessment FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
base_year = int(curr_fy.split(" ")[1].split("-")[0])

num_apps = st.number_input("How many applicants (1-10)?", 1, 10, 1, key="num_apps")
total_emi_capacity = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Financials", expanded=False):
        c_n, c_f = st.columns([2, 1])
        name = c_n.text_input(f"Name", key=f"name_{i}")
        foir = c_f.number_input(f"FOIR %", 10, 100, 60, key=f"foir_{i}")
        avg_m = st.radio(f"Avg Method", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}", horizontal=True)

        c1, c2, c3 = st.columns(3)
        annual_flows = []
        for idx in range(3):
            with [c1, c2, c3][idx]:
                n = st.number_input(f"NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                d = st.number_input(f"Dep", key=f"dep_{i}_{idx}", value=0.0)
                f_d = min(d, max(0.0, n)) if st.checkbox("Restrict Dep", key=f"re_{i}_{idx}", value=True) else d
                flow = n + f_d + st.number_input(f"Other Add-back", key=f"int_{i}_{idx}", value=0.0)
                annual_flows.append(flow)

        avg_p = (sum(annual_flows[:2])/2) if avg_m == "Latest 2 Years" else (sum(annual_flows)/3)
        cap = (avg_p / 12) * (foir / 100)
        total_emi_capacity += cap

# --- PART 3: OBLIGATIONS & DYNAMIC EMI ---
st.divider()
st.header("2. Current Monthly Obligations")
manual_emi_global = st.number_input("Manual Total EMI Entry (Non-detailed)", value=0.0, key="manual_emi")

if 'loans' not in st.session_state: st.session_state.loans = []
if st.button("➕ Add Detailed Loan Row"):
    st.session_state.loans.append({
        "amt": 1000000.0, "roi": 9.0, "tenure_months": 120,
        "start": date(2021, 4, 1), "closure": date(2030, 3, 31),
        "add_int": True, "obligate": True, "is_manual": False, "manual_emi_val": 0.0
    })

total_detailed_emi = 0.0
total_auto_int_addback = 0.0
target_years = [2022, 2023, 2024, 2025, 2026]

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.subheader(f"Loan Analysis: Row {idx+1}")
        l1, l2, l3, l4 = st.columns(4)
        
        # Inputs
        amt = l1.number_input(f"Loan Amount", key=f"la_{idx}", value=loan['amt'])
        roi = l1.number_input(f"ROI % (Annual)", key=f"lr_{idx}", value=loan['roi'])
        
        # EMI Toggle Logic
        is_manual = l2.checkbox("Manual EMI Entry?", key=f"lm_check_{idx}", value=loan.get('is_manual', False))
        
        if is_manual:
            active_emi = l2.number_input(f"Enter Exact EMI", key=f"le_man_{idx}", value=loan.get('manual_emi_val', 0.0))
        else:
            tenure = l2.number_input(f"Tenure (Months)", key=f"lt_{idx}", value=loan.get('tenure_months', 120))
            # PMT Formula for Auto EMI
            if amt > 0 and roi > 0 and tenure > 0:
                r = (roi / 12) / 100
                active_emi = (amt * r * (1 + r)**tenure) / ((1 + r)**tenure - 1)
                l2.info(f"Calculated EMI: ₹{active_emi:,.2f}")
            else:
                active_emi = 0.0

        start_dt = l3.date_input("Start Date", key=f"ls_{idx}", value=loan['start'])
        closure_dt = l3.date_input("Closure Date", key=f"lc_{idx}", value=loan['closure'])
        add_int_check = l4.checkbox("Add Int to Income?", key=f"lab_{idx}", value=loan['add_int'])
        obligate_check = l4.checkbox("Obligate EMI?", key=f"lob_{idx}", value=loan['obligate'])

        # Amortization Table
        if amt > 0 and active_emi > 0:
            schedule = []
            temp_bal = amt
            for y in range(start_dt.year, 2030):
                yr_int = temp_bal * (roi / 100)
                yr_prin = (active_emi * 12) - yr_int
                
                if y in target_years:
                    schedule.append({
                        "Financial Year": f"FY {y}-{str(y+1)[2:]}",
                        "Interest Paid": round(yr_int, 2),
                        "Principal Paid": round(max(0, yr_prin), 2),
                        "Closing Balance": round(max(0, temp_bal - yr_prin), 2)
                    })
                
                if y == base_year and add_int_check:
                    total_auto_int_addback += yr_int
                
                temp_bal = max(0, temp_bal - yr_prin)
                if temp_bal == 0: break

            if schedule:
                st.table(pd.DataFrame(schedule))

        if obligate_check and date.today() < closure_dt:
            total_detailed_emi += active_emi

total_emi_load = manual_emi_global + total_detailed_emi
addback_cap = (total_auto_int_addback / 12) * 0.60

# --- PART 4: RESULTS ---
st.divider()
st.header("3. Final Results")
n_roi = st.number_input("New Rate %", value=9.5, key="n_roi")
n_ten = st.number_input("New Tenure (Yrs)", value=15, key="n_ten")

max_new_emi = (total_emi_capacity + addback_cap) - total_emi_load

if max_new_emi > 0:
    r, n = (n_roi/12)/100, n_ten * 12
    max_loan = max_new_emi * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    
    # Simple Excel Summary
    report_data = {"Metric": ["Customer", "Total EMI Cap", "EMI Load", "Net Available", "Loan Eligibility"],
                   "Value": [client_name, f"{total_emi_capacity + addback_cap:,.0f}", f"{total_emi_load:,.0f}", f"{max_new_emi:,.0f}", f"{max_loan:,.0f}"]}
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        pd.DataFrame(report_data).to_excel(writer, index=False)
    st.download_button("📥 Export to Excel", data=buffer.getvalue(), file_name=f"Loan_{client_name}.xlsx")
else:
    st.error("No eligibility based on FOIR/Obligations.")
