import pandas as pd
import os

# Paths
RAW_DATA_PATH = "data/raw"
PROCESSED_DATA_PATH = "data/processed"
POWERBI_EXPORT_PATH = "data/powerbi_export"

def load_data():
    patients = pd.read_csv(f"{RAW_DATA_PATH}/patients.csv")
    clinicians = pd.read_csv(f"{RAW_DATA_PATH}/clinicians.csv")
    appointments = pd.read_csv(f"{RAW_DATA_PATH}/appointments.csv")
    billing = pd.read_csv(f"{RAW_DATA_PATH}/billing.csv")
    feedback = pd.read_csv(f"{RAW_DATA_PATH}/feedback.csv")
    return patients, clinicians, appointments, billing, feedback

def clean_and_transform():
    patients, clinicians, appointments, billing, feedback = load_data()
    
    # 1. Merge Appointments with Patients and Clinicians
    df_merged = appointments.merge(patients, on="PatientID", how="left")
    df_merged = df_merged.merge(clinicians, on="ClinicianID", how="left", suffixes=('_patient', '_clinician'))
    
    # 2. Add Billing info to Appointments
    df_final = df_merged.merge(billing[['AppointmentID', 'Amount', 'Discount', 'Final_Amount', 'PaymentStatus', 'PaymentMode']], 
                               on="AppointmentID", how="left")
    
    # 3. Handle data types
    df_final['Date'] = pd.to_datetime(df_final['Date'])
    df_final['Month'] = df_final['Date'].dt.strftime('%Y-%m')
    df_final['Year'] = df_final['Date'].dt.year
    
    # 4. Feature Engineering: Revenue per Session
    df_final['Revenue'] = df_final['Final_Amount'].fillna(0)
    
    # 5. Satisfaction Score aggregation
    # Add feedback to the main dataframe (if possible by PatientID, but feedback is overall)
    # We'll keep feedback separate for patient-level analysis.
    
    # 6. Save Processed Data
    if not os.path.exists(PROCESSED_DATA_PATH):
        os.makedirs(PROCESSED_DATA_PATH)
    
    df_final.to_csv(f"{PROCESSED_DATA_PATH}/cleaned_clinic_data.csv", index=False)
    print(f"Saved cleaned data with {len(df_final)} records.")
    
    # 7. Prepare Power BI Export (clean sheets)
    if not os.path.exists(POWERBI_EXPORT_PATH):
        os.makedirs(POWERBI_EXPORT_PATH)
        
    df_final.to_csv(f"{POWERBI_EXPORT_PATH}/powerbi_master_data.csv", index=False)
    patients.to_csv(f"{POWERBI_EXPORT_PATH}/dim_patients.csv", index=False)
    clinicians.to_csv(f"{POWERBI_EXPORT_PATH}/dim_clinicians.csv", index=False)
    feedback.to_csv(f"{POWERBI_EXPORT_PATH}/fact_feedback.csv", index=False)
    
    print("Power BI export files ready.")

if __name__ == "__main__":
    clean_and_transform()
