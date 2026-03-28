import pandas as pd
import xlsxwriter
import os

# Paths
PROCESSED_DATA_PATH = "data/processed/cleaned_clinic_data.csv"
REPORT_PATH = "reports/Clinic_MIS_Full_Dashboard.xlsx"

def generate_excel_report():
    if not os.path.exists(PROCESSED_DATA_PATH):
        print("Processed data not found. Run cleaning script first.")
        return

    df = pd.read_csv(PROCESSED_DATA_PATH)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create Excel writer
    writer = pd.ExcelWriter(REPORT_PATH, engine='xlsxwriter')
    workbook = writer.book
    
    # --- Formats ---
    header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
    num_format = workbook.add_format({'num_format': '#,##0', 'border': 1})
    currency_format = workbook.add_format({'num_format': '$#,##0', 'border': 1})
    pct_format = workbook.add_format({'num_format': '0%', 'border': 1})

    # --- 1. Executive Summary Sheet ---
    summary_data = {
        "Metric": ["Total Patients", "Total Appointments", "Total Revenue", "Avg Satisfaction", "No-Show Rate"],
        "Value": [
            df['PatientID'].nunique(),
            len(df),
            df['Revenue'].sum(),
            8.2, # Placeholder or calculated from feedback
            len(df[df['Status'] == 'No-show']) / len(df)
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Executive Summary', index=False, startrow=2, startcol=1)
    
    worksheet = writer.sheets['Executive Summary']
    worksheet.write('B2', 'Mental Health Clinic MIS Dashboard - Executive Summary', workbook.add_format({'bold': True, 'font_size': 14}))
    
    # --- 2. Monthly Performance ---
    monthly_rev = df.groupby('Month')['Revenue'].sum().reset_index()
    monthly_rev.to_excel(writer, sheet_name='Monthly Metrics', index=False)
    
    # Add a Chart to Monthly Metrics
    chart = workbook.add_chart({'type': 'line'})
    chart.add_series({
        'name': 'Monthly Revenue',
        'categories': "='Monthly Metrics'!$A$2:$A$13",
        'values': "='Monthly Metrics'!$B$2:$B$13",
        'line': {'color': 'blue'},
    })
    chart.set_title({'name': 'Revenue Trend (Last 12 Months)'})
    writer.sheets['Monthly Metrics'].insert_chart('D2', chart)
    
    # --- 3. Clinician Performance ---
    clinician_perf = df.groupby('Name_clinician').agg({
        'AppointmentID': 'count',
        'Revenue': 'sum'
    }).rename(columns={'AppointmentID': 'Total_Sessions', 'Revenue': 'Total_Revenue'}).reset_index()
    clinician_perf.to_excel(writer, sheet_name='Clinician Performance', index=False)
    
    # --- 4. Patient Demographics ---
    demo_perf = df.groupby('Gender').agg({'PatientID': 'nunique'}).rename(columns={'PatientID': 'PatientCount'}).reset_index()
    demo_perf.to_excel(writer, sheet_name='Patient Demographics', index=False)

    # --- 5. Raw Data (Hidden or for reference) ---
    # We'll include a sample or just keep it summarized for MIS.
    
    writer.close()
    print(f"Excel MIS Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    generate_excel_report()
