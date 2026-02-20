import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import os
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Loan Master Pro", layout="wide", page_icon="⚖️")

# --- CUSTOM CSS FOR ENHANCED FONT SIZES (18px+) ---
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    h2 { font-size: 22px !important; margin-top: 15px !important; margin-bottom: 8px !important; color: #1E3A8A; font-weight: bold !important; border-bottom: 2px solid #eee; }
    h3 { font-size: 19px !important; margin-top: 8px !important; margin-bottom: 8px !important; font-weight: bold !important; }
    .stDataFrame div, .stTable td, .stTable th { font-size: 18px !important; }
    label, .stTextInput input, .stSelectbox div, .stNumberInput input { font-size: 18px !important; }
    [data-testid="stSidebar"] { font-size: 18px !important; }
    [data-testid="stVerticalBlock"] > div { padding-top: 0.2rem !important; padding-bottom: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PERMANENT STORAGE ---
DB_FILE = "client_database.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4, default=str)

if 'db' not in st.session_state: st.session_state.db = load_db()

# --- PART 1: BRANDING & SIDEBAR ---
st.title("⚖️ Loan Eligibility Assessment Tool")
st.markdown("**CA KAILASH MALI | 7737306376 | Udaipur**")

with st.sidebar:
    st.header("Profile Management")
    if st.button("🆕 Start New Assessment (Reset)"):
        db_ref = st.session_state.db
        st.session_state.clear()
        st.session_state.db = db_ref
        st.rerun()
    st.divider()
    c_name = st.text_input("Customer Name", key="main_client_name")
    if st.button("💾 Save Customer Profile"):
        if c_name:
            st.session_state.db[c_name] = {k: v for k, v in st.session_state.items() if k != 'db'}
            save_db(st.session_state.db)
            st.success("Saved!")
    
    profiles = ["-- Select --"] + list(st.session_state.db.keys())
    sel = st.selectbox("Load Saved Profile", profiles)
    if st.button("🔄 Load Profile"):
        if sel != "-- Select --":
            data = st.session_state.db[sel]
            db_ref = st.session_state.db
            st.session_state.clear()
            st.session_state.db = db_ref
            for k, v in data.items():
                if isinstance(v, str) and len(v) == 10 and "-" in v:
                    try: st.session_state[k] = date.fromisoformat(v)
                    except: st.session_state[k] = v
                else: st.session_state[k] = v
            st.rerun()

# --- PART 2: ASSESSMENT SETTINGS ---
st.header("1. Assessment Settings")
col_fy, col_apps = st.columns(2)
curr_fy = col_fy.selectbox("Current Assessment FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
num_apps = col_apps.number_input("How many applicants?", 1, 10, 1, key="num_apps")

base_year = int(curr_fy.split(" ")[1].split("-")[0])
target_years = [2022, 2023, 2024, 2025, 2026]

if 'loans' not in st.session_state: st.session_state.loans = []
total_detailed_emi = 0.0
fy_interest_totals = {2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0, 2026: 0.0}

# --- PART 3: LOAN OBLIGATIONS ---
st.header("2. Current Monthly Obligations")
if st.button("➕ Add Detailed Loan Row"):
    st.session_state.loans.append({
        "amt": 1000000.0, "roi": 9.0, "tenure": 120, "start": date(2021, 4, 1),
        "add_int": True, "obligate": True, "is_man": False, "man_val": 0.0
    })

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.subheader(f"Loan Analysis: Row {idx+1}")
        l1, l2, l3, l4 = st.columns(4)
        amt = l1.number_input("Amount", key=f"la_{idx}", value=loan['amt'])
        roi = l1.number_input("ROI %", key=f"lr_{idx}", value=loan['roi'])
        
        is_man = l2.checkbox("Manual EMI?", key=f"lm_check_{idx}", value=loan.get('is_man', False))
        tenure = l2.number_input("Tenure (Mo)", key=f"lt_{idx}", value=loan.get('tenure', 120))
        
        # EMI CALCULATION (ALWAYS RUNS)
        if amt > 0 and roi > 0 and tenure > 0:
            r_rate = (roi / 12) / 100
            system_calc_emi = (amt * r_rate * (1 + r_rate)**tenure) / ((1 + r_rate)**tenure - 1)
        else:
            system_calc_emi = 0.0

        # DISPLAY SYSTEM EMI REGARDLESS OF TOGGLE
        l2.info(f"System EMI: ₹{system_calc_emi:,.0f}")

        start_dt = l3.date_input("Start Date", key=f"ls_{idx}", value=loan['start'])
        mat_dt = start_dt + relativedelta(months=int(tenure))
        st.caption(f"Maturity: {mat_dt.strftime('%d-%m-%Y')}")
        
        if is_man: 
            active_emi = l2.number_input("Enter Manual EMI", key=f"le_man_{idx}", value=loan.get('man_val', 0.0))
        else:
            active_emi = system_calc_emi

        add_int = l4.checkbox("Add Int to Income?", key=f"lab_{idx}", value=loan['add_int'])
        obli = l4.checkbox("Obligate EMI?", key=f"lob_{idx}", value=loan['obligate'])

        if amt > 0 and active_emi > 0:
            bal, sch = amt, []
            for y in range(start_dt.year, mat_dt.year + 1):
                y_i = bal * (roi / 100)
                y_p = (active_emi * 12) - y_i
                if y in target_years:
                    sch.append({"FY": f"{y}-{str(y+1)[2:]}", "Int Paid": round(y_i, 0), "Prin Paid": round(max(0, y_p), 0)})
                    if add_int: fy_interest_totals[y] += y_i
                bal = max(0, bal - y_p)
                if bal <= 0: break
            if sch: st.dataframe(pd.DataFrame(sch), hide_index=True, use_container_width=True)
        if obli and date.today() < mat_dt: total_detailed_emi += active_emi

# --- PART 4: APPLICANT DETAILS ---
st.header("3. Applicant Details & Financials")
total_cap = 0.0
for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1}", expanded=True):
        c_n, c_f, c_a = st.columns([2, 1, 1])
        name = c_n.text_input("Name", key=f"name_{i}")
        foir = c_f.number_input("FOIR %", 10, 100, 60, key=f"foir_{i}")
        meth = c_a.radio("Avg Method", ["2Y", "3Y"], key=f"avg_m_{i}", horizontal=True)

        c1, c2, c3 = st.columns(3)
        flows = []
        for idx in range(3):
            yr_val = base_year - idx
            with [c1, c2, c3][idx]:
                st.markdown(f"**FY {yr_val}-{str(yr_val+1)[2:]}**")
                n_p = st.number_input("NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input("Depreciation", key=f"dep_{i}_{idx}", value=0.0)
                s_i = fy_interest_totals.get(yr_val, 0.0)
                st.caption(f"Interest Sync: ₹{s_i:,.0f}")
                restr = st.checkbox("Restrict Dep", key=f"re_{i}_{idx}", value=True)
                f_d = min(dep, max(0.0, n_p)) if restr else dep
                fl = n_p + f_d + s_i + st.number_input("Manual Add-back", key=f"int_{i}_{idx}", value=0.0)
                flows.append(fl)
        
        avg = (sum(flows[:2])/2) if meth == "2Y" else (sum(flows)/3)
        cap = (avg / 12) * (foir / 100)
        total_cap += cap
        st.write(f"Monthly EMI Capacity: **₹{cap:,.0f}**")

# --- PART 5: FINAL RESULTS ---
st.header("4. Eligibility Results")
man_emi_ext = st.number_input("Other Manual EMIs", value=0.0)
net_emi_final = total_cap - (man_emi_ext + total_detailed_emi)

r_p, t_p = st.columns(2)
new_roi = r_p.number_input("Proposed ROI %", value=9.5)
new_tenure = t_p.number_input("Proposed Tenure (Yrs)", value=15)

if net_emi_final > 0:
    r_v, n_v = (new_roi/12)/100, new_tenure * 12
    eligible_loan = net_emi_final * ((1 - (1 + r_v)**-n_v) / r_v)
    st.success(f"### Maximum Eligible Loan: ₹{eligible_loan:,.0f}")
    
    res_summary = pd.DataFrame({"Metric": ["Net EMI Available", "Eligible Loan"], "Value": [f"{net_emi_final:,.0f}", f"{eligible_loan:,.0f}"]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: res_summary.to_excel(writer, index=False)
    st.download_button("📥 Export to Excel", buf.getvalue(), f"Loan_Eligibility_{c_name}.xlsx")
else: st.error("Obligations exceed FOIR capacity.")
