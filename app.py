import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
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
        except: return {}
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

# --- PART 2: GLOBAL SETTINGS & LOAN CALCULATIONS (PRE-CALC FOR ADD-BACK) ---
st.header("1. Assessment Settings")
curr_fy = st.selectbox("Current Assessment FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
base_year = int(curr_fy.split(" ")[1].split("-")[0])
target_years = [2022, 2023, 2024, 2025, 2026]

# Prepare variables for Loan Calculations
if 'loans' not in st.session_state: st.session_state.loans = []
total_detailed_emi = 0.0
# We use a dictionary to store interest add-back per FY to show in Financials later
fy_interest_totals = {2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0, 2026: 0.0}

# --- PART 3: LOAN OBLIGATIONS (CALCULATED FIRST TO SYNC DATA) ---
st.divider()
st.header("2. Current Monthly Obligations")
if st.button("➕ Add Detailed Loan Row"):
    st.session_state.loans.append({
        "amt": 1000000.0, "roi": 9.0, "tenure_months": 120,
        "start": date(2021, 4, 1), "pre_closure": None,
        "add_int": True, "obligate": True, "is_manual": False, "manual_emi_val": 0.0
    })

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.subheader(f"Loan Analysis: Row {idx+1}")
        l1, l2, l3, l4 = st.columns(4)
        
        amt = l1.number_input(f"Loan Amount", key=f"la_{idx}", value=loan['amt'])
        roi = l1.number_input(f"ROI %", key=f"lr_{idx}", value=loan['roi'])
        
        is_manual = l2.checkbox("Manual EMI Entry?", key=f"lm_check_{idx}", value=loan.get('is_manual', False))
        tenure_mo = l2.number_input(f"Tenure (Months)", key=f"lt_{idx}", value=loan.get('tenure_months', 120))
        
        start_dt = l3.date_input("Start Date", key=f"ls_{idx}", value=loan['start'])
        # Auto-calculate maturity
        maturity_dt = start_dt + relativedelta(months=int(tenure_mo))
        l3.info(f"Maturity Date: {maturity_dt.strftime('%d-%m-%Y')}")
        
        pre_closure = l3.date_input("Pre-closure Date (Optional)", key=f"lpc_{idx}", value=None if loan.get('pre_closure') == "None" else loan.get('pre_closure'))
        final_end_date = pre_closure if pre_closure else maturity_dt

        if is_manual:
            active_emi = l2.number_input(f"Enter Exact EMI", key=f"le_man_{idx}", value=loan.get('manual_emi_val', 0.0))
        else:
            if amt > 0 and roi > 0 and tenure_mo > 0:
                r = (roi / 12) / 100
                active_emi = (amt * r * (1 + r)**tenure_mo) / ((1 + r)**tenure_mo - 1)
                l2.info(f"Calc EMI: ₹{active_emi:,.0f}")
            else: active_emi = 0.0

        add_int_check = l4.checkbox("Add Int to Income?", key=f"lab_{idx}", value=loan['add_int'])
        obligate_check = l4.checkbox("Obligate EMI?", key=f"lob_{idx}", value=loan['obligate'])

        if amt > 0 and active_emi > 0:
            temp_bal = amt
            schedule = []
            for y in range(start_dt.year, final_end_date.year + 1):
                yr_int = temp_bal * (roi / 100)
                yr_prin = (active_emi * 12) - yr_int
                
                if y in target_years:
                    schedule.append({
                        "Financial Year": f"FY {y}-{str(y+1)[2:]}",
                        "Interest": round(yr_int, 2),
                        "Principal": round(max(0, yr_prin), 2)
                    })
                    if add_int_check:
                        fy_interest_totals[y] += yr_int
                
                temp_bal = max(0, temp_bal - yr_prin)
                if temp_bal == 0: break
            
            if schedule: st.table(pd.DataFrame(schedule))

        if obligate_check and date.today() < final_end_date:
            total_detailed_emi += active_emi

# --- PART 4: APPLICANT DETAILS (NOW SHOWING SYNCED INTEREST) ---
st.divider()
st.header("3. Applicant Details & Financials")
num_apps = st.number_input("How many applicants (1-10)?", 1, 10, 1, key="num_apps")
total_emi_capacity = 0.0

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1} Details", expanded=True):
        c_n, c_f = st.columns([2, 1])
        name = c_n.text_input(f"Name", key=f"name_{i}")
        foir = c_f.number_input(f"FOIR %", 10, 100, 60, key=f"foir_{i}")
        avg_m = st.radio(f"Avg Method", ["Latest 2 Years", "Latest 3 Years"], key=f"avg_m_{i}", horizontal=True)

        years_display = [f"FY {base_year}-{str(base_year+1)[2:]}", f"FY {base_year-1}-{str(base_year)[2:]}", f"FY {base_year-2}-{str(base_year-1)[2:]}"]
        c1, c2, c3 = st.columns(3)
        annual_flows = []
        
        for idx, yr_label in enumerate(years_display):
            y_int = int(yr_label.split(" ")[1].split("-")[0])
            with [c1, c2, c3][idx]:
                st.markdown(f"**{yr_label}**")
                n = st.number_input(f"NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                d = st.number_input(f"Depreciation", key=f"dep_{i}_{idx}", value=0.0)
                
                # SHOW AUTO-CALCULATED INTEREST HERE
                auto_int = fy_interest_totals.get(y_int, 0.0)
                st.write(f"Synced Loan Int: ₹{auto_int:,.2f}")
                
                man_add = st.number_input(f"Manual Add-back", key=f"int_{i}_{idx}", value=0.0)
                
                f_d = min(d, max(0.0, n)) if st.checkbox("Restrict Dep", key=f"re_{i}_{idx}", value=True) else d
                flow = n + f_d + auto_int + man_add
                annual_flows.append(flow)
                st.caption(f"Total Cash Flow: ₹{flow:,.0f}")

        avg_p = (sum(annual_flows[:2])/2) if avg_m == "Latest 2 Years" else (sum(annual_flows)/3)
        cap = (avg_p / 12) * (foir / 100)
        total_emi_capacity += cap
        st.success(f"Monthly EMI Capacity for {name if name else 'Applicant'}: ₹{cap:,.0f}")

# --- PART 5: RESULTS ---
st.divider()
st.header("4. Final Results")
manual_emi_global = st.number_input("Other Manual EMIs", value=0.0)
total_load = manual_emi_global + total_detailed_emi

p1, p2 = st.columns(2)
n_roi = p1.number_input("Proposed Rate %", value=9.5)
n_ten = p2.number_input("Proposed Tenure (Yrs)", value=15)

max_new_emi = total_emi_capacity - total_load

if max_new_emi > 0:
    r, n = (n_roi/12)/100, n_ten * 12
    max_loan = max_new_emi * ((1 - (1 + r)**-n) / r)
    st.balloons()
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    st.info(f"Total Capacity: ₹{total_emi_capacity:,.0f} | Existing Load: ₹{total_load:,.0f}")
else:
    st.error("No eligibility - Obligations exceed FOIR capacity.")
