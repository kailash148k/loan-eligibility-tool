import streamlit as st
import pandas as pd
from datetime import date
import json
import os
import io  # New import for file handling

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

# --- PART 2: FINANCIALS ---
st.header("1. Applicant Details & 3-Year Financials")
curr_fy = st.selectbox("Current Assessment FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
base_year = int(curr_fy.split(" ")[1].split("-")[0])

num_apps = st.number_input("How many applicants (1-10)?", 1, 10, 1, key="num_apps")
total_emi_capacity = 0.0
app_details_for_excel = []

for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1}", expanded=True):
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
        app_details_for_excel.append({"Name": name, "Avg Profit": avg_p, "EMI Cap": cap})

# --- PART 3: OBLIGATIONS ---
st.divider()
st.header("2. Current Monthly Obligations")
manual_emi = st.number_input("Manual Total EMI Entry", value=0.0, key="manual_emi")
if 'loans' not in st.session_state: st.session_state.loans = []

if st.button("➕ Add Loan Row"):
    st.session_state.loans.append({"amt": 0.0, "emi": 0.0, "roi": 9.0, "start": date(2021, 4, 1), "closure": date(2030, 3, 31), "add_int": True, "obligate": True})

total_detailed_emi = 0.0
total_auto_int = 0.0
for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        l1, l2, l3, l4 = st.columns(4)
        amt = l1.number_input(f"Loan Amt", key=f"la_{idx}", value=loan['amt'])
        roi = l1.number_input(f"ROI %", key=f"lr_{idx}", value=loan['roi'])
        emi = l2.number_input(f"EMI", key=f"le_{idx}", value=loan['emi'])
        if amt > 0 and emi > 0:
            total_auto_int += (amt * (roi/100)) # Simple annual interest proxy
        if l4.checkbox("Obligate?", key=f"lob_{idx}", value=loan['obligate']):
            total_detailed_emi += emi

total_emi_load = manual_emi + total_detailed_emi
addback_cap = (total_auto_int / 12) * 0.60

# --- PART 4: RESULTS & EXCEL EXPORT ---
st.divider()
st.header("3. Final Results")
n_roi = st.number_input("New Rate %", value=9.5, key="n_roi")
n_ten = st.number_input("New Tenure (Yrs)", value=15, key="n_ten")

max_new_emi = (total_emi_capacity + addback_cap) - total_emi_load

if max_new_emi > 0:
    r, n = (n_roi/12)/100, n_ten * 12
    max_loan = max_new_emi * ((1 - (1 + r)**-n) / r)
    st.success(f"### Maximum Eligible Loan: ₹{max_loan:,.0f}")
    
    # EXCEL EXPORT LOGIC
    report_data = {
        "Summary Item": ["Customer Name", "Total Income EMI Capacity", "Existing EMI Load", "Net EMI Available", "Eligible Loan Amount"],
        "Value": [client_name, round(total_emi_capacity + addback_cap, 2), total_emi_load, round(max_new_emi, 2), round(max_loan, 2)]
    }
    df = pd.DataFrame(report_data)
    
    # Create Buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Eligibility_Summary')
    
    st.download_button(
        label="📥 Download Excel Report",
        data=buffer.getvalue(),
        file_name=f"Loan_Eligibility_{client_name}.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.error("No eligibility found.")
