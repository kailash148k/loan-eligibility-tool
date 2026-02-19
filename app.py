import streamlit as st
import pandas as pd
from datetime import date

Basic Page Config
st.set_page_config(page_title="Loan Eligibility Master", layout="wide")

Header with your Branding
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI - 7737306376")

PART 6: APPLICANT DEMOGRAPHICS
st.header("1. Applicant Details")
num_apps = st.number_input("Total Number of Applicants", 1, 4, 1)
applicants = []

for i in range(int(num_apps)):
col1, col2, col3 = st.columns(3)
with col1:
name = st.text_input(f"Applicant {i+1} Name", key=f"n{i}")
with col2:
pan = st.text_input(f"PAN (App {i+1})", key=f"p{i}")
with col3:
dob = st.date_input(f"DOB (App {i+1})", date(1990, 1, 1), key=f"d{i}")
age = date.today().year - dob.year - ((date.today().month, date.today().day) < (dob.month, dob.day))
st.caption(f"Calculated Age: {age} Years")
applicants.append({"Name": name, "Age": age})

st.divider()

PART 1: JOINT CASH PROFIT (With your specific CA Logic)
st.header("2. Joint Income & Cash Profit Analysis")
total_annual_profit = 0

for i in range(int(num_apps)):
with st.expander(f"Financials: {applicants[i]['Name'] or f'Applicant {i+1}'}", expanded=True):
c1, c2, c3 = st.columns(3)
with c1:
npbt = st.number_input(f"NPBT", key=f"np{i}", value=0.0)
sal = st.number_input(f"Salary/Rent", key=f"s{i}", value=0.0)
with c2:
dep = st.number_input(f"Depreciation", key=f"dp{i}", value=0.0)
restrict = st.checkbox("Restrict Dep. to 100% of NPBT", key=f"r{i}")

st.divider()

PART 4 & 5: ELIGIBILITY CALCULATION
st.header("3. Final Loan Eligibility")
monthly_avg_profit = total_annual_profit / 12

col_res1, col_res2 = st.columns(2)
with col_res1:
foir = st.slider("FOIR % (Bank Limit)", 40, 80, 60)
max_emi = monthly_avg_profit * (foir / 100)
st.metric("Max Allowed EMI", f"₹{max_emi:,.2f}")

with col_res2:
roi = st.number_input("Proposed Interest Rate (%)", value=9.5)
tenure = st.number_input("Tenure (Years)", value=15)

Sidebar
st.sidebar.markdown(f"Firm: Rajasthan MSME Subsidy Comparison Tool")
st.sidebar.markdown(f"CA KAILASH MALI")
st.sidebar.markdown(f"📞 7737306376")
