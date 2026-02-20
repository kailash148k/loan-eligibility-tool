import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import os
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Loan Master Pro", layout="wide", page_icon="⚖️")

# --- COMPACT CSS FOR MINIMAL SPACE ---
st.markdown("""
    <style>
    /* Reduce top padding of the app */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* Main font and small text */
    html, body, [class*="css"] { font-size: 13px !important; }
    
    /* Strict Header Sizing */
    h1 { font-size: 18px !important; margin-bottom: 5px !important; padding-top: 0px !important; }
    h2 { font-size: 15px !important; margin-top: 10px !important; margin-bottom: 5px !important; color: #1E3A8A; font-weight: bold !important; }
    h3 { font-size: 13px !important; margin-top: 5px !important; margin-bottom: 2px !important; font-weight: bold !important; }
    
    /* Shrink spacing between widgets */
    div[data-testid="stVerticalBlock"] > div { padding-top: 0.1rem !important; padding-bottom: 0.1rem !important; }
    
    /* Compact Table/Dataframe */
    .stDataFrame, .stTable { font-size: 12px !important; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { width: 250px !important; }
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
st.title("⚖️ Loan Eligibility Tool")
st.caption("CA KAILASH MALI | Udaipur")

with st.sidebar:
    st.header("Profile Manager")
    if st.button("🆕 New Assessment"):
        db = st.session_state.db
        st.session_state.clear()
        st.session_state.db = db
        st.rerun()
    st.divider()
    c_name = st.text_input("Client Name", key="main_client_name")
    if st.button("💾 Save"):
        if c_name:
            st.session_state.db[c_name] = {k: v for k, v in st.session_state.items() if k != 'db'}
            save_db(st.session_state.db)
            st.success("Saved")
    
    profiles = ["-- Select --"] + list(st.session_state.db.keys())
    sel = st.selectbox("Load Profile", profiles)
    if st.button("🔄 Load"):
        if sel != "-- Select --":
            data = st.session_state.db[sel]
            db = st.session_state.db
            st.session_state.clear()
            st.session_state.db = db
            for k, v in data.items():
                if isinstance(v, str) and len(v) == 10 and "-" in v:
                    try: st.session_state[k] = date.fromisoformat(v)
                    except: st.session_state[k] = v
                else: st.session_state[k] = v
            st.rerun()

# --- PART 2: ASSESSMENT SETTINGS ---
st.header("1. Assessment Settings")
col_fy, col_apps = st.columns(2)
curr_fy = col_fy.selectbox("FY", ["FY 2024-25", "FY 2025-26"], index=0, key="global_fy")
num_apps = col_apps.number_input("No. of Applicants", 1, 10, 1, key="num_apps")

base_year = int(curr_fy.split(" ")[1].split("-")[0])
target_years = [2022, 2023, 2024, 2025, 2026]

if 'loans' not in st.session_state: st.session_state.loans = []
total_detailed_emi = 0.0
fy_interest_totals = {2022: 0.0, 2023: 0.0, 2024: 0.0, 2025: 0.0, 2026: 0.0}

# --- PART 3: LOAN OBLIGATIONS ---
st.header("2. Loan Obligations")
if st.button("➕ Add Loan"):
    st.session_state.loans.append({
        "amt": 1000000.0, "roi": 9.0, "tenure": 120, "start": date(2021, 4, 1),
        "add_int": True, "obligate": True, "is_man": False, "man_val": 0.0
    })

for idx, loan in enumerate(st.session_state.loans):
    with st.container(border=True):
        st.subheader(f"Loan {idx+1}")
        l1, l2, l3, l4 = st.columns(4)
        amt = l1.number_input("Amount", key=f"la_{idx}", value=loan['amt'])
        roi = l1.number_input("ROI %", key=f"lr_{idx}", value=loan['roi'])
        
        is_man = l2.checkbox("Manual EMI?", key=f"lm_check_{idx}", value=loan.get('is_man', False))
        tenure = l2.number_input("Tenure (Mo)", key=f"lt_{idx}", value=loan.get('tenure', 120))
        
        start_dt = l3.date_input("Start", key=f"ls_{idx}", value=loan['start'])
        mat_dt = start_dt + relativedelta(months=int(tenure))
        st.caption(f"Maturity: {mat_dt.strftime('%d-%m-%Y')}")
        
        if is_man: emi_val = l2.number_input("EMI", key=f"le_man_{idx}", value=loan.get('man_val', 0.0))
        else:
            r = (roi / 12) / 100
            emi_val = (amt * r * (1 + r)**tenure) / ((1 + r)**tenure - 1) if amt > 0 and roi > 0 else 0.0
        
        add_int = l4.checkbox("Add Int?", key=f"lab_{idx}", value=loan['add_int'])
        obli = l4.checkbox("Obligate?", key=f"lob_{idx}", value=loan['obligate'])

        if amt > 0 and emi_val > 0:
            bal, sch = amt, []
            for y in range(start_dt.year, mat_dt.year + 1):
                y_i = bal * (roi / 100)
                y_p = (emi_val * 12) - y_i
                if y in target_years:
                    sch.append({"FY": f"{y}-{str(y+1)[2:]}", "Int": round(y_i, 0), "Prin": round(max(0, y_p), 0)})
                    if add_int: fy_interest_totals[y] += y_i
                bal = max(0, bal - y_p)
                if bal <= 0: break
            if sch: st.dataframe(pd.DataFrame(sch), hide_index=True, use_container_width=True)
        if obli and date.today() < mat_dt: total_detailed_emi += emi_val

# --- PART 4: FINANCIALS ---
st.header("3. Applicant Financials")
total_cap = 0.0
for i in range(int(num_apps)):
    with st.expander(f"Applicant {i+1}", expanded=True):
        c_n, c_f, c_a = st.columns([2, 1, 1])
        name = c_n.text_input("Name", key=f"name_{i}")
        foir = c_f.number_input("FOIR %", 10, 100, 60, key=f"foir_{i}")
        meth = c_a.radio("Avg", ["2Y", "3Y"], key=f"avg_m_{i}", horizontal=True)

        c1, c2, c3 = st.columns(3)
        flows = []
        for idx in range(3):
            yr_val = base_year - idx
            with [c1, c2, c3][idx]:
                st.markdown(f"**FY {yr_val}-{str(yr_val+1)[2:]}**")
                n_p = st.number_input("NPBT", key=f"npbt_{i}_{idx}", value=0.0)
                dep = st.number_input("Dep", key=f"dep_{i}_{idx}", value=0.0)
                s_i = fy_interest_totals.get(yr_val, 0.0)
                st.caption(f"Int Sync: {s_i:,.0f}")
                restr = st.checkbox("Restr", key=f"re_{i}_{idx}", value=True)
                f_d = min(dep, max(0.0, n_p)) if restr else dep
                fl = n_p + f_d + s_i + st.number_input("Man.Add", key=f"int_{i}_{idx}", value=0.0)
                flows.append(fl)
        
        avg = (sum(flows[:2])/2) if meth == "2Y" else (sum(flows)/3)
        cap = (avg / 12) * (foir / 100)
        total_cap += cap
        st.write(f"EMI Capacity: **₹{cap:,.0f}**")

# --- PART 5: FINAL ---
st.header("4. Result")
man_emi = st.number_input("Other EMIs", value=0.0)
net_emi = total_cap - (man_emi + total_detailed_emi)

r_p, t_p = st.columns(2)
n_r = r_p.number_input("New ROI %", value=9.5)
n_t = t_p.number_input("New Tenure (Yrs)", value=15)

if net_emi > 0:
    r_v, n_v = (n_r/12)/100, n_t * 12
    max_l = net_emi * ((1 - (1 + r_v)**-n_v) / r_v)
    st.success(f"### Eligibility: ₹{max_l:,.0f}")
    
    res_df = pd.DataFrame({"Item": ["Net EMI", "Loan"], "Value": [f"{net_emi:,.0f}", f"{max_l:,.0f}"]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: res_df.to_excel(writer, index=False)
    st.download_button("📥 Excel", buf.getvalue(), f"Loan_{c_name}.xlsx")
else: st.error("No Eligibility")
