import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Loan Eligibility Master", layout="wide")
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI - 7737306376")

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
age = date.today().year - dob.year
st.caption(f"Age: {age} Years")
applicants.append({"Name": name, "Age": age})

total_annual_profit = 0
for i in range(int(num_apps)):
with st.expander(f"Financials: {applicants[i]['Name'] or f'Applicant {i+1}'}", expanded=True):
c1, c2 = st.columns(2)
with c1:
npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"np{i}")
dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dp{i}")
with c2:
restrict = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", key=f"r{i}")
if restrict:
final_dep = min(dep, max(0.0, npbt))
else:
final_dep = dep
total_annual_profit += (npbt + final_dep)

num_loans = st.number_input("Number of Existing Loans", 0, 5, 0)
total_monthly_obligation = 0

if num_loans > 0:
for j in range(int(num_loans)):
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
l_name = st.text_input(f"Bank Name (Loan {j+1})", key=f"ln{j}")
with col_l2:
emi = st.number_input(f"EMI Amount (Loan {j+1})", value=0.0, key=f"le{j}")
with col_l3:
status = st.selectbox(f"Status (Loan {j+1})", ["Obligated (Running)", "To be Closed"], key=f"ls{j}")
if status == "Obligated (Running)":
total_monthly_obligation += emi

foir = st.slider("FOIR % (Bank Policy)", 40, 80, 60)
monthly_income = total_annual_profit / 12
max_allowed_emi = (monthly_income * (foir / 100)) - total_monthly_obligation

st.divider()
col_res1, col_res2 = st.columns(2)
with col_res1:
st.metric("Total Monthly Cash Profit", f"₹{monthly_income:,.2f}")
st.metric("Existing EMI Deducted", f"₹{total_monthly_obligation:,.2f}")
with col_res2:
st.metric("Max New EMI Allowed", f"₹{max_allowed_emi:,.2f}")

roi = st.number_input("Interest Rate (%)", value=9.5)
tenure = st.number_input("Tenure (Years)", value=15)
r = (roi / 12) / 100
n = tenure * 12
if r > 0:
max_loan = max_allowed_emi * ((1 - (1 + r)**-n) / r)
else:
max_loan = max_allowed_emi * n

if max_loan > 0:
st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")
else:
st.error("Not eligible for a new loan based on FOIR.")

st.sidebar.markdown(f"CA KAILASH MALI\n7737306376")
