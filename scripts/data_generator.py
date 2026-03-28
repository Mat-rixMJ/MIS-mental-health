import pandas as pd
import numpy as np
from faker import Faker
import random
import os
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# Configuration
NUM_PATIENTS = 1000
NUM_CLINICIANS = 20
NUM_APPOINTMENTS = 5000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

RAW_DATA_PATH = "data/raw"

def generate_patients():
    patients = []
    for i in range(1, NUM_PATIENTS + 1):
        patients.append({
            "PatientID": f"P-{i:04d}",
            "Name": fake.name(),
            "Age": random.randint(18, 75),
            "Gender": random.choice(["Male", "Female", "Non-binary"]),
            "Location": fake.city(),
            "InsuranceType": random.choice(["Private", "Public", "Self-pay"]),
            "AdmissionDate": fake.date_between(start_date=START_DATE, end_date=END_DATE)
        })
    df = pd.DataFrame(patients)
    df.to_csv(f"{RAW_DATA_PATH}/patients.csv", index=False)
    print(f"Generated {NUM_PATIENTS} patients.")
    return df

def generate_clinicians():
    clinicians = []
    specializations = ["Psychiatrist", "Clinical Psychologist", "Counselor", "Social Worker", "Occupational Therapist"]
    qualifications = ["MD", "PhD", "MSc", "MSW", "BSc"]
    
    for i in range(1, NUM_CLINICIANS + 1):
        clinicians.append({
            "ClinicianID": f"C-{i:03d}",
            "Name": f"Dr. {fake.last_name()}",
            "Specialization": random.choice(specializations),
            "Qualification": random.choice(qualifications),
            "Experience_Yrs": random.randint(2, 30),
            "HireDate": fake.date_between(start_date=datetime(2015, 1, 1), end_date=START_DATE)
        })
    df = pd.DataFrame(clinicians)
    df.to_csv(f"{RAW_DATA_PATH}/clinicians.csv", index=False)
    print(f"Generated {NUM_CLINICIANS} clinicians.")
    return df

def generate_appointments(patient_ids, clinician_ids):
    appointments = []
    statuses = ["Completed", "Completed", "Completed", "Completed", "Completed", "Cancelled", "No-show"]
    session_types = ["Therapy", "Diagnosis", "Follow-up", "Consultation"]
    
    for i in range(1, NUM_APPOINTMENTS + 1):
        date = fake.date_between(start_date=START_DATE, end_date=END_DATE)
        appointments.append({
            "AppointmentID": f"A-{i:05d}",
            "PatientID": random.choice(patient_ids),
            "ClinicianID": random.choice(clinician_ids),
            "Date": date,
            "Duration_Min": random.choice([30, 45, 60, 90]),
            "Status": random.choice(statuses),
            "SessionType": random.choice(session_types)
        })
    df = pd.DataFrame(appointments)
    df.to_csv(f"{RAW_DATA_PATH}/appointments.csv", index=False)
    print(f"Generated {NUM_APPOINTMENTS} appointments.")
    return df

def generate_billing(appointment_df):
    billing = []
    # Base rates for session types
    rates = {"Therapy": 150, "Diagnosis": 250, "Follow-up": 100, "Consultation": 120}
    
    # Only bill for Completed appointments (mostly)
    completed_apps = appointment_df[appointment_df["Status"] == "Completed"]
    
    for idx, row in completed_apps.iterrows():
        base_rate = rates[row["SessionType"]]
        # Add some variation
        amount = base_rate + random.randint(-20, 50)
        discount = random.choice([0, 0, 0, 0, 10, 20]) if amount > 150 else 0
        
        billing.append({
            "InvoiceID": f"INV-{idx:05d}",
            "AppointmentID": row["AppointmentID"],
            "PatientID": row["PatientID"],
            "Amount": amount,
            "Discount": discount,
            "Final_Amount": amount - discount,
            "PaymentStatus": random.choice(["Paid", "Paid", "Paid", "Pending"]),
            "PaymentMode": random.choice(["Insurance", "Credit Card", "Cash", "Bank Transfer"]),
            "Date": row["Date"]
        })
    
    df = pd.DataFrame(billing)
    df.to_csv(f"{RAW_DATA_PATH}/billing.csv", index=False)
    print(f"Generated {len(df)} billing records.")
    return df

def generate_feedback(patient_ids):
    feedback = []
    for pid in patient_ids[:int(NUM_PATIENTS * 0.7)]: # 70% of patients give feedback
        feedback.append({
            "PatientID": pid,
            "SatisfactionScore": random.randint(1, 10),
            "ImprovementIndex": random.randint(1, 10),
            "Comments": fake.sentence()
        })
    df = pd.DataFrame(feedback)
    df.to_csv(f"{RAW_DATA_PATH}/feedback.csv", index=False)
    print(f"Generated {len(df)} feedback records.")
    return df

def main():
    if not os.path.exists(RAW_DATA_PATH):
        os.makedirs(RAW_DATA_PATH)
        
    p_df = generate_patients()
    c_df = generate_clinicians()
    a_df = generate_appointments(p_df["PatientID"].tolist(), c_df["ClinicianID"].tolist())
    generate_billing(a_df)
    generate_feedback(p_df["PatientID"].tolist())
    print("\nData generation complete.")

if __name__ == "__main__":
    main()
