@echo off
echo Running Data Generation...
python scripts/generate_data.py
echo.
echo Running Data Cleaning...
python scripts/clean_data.py
echo.
echo Generating Excel MIS Report...
python scripts/generate_excel_report.py
echo.
echo Generating PDF Business Insights...
python scripts/generate_pdf_report.py
echo.
echo ✅ All scripts completed successfully. Project ready for GitHub.
