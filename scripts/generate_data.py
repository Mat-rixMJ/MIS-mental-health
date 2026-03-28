"""
generate_data.py - Mental Health Clinic Data Generator
Generates a realistic synthetic dataset simulating a mental health clinic with intentional data quality issues.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
TOTAL_ROWS = 1500
DUPE_PERCENT = 0.05
NUM_UNIQUE = int(TOTAL_ROWS * (1 - DUPE_PERCENT))
NUM_DUPES = TOTAL_ROWS - NUM_UNIQUE
SEED = 42

np.random.seed(SEED)
random.seed(SEED)

def generate_data():
    """Generates synthetic dataset and injects predefined quality issues."""
    
    # Core reference data mapping
    therapists = {
        "T01": "Dr. Aarav Sharma", "T02": "Dr. Priya Patel",
        "T03": "Dr. Rohan Gupta", "T04": "Dr. Ananya Reddy",
        "T05": "Dr. Vikram Singh", "T06": "Dr. Neha Desai",
        "T07": "Dr. Arjun Kumar", "T08": "Dr. Meera Iyer"
    }
    
    departments = ["Anxiety & Stress", "Depression", "Addiction Recovery", "Child & Adolescent", "Trauma & PTSD"]
    appt_types = ["Initial Consultation", "Follow-up", "Group Session", "Crisis Intervention"]
    genders = ["Male", "Female", "Non-binary", "Prefer not to say"]
    gender_probs = [0.45, 0.45, 0.05, 0.05]
    cities = ["Mumbai", "Delhi", "Kolkata", "Bangalore", "Chennai", "Hyderabad"]
    durations = [30, 45, 60, 90]
    referral_sources = ["Self-referral", "Doctor referral", "Online search", "Word of mouth", "NGO partner"]
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    data = []
    
    # Generate unique rows
    for i in range(NUM_UNIQUE):
        # Age skewed 25-40 using triangular distribution over 18-65 peaked at 30
        age = int(np.random.triangular(18, 30, 65))
        
        # Therapist selection
        t_id = random.choice(list(therapists.keys()))
        t_name = therapists[t_id]
        
        # Appointment Details
        appt_date = start_date + timedelta(days=random.randint(0, date_range))
        appt_type = random.choice(appt_types)
        
        # Determine session fee based on appointment type boundaries
        fee = 0
        if appt_type == "Initial Consultation": fee = random.randint(800, 1200)
        elif appt_type == "Follow-up": fee = random.randint(500, 800)
        elif appt_type == "Group Session": fee = random.randint(300, 500)
        elif appt_type == "Crisis Intervention": fee = random.randint(1000, 1500)
        
        # ~85% attendance rate
        attended = random.random() < 0.85
        
        # Satisfaction is 1-5, only if attended=True (leave blank ~20% of the time)
        sat_score = np.nan
        if attended and random.random() < 0.80:
            sat_score = float(random.randint(1, 5))
            
        data.append({
            "patient_id": f"P{random.randint(1, 5000):04d}",
            "appointment_date": appt_date.strftime("%Y-%m-%d"),
            "therapist_name": t_name,
            "therapist_id": t_id,
            "department": random.choice(departments),
            "appointment_type": appt_type,
            "patient_age": age,
            "patient_gender": np.random.choice(genders, p=gender_probs),
            "city": random.choice(cities),
            "session_duration_mins": random.choice(durations),
            "attended": attended,
            "session_fee": fee,
            "payment_status": np.random.choice(["Paid", "Pending", "Waived"], p=[0.7, 0.2, 0.1]),
            "satisfaction_score": sat_score,
            "wait_time_days": random.randint(0, 21),
            "referral_source": random.choice(referral_sources)
        })
        
    df = pd.DataFrame(data)
    
    # --- Inject Data Quality Issues ---
    
    # 1. 5% appointment_dates formatted as DD/MM/YYYY instead of YYYY-MM-DD
    date_err_idx = df.sample(frac=0.05, random_state=SEED).index
    df.loc[date_err_idx, "appointment_date"] = pd.to_datetime(df.loc[date_err_idx, "appointment_date"]).dt.strftime("%d/%m/%Y")
    
    # 2. 3% session_fee values as negative numbers
    fee_err_idx = df.sample(frac=0.03, random_state=SEED+1).index
    df.loc[fee_err_idx, "session_fee"] = df.loc[fee_err_idx, "session_fee"] * -1
    
    # 3. 4% patient_age values as 0 or >100
    age_err_idx = df.sample(frac=0.04, random_state=SEED+2).index
    df.loc[age_err_idx, "patient_age"] = np.random.choice([0, 2, 105, 110], size=len(age_err_idx))
    
    # 4. 3% rows with missing therapist_name
    name_err_idx = df.sample(frac=0.03, random_state=SEED+3).index
    df.loc[name_err_idx, "therapist_name"] = np.nan
    
    # 5. 2% of satisfaction_score filled even when attended=False
    num_sat_issues = int(TOTAL_ROWS * 0.02)
    unattended_idx = df[~df["attended"]].index
    if len(unattended_idx) >= num_sat_issues:
        sat_err_idx = np.random.choice(unattended_idx, size=num_sat_issues, replace=False)
        df.loc[sat_err_idx, "satisfaction_score"] = np.random.randint(1, 6, size=len(sat_err_idx)).astype(float)
    
    # 6. 5% duplicate rows (copying sample rows and appending)
    dupes = df.sample(n=NUM_DUPES, random_state=SEED+4)
    df = pd.concat([df, dupes], ignore_index=True)
    
    # Shuffle entire dataset
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    
    return df

def main():
    """Main execution function."""
    output_path = Path("data/raw/clinic_raw_data.csv")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = generate_data()
    
    try:
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully generated {len(df)} rows.")
        print(f"✅ Saved raw data to -> {output_path}")
    except Exception as e:
        print(f"❌ Target path error: {e}")

if __name__ == "__main__":
    main()
