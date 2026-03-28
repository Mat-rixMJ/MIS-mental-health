"""
generate_pdf_report.py - PDF Business Insight Generator
Calculates insights from cleaned data and generates a professional PDF using ReportLab.
"""
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from pathlib import Path
from datetime import datetime

def draw_kpi_box(c, x, y, width, height, title, value):
    c.setStrokeColor(HexColor("#1F3864"))
    c.setLineWidth(1.5)
    c.rect(x, y, width, height)
    
    # Fill header
    c.setFillColor(HexColor("#1F3864"))
    c.rect(x, y + height - 25, width, 25, fill=1)
    
    # Title
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + width/2.0, y + height - 18, title)
    
    # Value
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x + width/2.0, y + 20, str(value))

def generate_pdf():
    input_path = Path("data/cleaned/clinic_cleaned_data.csv")
    output_path = Path("output/Business_Insights_Report.pdf")
    
    if not input_path.exists():
        print(f"❌ Error: Could not find '{input_path}'")
        return
        
    df = pd.read_csv(input_path)
    
    # Calculations
    total_apps = len(df)
    total_revenue = df['revenue'].sum()
    att_rate = df['attended'].mean() * 100
    avg_sat = df['satisfaction_score'].mean()
    avg_wait = df['wait_time_days'].mean()
    
    dept_stats = df.groupby('department').agg(Appts=('patient_id', 'count'), Rev=('revenue', 'sum'))
    top_dept = dept_stats['Appts'].idxmax()
    top_dept_apps = dept_stats.loc[top_dept, 'Appts']
    
    therapist_stats = df[df['attended'] == True].groupby('therapist_name').agg(Sat=('satisfaction_score', 'mean'), Appts=('patient_id', 'count'))
    top_therapist = therapist_stats['Sat'].idxmax()
    top_therapist_sat = therapist_stats.loc[top_therapist, 'Sat']
    
    dropout_risk = (1 - (df['attended'].sum() / total_apps)) * 100
    
    # Create Canvas
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # === PAGE 1: Cover + KPIs ===
    c.setFillColor(HexColor("#1F3864"))
    c.rect(0, height - 100, width, 100, fill=1)
    
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2.0, height - 45, "MindBridge Wellness Clinic")
    
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2.0, height - 70, "Annual MIS Performance Report 2023–2024")
    
    c.setFillColor(black)
    c.setFont("Helvetica-Oblique", 12)
    c.drawRightString(width - 40, height - 130, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 170, "Executive Dashboard")
    c.setLineWidth(1)
    c.line(40, height - 175, width - 40, height - 175)
    
    # Grid for KPIs
    box_w = 200
    box_h = 70
    start_y = height - 280
    
    # Row 1
    draw_kpi_box(c, 70, start_y, box_w, box_h, "Total Appointments", f"{total_apps:,}")
    draw_kpi_box(c, width - 70 - box_w, start_y, box_w, box_h, "Total Revenue Collected", f"INR {total_revenue:,.2f}")
    
    # Row 2
    draw_kpi_box(c, 70, start_y - 100, box_w, box_h, "Overall Attendance Rate", f"{att_rate:.1f}%")
    draw_kpi_box(c, width - 70 - box_w, start_y - 100, box_w, box_h, "Average Wait Time", f"{avg_wait:.1f} Days")
    
    # Row 3 (Centered)
    draw_kpi_box(c, (width - box_w)/2.0, start_y - 200, box_w, box_h, "Average Satisfaction", f"{avg_sat:.2f} / 5.0")
    
    c.showPage()
    
    # === PAGE 2: Key Insights ===
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(HexColor("#1F3864"))
    c.drawString(40, height - 60, "Key Analytical Insights")
    c.setLineWidth(1)
    c.line(40, height - 65, width - 40, height - 65)
    
    textobject = c.beginText()
    textobject.setTextOrigin(40, height - 110)
    
    def add_insight(title, body):
        textobject.setFont("Helvetica-Bold", 14)
        textobject.setFillColor(HexColor("#333333"))
        textobject.textLine(title)
        textobject.moveCursor(0, 5)
        textobject.setFont("Helvetica", 11)
        textobject.setFillColor(black)
        
        # Word wrap manually
        from textwrap import wrap
        lines = wrap(body, width=90)
        for line in lines:
            textobject.textLine(line)
        textobject.moveCursor(0, 15)
        
    i1 = f"Over the 2023-2024 period, MindBridge Wellness Clinic successfully facilitated {total_apps:,} appointments, driving a total revenue collection of INR {total_revenue:,.2f}. Given the consistent wait time of approximately {avg_wait:.1f} days, overall operational throughput remains robust with clear signals of sustained demand."
    
    i2 = f"The {top_dept} department emerged as the most active service line, comprising {top_dept_apps:,} appointments. This highlights a significant clinical need in this area, suggesting that future resource allocation, hiring, and programmatic funding should prioritize this department to maintain high service standards."
    
    i3 = f"The overall clinic attendance rate stabilized at {att_rate:.1f}%, indicating a baseline no-show or cancellation risk of around {dropout_risk:.1f}%. This represents a tangible area of revenue leakage and continuity-of-care disruption. Implementing automated SMS reminders 24-48 hours prior to appointments could mitigate this dropout rate."
    
    i4 = f"{top_therapist} stands out as the top performer in patient outcomes, achieving an unparalleled average satisfaction score of {top_therapist_sat:.2f}/5.0. Analyzing their patient engagement methods could provide a valuable standard of care framework to train newer clinicians and elevate clinic-wide satisfaction metrics."
    
    i5 = f"To maximize operational margins, management should consider expanding the Group Session offerings. While Initial Consultations drive higher singular fees, Group Sessions scale effectively under current therapist capacities without extending the {avg_wait:.1f}-day average wait time, thereby increasing overall accessibility and revenue density."

    add_insight("1. Overall Performance Summary", i1)
    add_insight("2. Department Spotlight", i2)
    add_insight("3. Attendance & Dropout Concern", i3)
    add_insight("4. Therapist Performance Observation", i4)
    add_insight("5. Strategic Recommendation", i5)
    
    c.drawText(textobject)
    
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2.0, 30, "Generated by MIS Dashboard Pipeline | Confidential")
    
    c.save()
    print(f"✅ Saved PDF Insights Report to -> {output_path}")

if __name__ == "__main__":
    generate_pdf()
