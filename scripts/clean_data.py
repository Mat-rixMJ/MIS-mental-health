"""
clean_data.py - Data Cleaning Pipeline
Reads raw data, performs precise cleaning steps, logs the process, and exports for analysis.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def print_summary(df_before, df_after, fixes_log):
    """Prints a detailed cleaning summary to console."""
    print("="*50)
    print("--- DATA CLEANING SUMMARY ---")
    print("="*50)
    print(f"Rows before cleaning : {len(df_before)}")
    print(f"Rows after cleaning  : {len(df_after)}")
    print(f"Rows dropped         : {len(df_before) - len(df_after)}")
    print("-"*50)
    print("Issues Fixed:")
    for issue, count in fixes_log.items():
        print(f" - {issue:<30}: {count} rows")
    print("="*50)

def main():
    raw_path = Path("data/raw/clinic_raw_data.csv")
    cleaned_path = Path("data/cleaned/clinic_cleaned_data.csv")
    pbi_path = Path("output/powerbi_export.csv")
    
    # Ensure dirs exist
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    pbi_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df = pd.read_csv(raw_path)
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{raw_path}'")
        return
        
    df_initial = df.copy()
    fixes = {}
    
    # 1. Fix appointment_date: detect DD/MM/YYYY
    # Identify rows containing '/' which implies DD/MM/YYYY
    mask_slash = df['appointment_date'].str.contains('/', na=False)
    fixes['Date Format (DD/MM/YYYY)'] = mask_slash.sum()
    
    df['date_fixed_flag'] = mask_slash
    
    # Convert dates safely
    def parse_date(date_str):
        if '/' in date_str:
            return pd.to_datetime(date_str, format="%d/%m/%Y")
        return pd.to_datetime(date_str, format="%Y-%m-%d")
        
    df['appointment_date'] = df['appointment_date'].apply(parse_date)
    
    # 2. Remove negative session_fee values, replace with median fee for that appointment_type
    mask_neg_fee = df['session_fee'] < 0
    fixes['Negative Session Fees'] = mask_neg_fee.sum()
    
    # Calculate median per type from positive fees
    medians = df[~mask_neg_fee].groupby('appointment_type')['session_fee'].median()
    
    def fix_fee(row):
        if row['session_fee'] < 0:
            return medians.get(row['appointment_type'], 0)
        return row['session_fee']
        
    df['session_fee'] = df.apply(fix_fee, axis=1)
    
    # 3. Remove rows where patient_age < 5 or > 100
    mask_age_outlier = (df['patient_age'] < 5) | (df['patient_age'] > 100)
    fixes['Invalid Age (Dropped)'] = mask_age_outlier.sum()
    df = df[~mask_age_outlier]
    
    # 4. Fill missing therapist_name using therapist_id
    mask_missing_name = df['therapist_name'].isna()
    fixes['Missing Therapist Names'] = mask_missing_name.sum()
    
    therapist_map = df.dropna(subset=['therapist_name']).set_index('therapist_id')['therapist_name'].to_dict()
    df['therapist_name'] = df['therapist_name'].fillna(df['therapist_id'].map(therapist_map))
    
    # 5. Remove satisfaction_score where attended=False
    mask_invalid_score = (~df['attended']) & (df['satisfaction_score'].notna())
    fixes['Invalid Satisfaction Scores'] = mask_invalid_score.sum()
    df.loc[~df['attended'], 'satisfaction_score'] = np.nan
    
    # 6. Drop exact duplicate rows
    dupes_count = df.duplicated().sum()
    fixes['Exact Duplicate Rows'] = dupes_count
    df = df.drop_duplicates()
    
    # 7. Add derived columns
    df['month'] = df['appointment_date'].dt.strftime('%B')
    df['month_num'] = df['appointment_date'].dt.month
    df['year'] = df['appointment_date'].dt.year
    df['quarter'] = df['appointment_date'].dt.quarter.apply(lambda x: f"Q{x}")
    
    def get_age_group(age):
        if age <= 25: return "18-25"
        if age <= 35: return "26-35"
        if age <= 45: return "36-45"
        if age <= 55: return "46-55"
        return "56+"
    
    df['age_group'] = df['patient_age'].apply(get_age_group)
    
    # revenue: session_fee where payment_status="Paid", else 0
    df['revenue'] = np.where(df['payment_status'] == 'Paid', df['session_fee'], 0)
    
    # is_weekend: True if appointment_date falls on Saturday or Sunday
    df['is_weekend'] = df['appointment_date'].dt.dayofweek >= 5
    
    # 8. Print cleaning summary
    print_summary(df_initial, df, fixes)
    
    # Save standard cleaned version
    df.to_csv(cleaned_path, index=False)
    print(f"✅ Saved cleaned dataset to -> {cleaned_path}")
    
    # 9. Power BI Export specific formatting
    df_pbi = df.copy()
    
    # Ensure all date columns are YYYY-MM-DD
    df_pbi['appointment_date'] = df_pbi['appointment_date'].dt.strftime('%Y-%m-%d')
    
    # No special chars in column names (use underscores)
    df_pbi.columns = df_pbi.columns.str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)
    
    # Boolean columns converted to "Yes"/"No" strings
    bool_cols = df_pbi.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        df_pbi[col] = df_pbi[col].map({True: 'Yes', False: 'No'})
        
    # All numeric columns have no trailing spaces (this applies broadly to objects)
    obj_cols = df_pbi.select_dtypes(include=['object']).columns
    for col in obj_cols:
        df_pbi[col] = df_pbi[col].astype(str).str.strip()
    
    df_pbi['patient_age'] = df_pbi['patient_age'].astype(int)
    
    df_pbi.to_csv(pbi_path, index=False)
    print(f"✅ Saved Power BI ready dataset to -> {pbi_path}")

if __name__ == "__main__":
    main()
