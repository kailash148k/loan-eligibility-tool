import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Loan Eligibility Master", layout="wide")

--- PART 1: BRANDING ---
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI | 7737306376 | Udaipur")

--- PART 2: APPLICANT DETAILS ---
st.header("1. Applicant Information")
col_a, col_b = st.columns(2)
with col_a:
name1 = st.text_input("Primary Applicant Name", "Applicant 1")
dob1 = st.date_input("DOB (App 1)", date(1990, 1, 1))
age1 = date.today().year - dob1.year
with col_b:
name2 = st.text_input("Co-Applicant Name", "Applicant 2")
dob2 = st.date_input("DOB (App 2)", date(1995, 1, 1))
age2 = date.today().year - dob2.year

--- PART 3: JOINT CASH PROFIT (CA LOGIC) ---
st.header("2. Income & Cash Profit Analysis")
c1, c2 = st.columns(2)
with c1:
st.write(f"{name1} Financials")
npbt1 = st.number_input("NPBT (App 1)", value=0.0)
dep1 = st.number_input("Depreciation (App 1)", value=0.0)
res1 = st.checkbox("Restrict Dep to NPBT (App 1)", value=True)
f_dep1 = min(dep1, max(0.0, npbt1)) if res1 else dep1
income1 = npbt1 + f_dep1
with c2:
st.write(f"{name2} Financials")
npbt2 = st.number_input("NPBT (App 2)", value=0.0)
dep2 = st.number_input("Depreciation (App 2)", value=0.0)
res2 = st.checkbox("Restrict Dep to NPBT (App 2)", value=True)
f_dep2 = min(dep2, max(0.0, npbt2)) if res2 else dep2
income2 = npbt2 + f_dep2

total_monthly_income = (income1 + income2) / 12

--- PART 4: EXISTING OBLIGATIONS ---
st.header("3. Existing Obligations")
running_emi = st.number_input("Total Monthly EMI of All Running Loans", value=0.0)
st.caption("Note: Do not include loans that will be closed before this new disbursement.")

--- PART 5: BANK POLICY (FOIR & ROI) ---
st.header("4. Bank Policy Parameters")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
foir = st.slider("FOIR %", 40, 80, 60)
with col_p2:
roi = st.number_input("Interest Rate (%)", value=9.5)
with col_p3:
tenure = st.number_input("Tenure (Years)", value=14)

max_emi_allowed = (total_monthly_income * (foir / 100)) - running_emi

--- PART 6: RESULTS & 14-YEAR SCHEDULE ---
st.divider()
st.header("5. Final Eligibility Result")

if max_emi_allowed > 0:
r = (roi / 12) / 100
n = tenure * 12
max_loan = max_emi_allowed * ((1 - (1 + r)**-n) / r)

else:
st.error("Applicant is not eligible based on current FOIR and Obligations.")

st.sidebar.markdown(f"CA KAILASH MALI\nUdaipur | 7737306376")
