import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Loan Eligibility Master", layout="wide")
st.title("⚖️ Loan Eligibility Assessment Tool")
st.subheader("CA KAILASH MALI - 7737306376")

num_apps = st.number_input("Number of Applicants", 1, 4, 1)
total_annual_profit = 0.0

for i in range(int(num_apps)):
st.markdown(f"---")
st.write(f"### Applicant {i+1}")
name = st.text_input(f"Name (App {i+1})", key=f"name{i}")
c1, c2, c3 = st.columns(3)
with c1:
npbt = st.number_input(f"NPBT (App {i+1})", value=0.0, key=f"np{i}")
with c2:
dep = st.number_input(f"Depreciation (App {i+1})", value=0.0, key=f"dp{i}")
with c3:
res = st.checkbox(f"Restrict Dep to NPBT (App {i+1})", key=f"r{i}")
sal = st.number_input(f"Salary/Rent (App {i+1})", value=0.0, key=f"s{i}")

st.markdown(f"---")
num_loans = st.number_input("Number of Existing Loans", 0, 5, 0)
total_emi = 0.0

if num_loans > 0:
for j in range(int(num_loans)):
cl1, cl2, cl3 = st.columns(3)
with cl1:
l_bank = st.text_input(f"Bank {j+1}", key=f"lb{j}")
with cl2:
l_emi = st.number_input(f"EMI {j+1}", value=0.0, key=f"le{j}")
with cl3:
status = st.selectbox(f"Status (Loan {j+1})", ["Running", "To be Closed"], key=f"ls{j}")
if status == "Running":
total_emi += l_emi

st.markdown(f"---")
foir = st.slider("FOIR %", 40, 80, 60)
roi = st.number_input("Interest Rate (%)", value=9.5)
tenure = st.number_input("Tenure (Years)", value=14)

monthly_income = total_annual_profit / 12
max_emi = (monthly_income * (foir / 100)) - total_emi

st.divider()
res_col1, res_col2 = st.columns(2)
with res_col1:
st.metric("Total Monthly Profit", f"₹{monthly_income:,.2f}")
st.metric("Existing Obligations", f"₹{total_emi:,.2f}")
with res_col2:
st.metric("Eligible New EMI", f"₹{max_emi:,.2f}")

r = (roi / 12) / 100
n = tenure * 12
if r > 0 and max_emi > 0:
max_loan = max_emi * ((1 - (1 + r)**-n) / r)
st.success(f"### Maximum Eligible Loan Amount: ₹{max_loan:,.0f}")

else:
st.error("No eligibility based on current financials.")

st.sidebar.markdown(f"CA KAILASH MALI\n7737306376")
