-- Mental Health Clinic MIS Dashboard - SQL Schema and Analysis Queries

-- 1. Table Definitions (Conceptual, to be run in any SQL environment)

CREATE TABLE Patients (
    PatientID TEXT PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Gender TEXT,
    Location TEXT,
    InsuranceType TEXT,
    AdmissionDate DATE
);

CREATE TABLE Clinicians (
    ClinicianID TEXT PRIMARY KEY,
    Name TEXT,
    Specialization TEXT,
    Qualification TEXT,
    Experience_Yrs INTEGER,
    HireDate DATE
);

CREATE TABLE Appointments (
    AppointmentID TEXT PRIMARY KEY,
    PatientID TEXT,
    ClinicianID TEXT,
    Date DATE,
    Duration_Min INTEGER,
    Status TEXT,
    SessionType TEXT,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
    FOREIGN KEY (ClinicianID) REFERENCES Clinicians(ClinicianID)
);

CREATE TABLE Billing (
    InvoiceID TEXT PRIMARY KEY,
    AppointmentID TEXT,
    PatientID TEXT,
    Amount DECIMAL(10,2),
    Discount DECIMAL(10,2),
    Final_Amount DECIMAL(10,2),
    PaymentStatus TEXT,
    PaymentMode TEXT,
    Date DATE,
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID),
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID)
);

-- 2. Business Analysis Queries

-- Q1: Total Revenue by Month
SELECT 
    strftime('%Y-%m', Date) as Month, 
    SUM(Final_Amount) as TotalRevenue,
    COUNT(InvoiceID) as TotalInvoices
FROM Billing
GROUP BY Month
ORDER BY Month DESC;

-- Q2: Clinician Productivity (Sessions and Revenue)
SELECT 
    c.Name as ClinicianName,
    c.Specialization,
    COUNT(a.AppointmentID) as TotalSessions,
    SUM(b.Final_Amount) as TotalRevenueGenerated
FROM Clinicians c
JOIN Appointments a ON c.ClinicianID = a.ClinicianID
JOIN Billing b ON a.AppointmentID = b.AppointmentID
WHERE a.Status = 'Completed'
GROUP BY c.ClinicianID
ORDER BY TotalRevenueGenerated DESC;

-- Q3: Patient Demographics Analysis (Revenue per Gender)
SELECT 
    p.Gender,
    AVG(p.Age) as AverageAge,
    SUM(b.Final_Amount) as TotalRevenue
FROM Patients p
JOIN Billing b ON p.PatientID = b.PatientID
GROUP BY p.Gender;

-- Q4: Appointment Status Distribution (%)
SELECT 
    Status,
    COUNT(*) as Count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Appointments), 2) as Percentage
FROM Appointments
GROUP BY Status;

-- Q5: Top session types by demand
SELECT 
    SessionType,
    COUNT(*) as Frequency
FROM Appointments
GROUP BY SessionType
ORDER BY Frequency DESC;
