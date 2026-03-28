-- queries.sql - Analytical SQL Queries for MindBridge Wellness Clinic
-- Assumes a flat table named `clinic_data`

/*
-------------------------------------------------------------------------
Query 1: Department Performance (2024)
Purpose: Analyze the volume and financial contribution of each department for the year 2024.
Business Question: Which departments generated the most appointments and revenue in 2024?
-------------------------------------------------------------------------
*/
SELECT 
    department AS Department_Name,
    COUNT(patient_id) AS Total_Appointments,
    SUM(revenue) AS Total_Revenue
FROM clinic_data
WHERE year = 2024
GROUP BY department
ORDER BY Total_Revenue DESC;

/*
-------------------------------------------------------------------------
Query 2: Monthly Appointment Trend
Purpose: Track clinic utilization over time to identify seasonal peaks or growth.
Business Question: How are appointment volumes trending month over month across different years?
-------------------------------------------------------------------------
*/
SELECT 
    year AS Appt_Year,
    month_num AS Appt_Month,
    month AS Month_Name,
    COUNT(patient_id) AS Total_Appointments
FROM clinic_data
GROUP BY year, month_num, month
ORDER BY year ASC, month_num ASC;

/*
-------------------------------------------------------------------------
Query 3: Top Therapists by Satisfaction
Purpose: Highlight the best-rated therapists to understand clinical excellence.
Business Question: Who are the top 3 therapists based on patient satisfaction, ensuring they have a reliable sample size (min 50 sessions)?
-------------------------------------------------------------------------
*/
SELECT 
    therapist_name AS Therapist,
    department AS Department,
    ROUND(AVG(satisfaction_score), 2) AS Avg_Satisfaction,
    COUNT(patient_id) AS Total_Sessions
FROM clinic_data
WHERE attended IN (1, 'Yes', 'True')
GROUP BY therapist_name, department
HAVING COUNT(patient_id) >= 50
ORDER BY Avg_Satisfaction DESC
LIMIT 3;

/*
-------------------------------------------------------------------------
Query 4: Attendance Rate by City and Type
Purpose: Identify geographic and service-level attendance behaviors.
Business Question: How do no-show rates vary across different cities and types of appointments?
-------------------------------------------------------------------------
*/
SELECT 
    city AS City,
    appointment_type AS Appt_Type,
    COUNT(patient_id) AS Total_Booked,
    SUM(CASE WHEN attended IN (1, 'Yes', 'True') THEN 1 ELSE 0 END) AS Total_Attended,
    ROUND(SUM(CASE WHEN attended IN (1, 'Yes', 'True') THEN 1 ELSE 0 END) * 100.0 / COUNT(patient_id), 2) AS Attendance_Rate_Pct
FROM clinic_data
GROUP BY city, appointment_type
ORDER BY city ASC, Attendance_Rate_Pct DESC;

/*
-------------------------------------------------------------------------
Query 5: Patient Dropout Analysis
Purpose: Understand patient retention by seeing how many only had one session versus recurring visits.
Business Question: What proportion of our patient base are one-time visitors vs. returning patients?
-------------------------------------------------------------------------
*/
WITH PatientVisits AS (
    SELECT 
        patient_id, 
        COUNT(appointment_date) AS Visit_Count
    FROM clinic_data
    GROUP BY patient_id
)
SELECT 
    CASE 
        WHEN Visit_Count = 1 THEN 'Single Visit (Dropout Risk)'
        ELSE 'Returning Patient (2+ Visits)' 
    END AS Retention_Category,
    COUNT(patient_id) AS Total_Patients,
    ROUND(COUNT(patient_id) * 100.0 / (SELECT COUNT(DISTINCT patient_id) FROM clinic_data), 2) AS Pct_Of_Total_Base
FROM PatientVisits
GROUP BY Retention_Category;

