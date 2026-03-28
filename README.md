# MindBridge Wellness Clinic: MIS Dashboard 

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

An end-to-end Data Analytics portfolio project demonstrating Python-driven data engineering, automated Excel reporting, PDF business insights, and advanced SQL analytics for a mental health clinic.

## 📖 Problem Statement
In the rapidly growing mental health-tech sector, clinical directors and operations managers struggle to consolidate data from disparate booking, billing, and clinical systems. A unified Management Information System (MIS) reporting pipeline is essential to track therapist performance, monitor patient dropout rates, and manage session revenues efficiently. This project automates the entire data lifecycle from generation to final executive reporting.

## ⚙️ Tech Stack
- **Data Engineering**: Python (`pandas`, `numpy`, `faker`)
- **Automated Reporting**: Python (`openpyxl`, `reportlab`)
- **Analytics Engine**: SQLite
- **Visualization Integration**: Power BI Ready Export

## 📁 Project Structure
```text
mentalhealth/
├── data/
│   ├── raw/                 # Generated synthetic data with intentional quality issues
│   └── cleaned/             # Data post-ETL processing
├── output/
│   ├── MIS_Weekly_Report.xlsx       # Automated Multi-sheet Excel Dashboard
│   ├── Business_Insights_Report.pdf # Executive Summary PDF
│   └── powerbi_export.csv           # Formatted flat file for Power BI
├── scripts/
│   ├── generate_data.py          # Synthetic data generator
│   ├── clean_data.py             # ETL and data validation script
│   ├── generate_excel_report.py  # Excel report generator (openpyxl)
│   └── generate_pdf_report.py    # Business insight generator (reportlab)
├── sql/
│   └── queries.sql               # 10 advanced business intelligence queries
├── README.md
└── requirements.txt
```

## 🚀 How to Run
To reproduce the entire pipeline locally, follow these steps:

1. **Clone the repository** (or download the files).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the pipeline in order**:
   ```bash
   python scripts/generate_data.py
   python scripts/clean_data.py
   python scripts/generate_excel_report.py
   python scripts/generate_pdf_report.py
   ```
4. View the generated reports in the `output/` folder and explore SQL analytics in `sql/queries.sql`.

## Running the Dashboard
To launch the interactive Python Streamlit dashboard:
1. `pip install -r requirements.txt`
2. `python -m streamlit run app.py`
3. The dashboard will automatically open at `http://localhost:8501`

## 💡 Key Insights
- **Revenue Leakage**: A significant portion of revenue remains uncollected due to pending payments within the Addiction Recovery and Trauma & PTSD departments.
- **Therapist Utilization**: Top-performing therapists consistently maintain attendance rates above 90%, highlighting an opportunity to formalize their patient engagement techniques across the clinic.
- **Geographic Patterns**: Patient attendance is notably higher for specific operational hubs, suggesting that local clinical campaigns might yield better retention than broader regional approaches.

## 📊 Power BI Dashboard
**To build the visual dashboard:** Import `output/powerbi_export.csv` into Power BI Desktop. 

**Suggested Visuals & Page Structure:**

* **Page 1: Executive Overview**
  - KPI Cards: Total Revenue, Total Appointments, Avg Wait Time, Avg Satisfaction.
  - Line Chart: Revenue by Month (`appointment_date`, `revenue`).
  - Donut Chart: Overall Attendance Rate (`attended`).

* **Page 2: Department & Therapist Analysis**
  - Clustered Bar Chart: Total Appointments by Department (`department`, count of `patient_id`).
  - Matrix Table: Therapist Performance (`therapist_name`, avg of `satisfaction_score`, sum of `revenue`).
  - Stacked Column Chart: Attendance by Department (`department`, `attended`).

* **Page 3: Patient Demographics**
  - Donut Chart: Patient Gender Distribution (`patient_gender`).
  - Ribbon Chart: Age Group Distribution over time (`age_group`, `appointment_date`).
  - Filled Map: Appointments geographic spread (`city`).

* **Page 4: Financial Summary**
  - Waterfall Chart: Revenue by Month (`appointment_date`, `revenue`).
  - Pie Chart: Payment Status Breakdown (`payment_status`).

---
*Created by [Your Name] – Data Analyst Internship Portfolio Project*