/*
-------------------------------------------------------------------------
Query 6: Revenue Leakage
Purpose: Quantify uncollected revenue due to pending or waived payments.
Business Question: How much potential revenue is lost or delayed across departments?
-------------------------------------------------------------------------
*/
SELECT 
    department AS Department,
    SUM(CASE WHEN payment_status = 'Pending' THEN session_fee ELSE 0 END) AS Total_Pending_INR,
    SUM(CASE WHEN payment_status = 'Waived' THEN session_fee ELSE 0 END) AS Total_Waived_INR,
    SUM(CASE WHEN payment_status IN ('Pending', 'Waived') THEN session_fee ELSE 0 END) AS Total_Leakage_INR
FROM clinic_data
GROUP BY department
ORDER BY Total_Leakage_INR DESC;

/*
-------------------------------------------------------------------------
Query 7: Weekend vs. Weekday Comparison
Purpose: Evaluate clinic utilization on weekends.
Business Question: Are weekend slots as utilized and profitable as weekday slots?
-------------------------------------------------------------------------
*/
SELECT 
    CASE WHEN is_weekend IN (1, 'Yes', 'True') THEN 'Weekend' ELSE 'Weekday' END AS Day_Type,
    COUNT(patient_id) AS Total_Appointments,
    ROUND(AVG(session_fee), 2) AS Avg_Session_Fee,
    SUM(revenue) AS Total_Revenue,
    ROUND(SUM(CASE WHEN attended IN (1, 'Yes', 'True') THEN 1 ELSE 0 END) * 100.0 / COUNT(patient_id), 2) AS Attendance_Rate_Pct
FROM clinic_data
GROUP BY CASE WHEN is_weekend IN (1, 'Yes', 'True') THEN 'Weekend' ELSE 'Weekday' END;

/*
-------------------------------------------------------------------------
Query 8: Wait Time Distribution
Purpose: Assess operational efficiency and patient access to care.
Business Question: What percentage of patients are seen quickly (<3 days) versus experiencing long wait times (>7 days)?
-------------------------------------------------------------------------
*/
SELECT 
    CASE 
        WHEN wait_time_days <= 3 THEN '0-3 Days (Fast)'
        WHEN wait_time_days <= 7 THEN '4-7 Days (Standard)'
        ELSE '8+ Days (Delayed)' 
    END AS Wait_Time_Bucket,
    COUNT(patient_id) AS Patient_Count,
    ROUND(COUNT(patient_id) * 100.0 / (SELECT COUNT(*) FROM clinic_data), 2) AS Pct_Of_Total
FROM clinic_data
GROUP BY 
    CASE 
        WHEN wait_time_days <= 3 THEN '0-3 Days (Fast)'
        WHEN wait_time_days <= 7 THEN '4-7 Days (Standard)'
        ELSE '8+ Days (Delayed)' 
    END;

/*
-------------------------------------------------------------------------
Query 9: Crisis Intervention Seasonality
Purpose: Track critical mental health trends over the calendar year.
Business Question: Are there specific months where Crisis Intervention volumes spike?
-------------------------------------------------------------------------
*/
SELECT 
    month_num AS Appt_Month_Num,
    month AS Month_Name,
    COUNT(patient_id) AS Total_Crisis_Sessions
FROM clinic_data
WHERE appointment_type = 'Crisis Intervention'
GROUP BY month_num, month
ORDER BY month_num ASC;

/*
-------------------------------------------------------------------------
Query 10: Referral Source Effectiveness
Purpose: Determine which marketing or referral channels yield the most reliable patients.
Business Question: Which referral sources bring in patients with the highest attendance rates?
-------------------------------------------------------------------------
*/
SELECT 
    referral_source AS Referral_Channel,
    COUNT(patient_id) AS Total_Referred,
    SUM(CASE WHEN attended IN (1, 'Yes', 'True') THEN 1 ELSE 0 END) AS Attended_Sessions,
    ROUND(SUM(CASE WHEN attended IN (1, 'Yes', 'True') THEN 1 ELSE 0 END) * 100.0 / COUNT(patient_id), 2) AS Attendance_Rate_Pct
FROM clinic_data
GROUP BY referral_source
ORDER BY Attendance_Rate_Pct DESC;
