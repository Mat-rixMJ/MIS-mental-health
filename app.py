import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess
import time
from datetime import datetime
import numpy as np

# PAGE CONFIG
st.set_page_config(page_title="MindBridge Wellness Clinic — MIS Dashboard", layout="wide")

# CSS INJECTION
st.markdown("""
<style>
/* KPI metric cards */
[data-testid="stMetric"] {
    background-color: var(--secondary-background-color);
    border-left: 5px solid #1F3864;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
/* Ensure headers follow theme color or primary clinic color */
h1, h2, h3 {
    color: var(--text-color);
}
h1 {
    font-size: 32px !important;
    font-weight: 700 !important;
}
/* Sidebar navigation text visibility */
[data-testid="stSidebarNav"] {
    color: var(--text-color);
}
</style>
""", unsafe_allow_html=True)

# HELPER FUNCTIONS
def format_indian_currency(amount):
    if pd.isna(amount): return "₹0"
    try:
        s, *d = str(int(amount)).partition(".")
        r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
        return f"₹{r}"
    except:
        return f"₹{amount}"

def get_delta_color(current, previous, higher_is_better=True):
    if current == previous:
        return "off"
    if higher_is_better:
        return "normal" if current > previous else "inverse"
    else:
        return "inverse" if current > previous else "normal"

# DATA LOADING
@st.cache_data(ttl=300)
def load_data():
    file_path = "data/cleaned/clinic_cleaned_data.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    if 'appointment_date' in df.columns:
        df['appointment_date'] = pd.to_datetime(df['appointment_date'])
        df['Year'] = df['appointment_date'].dt.year
        df['Month_Num'] = df['appointment_date'].dt.month
        df['Month_Name'] = df['appointment_date'].dt.strftime('%b')
        df['DayOfWeek'] = df['appointment_date'].dt.day_name()
        df['WeekNum'] = df['appointment_date'].dt.isocalendar().week
    return df

raw_df = load_data()

# SIDEBAR
st.sidebar.markdown(
    """
    <div style="background-color: #1F3864; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">
        <h2 style="color: white !important; margin: 0; font-size: 24px; letter-spacing: 1px;">MindBridge</h2>
        <span style="color: #64B5F6; font-weight: 600; font-size: 14px; text-transform: uppercase;">Wellness Clinic</span>
    </div>
    """, unsafe_allow_html=True
)

pages = [
    "Pipeline Control",
    "Executive Overview",
    "Department & Therapist",
    "Demographics & Geography",
    "Financial Analysis"
]

selected_page = st.sidebar.radio("Navigation", pages)
filtered_df = pd.DataFrame()

if selected_page != "Pipeline Control":
    if raw_df.empty:
        st.warning("Run the pipeline first on the Pipeline Control page")
        st.stop()
        
    st.sidebar.markdown("### Filters")
    available_years = sorted(raw_df['Year'].dropna().unique().tolist()) if 'Year' in raw_df.columns else []
    year_options = available_years + ["Both"]
    selected_years = st.sidebar.multiselect("Year", year_options, default=["Both"])
    
    available_cities = ["All Cities"] + sorted(raw_df['city'].dropna().unique().tolist() if 'city' in raw_df.columns else [])
    selected_cities = st.sidebar.multiselect("City", available_cities, default=["All Cities"])
    
    available_depts = sorted(raw_df['department'].dropna().unique().tolist() if 'department' in raw_df.columns else [])
    selected_depts = st.sidebar.multiselect("Department", available_depts, default=[])

    filtered_df = raw_df.copy()
    if "Both" not in selected_years and selected_years:
        filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
    if "All Cities" not in selected_cities and selected_cities:
        if 'city' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
    if selected_depts:
        if 'department' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['department'].isin(selected_depts)]

st.sidebar.divider()

if os.path.exists("data/cleaned/clinic_cleaned_data.csv"):
    mod_time = os.path.getmtime("data/cleaned/clinic_cleaned_data.csv")
    st.sidebar.caption(f"Last updated: {datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')}")

if os.path.exists("output/MIS_Weekly_Report.xlsx"):
    with open("output/MIS_Weekly_Report.xlsx", "rb") as file:
        st.sidebar.download_button("📊 Download Excel Report", data=file, file_name="MIS_Weekly_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
if os.path.exists("output/Business_Insights_Report.pdf"):
    with open("output/Business_Insights_Report.pdf", "rb") as file:
        st.sidebar.download_button("📄 Download PDF Report", data=file, file_name="Business_Insights_Report.pdf", mime="application/pdf", use_container_width=True)

if os.path.exists("output/powerbi_export.csv"):
    with open("output/powerbi_export.csv", "rb") as file:
        st.sidebar.download_button("⚡ Download Power BI CSV", data=file, file_name="powerbi_export.csv", mime="text/csv", use_container_width=True)
elif os.path.exists("data/cleaned/clinic_cleaned_data.csv"):
    # Fallback: offer cleaned data if PowerBI export hasn't been generated yet
    with open("data/cleaned/clinic_cleaned_data.csv", "rb") as file:
        st.sidebar.download_button("⚡ Download Data (CSV)", data=file, file_name="clinic_cleaned_data.csv", mime="text/csv", use_container_width=True)


def check_empty(df):
    if df.empty:
        st.info("No data matches the current filters. Please adjust sidebar filters.")
        return True
    return False

# ---------------------------------------------------------
# PAGE 1: PIPELINE CONTROL
# ---------------------------------------------------------
if selected_page == "Pipeline Control":
    st.title("Pipeline Control Center")
    st.markdown("### Run the data pipeline step by step or all at once")

    def run_command_live_output(command):
        output_placeholder = st.empty()
        output_lines = []
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
            for line in process.stdout:
                output_lines.append(line.strip())
                output_placeholder.code("\n".join(output_lines[-20:]), language='bash')
            process.wait()
            return process.returncode == 0
        except Exception as e:
            output_placeholder.error(f"Failed to execute: {str(e)}")
            return False

    def get_file_status(filepath):
        if not os.path.exists(filepath):
            return "Missing", "red", 0
        mtime = os.path.getmtime(filepath)
        age_hours = (time.time() - mtime) / 3600
        color = "green" if age_hours < 1 else "orange"
        status = "Recent" if color == "green" else "Old"
        return status, color, os.path.getsize(filepath)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**1. Generate Data**")
        status, color, size = get_file_status("data/raw/clinic_raw_data.csv")
        st.markdown(f"Status: :{color}[{status}]")
        if size > 0:
            try: st.caption(f"Rows: {len(pd.read_csv('data/raw/clinic_raw_data.csv'))}")
            except: pass
        if st.button("Generate Raw Data", use_container_width=True):
            run_command_live_output("python scripts/generate_data.py")
            st.rerun()

    with col2:
        st.markdown("**2. Clean Data**")
        status, color, size = get_file_status("data/cleaned/clinic_cleaned_data.csv")
        st.markdown(f"Status: :{color}[{status}]")
        if size > 0:
            try: st.caption(f"Rows: {len(pd.read_csv('data/cleaned/clinic_cleaned_data.csv'))}")
            except: pass
        if st.button("Run Data Cleaning", use_container_width=True):
            run_command_live_output("python scripts/clean_data.py")
            st.rerun()
            
    with col3:
        st.markdown("**3. Generate Excel**")
        status, color, size = get_file_status("output/MIS_Weekly_Report.xlsx")
        st.markdown(f"Status: :{color}[{status}]")
        if size > 0: st.caption(f"Size: {size/1024:.1f} KB")
        if st.button("Generate Excel Report", use_container_width=True):
            if run_command_live_output("python scripts/generate_excel_report.py"):
                st.success("Excel Generation Complete")
            st.rerun()
            
    with col4:
        st.markdown("**4. Generate PDF**")
        status, color, size = get_file_status("output/Business_Insights_Report.pdf")
        st.markdown(f"Status: :{color}[{status}]")
        if size > 0: st.caption(f"Size: {size/1024:.1f} KB")
        if st.button("Generate PDF Report", use_container_width=True):
            if run_command_live_output("python scripts/generate_pdf_report.py"):
                st.success("PDF Generation Complete")
            st.rerun()

    st.markdown("---")
    if st.button("Run Full Pipeline", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        start_time = time.time()
        run_command_live_output("python scripts/generate_data.py")
        progress_bar.progress(25)
        run_command_live_output("python scripts/clean_data.py")
        progress_bar.progress(50)
        run_command_live_output("python scripts/generate_excel_report.py")
        progress_bar.progress(75)
        run_command_live_output("python scripts/generate_pdf_report.py")
        progress_bar.progress(100)
        st.balloons()
        st.success(f"Pipeline finished successfully in {time.time() - start_time:.1f} seconds!")
        st.rerun()

    if os.path.exists("data/raw/clinic_raw_data.csv"):
        with st.expander("View Raw Data Sample"):
            st.dataframe(pd.read_csv("data/raw/clinic_raw_data.csv", nrows=20))
            
    if os.path.exists("data/cleaned/clinic_cleaned_data.csv"):
        with st.expander("View Cleaned Data Sample"):
            df_cl = pd.read_csv("data/cleaned/clinic_cleaned_data.csv", nrows=20)
            st.dataframe(df_cl)
            st.write("Column Types:", df_cl.dtypes.to_dict())

# ---------------------------------------------------------
# PAGE 2: EXECUTIVE OVERVIEW
# ---------------------------------------------------------
elif selected_page == "Executive Overview":
    st.title("Executive Overview")
    if not check_empty(filtered_df):
        try:
            cur_year = filtered_df['Year'].max() if 'Year' in filtered_df.columns else 0
            df_cur = filtered_df[filtered_df['Year'] == cur_year] if cur_year > 0 else filtered_df
            df_prev = filtered_df[filtered_df['Year'] == (cur_year - 1)] if cur_year > 0 else pd.DataFrame()
            
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            
            cur_appts = len(df_cur)
            prev_appts = len(df_prev)
            kpi1.metric("Total Appointments", cur_appts, delta=cur_appts - prev_appts if prev_appts>0 else 0, delta_color=get_delta_color(cur_appts, prev_appts))
            
            cur_rev = df_cur['revenue'].sum() if 'revenue' in df_cur.columns else 0
            prev_rev = df_prev['revenue'].sum() if 'revenue' in df_prev.columns else 0
            kpi2.metric("Total Revenue", format_indian_currency(cur_rev), delta=format_indian_currency(cur_rev - prev_rev) if prev_rev>0 else "0", delta_color=get_delta_color(cur_rev, prev_rev))
            
            def get_att_rate(d): return (d['attended'].mean()*100) if not d.empty and 'attended' in d.columns else 0
            cur_att, prev_att = get_att_rate(df_cur), get_att_rate(df_prev)
            kpi3.metric("Attendance Rate (%)", f"{cur_att:.1f}%", delta=f"{cur_att - prev_att:.1f}%" if prev_att>0 else None, delta_color=get_delta_color(cur_att, prev_att))
            
            def get_sat(d): return d['satisfaction_score'].mean() if not d.empty and 'satisfaction_score' in d.columns else 0
            cur_sat, prev_sat = get_sat(df_cur), get_sat(df_prev)
            kpi4.metric("Avg Satisfaction", f"{cur_sat:.2f}", delta=f"{cur_sat - prev_sat:.2f}" if prev_sat>0 else None, delta_color=get_delta_color(cur_sat, prev_sat))
            
            def get_wait(d): return d['wait_time_days'].mean() if not d.empty and 'wait_time_days' in d.columns else 0
            cur_wait, prev_wait = get_wait(df_cur), get_wait(df_prev)
            kpi5.metric("Avg Wait Time (days)", f"{cur_wait:.1f}", delta=f"{cur_wait - prev_wait:.1f}" if prev_wait>0 else None, delta_color=get_delta_color(cur_wait, prev_wait, False))
            
            col1, col2 = st.columns([6, 4])
            with col1:
                trend_df = filtered_df.groupby(['Year', 'Month_Num', 'Month_Name']).size().reset_index(name='Appointments')
                trend_df = trend_df.sort_values(['Year', 'Month_Num'])
                fig_trend = px.line(trend_df, x='Month_Name', y='Appointments', color='Year', title="Monthly Appointment Trend")
                fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_trend, use_container_width=True)
            with col2:
                if 'attended' in filtered_df.columns:
                    att_df = filtered_df['attended'].value_counts().reset_index()
                    att_df.columns = ['Attended', 'Count']
                    att_df['Attended'] = att_df['Attended'].astype(str).map({'True':'Yes', 'False':'No', 'Yes':'Yes', 'No':'No'})
                    fig_pie = px.pie(att_df, names='Attended', values='Count', hole=0.5, title="Attendance Breakdown", color='Attended', color_discrete_map={'Yes':'green', 'No':'coral'}, template="plotly_white")
                    fig_pie.update_traces(textinfo='percent+label')
                    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), annotations=[dict(text=f"Total<br>{len(filtered_df)}", x=0.5, y=0.5, showarrow=False)])
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            col3, col4, col5 = st.columns(3)
            with col3:
                if 'appointment_type' in filtered_df.columns:
                    type_df = filtered_df['appointment_type'].value_counts().reset_index()
                    type_df.columns = ['Type', 'Count']
                    fig_type = px.bar(type_df, y='Type', x='Count', orientation='h', title="Appointments by Type", color='Type', template="plotly_white")
                    fig_type.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), showlegend=False)
                    fig_type.update_yaxes(categoryorder='total ascending')
                    st.plotly_chart(fig_type, use_container_width=True)
            with col4:
                if 'referral_source' in filtered_df.columns:
                    ref_df = filtered_df['referral_source'].value_counts().reset_index()
                    ref_df.columns = ['Source', 'Count']
                    fig_ref = px.bar(ref_df, y='Source', x='Count', orientation='h', title="Patient Referral Sources", template="plotly_white")
                    fig_ref.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    fig_ref.update_yaxes(categoryorder='total ascending')
                    st.plotly_chart(fig_ref, use_container_width=True)
            with col5:
                if 'satisfaction_score' in filtered_df.columns:
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number", value=filtered_df['satisfaction_score'].mean(), title={'text': "Avg Satisfaction Score", 'font': {'size': 14, 'color': '#1F3864'}},
                        gauge={'axis': {'range': [0, 5]}, 'bar': {'color': "#1F3864"}, 'steps': [{'range': [0, 3], 'color': "red"}, {'range': [3, 4], 'color': "yellow"}, {'range': [4, 5], 'color': "green"}]}
                    ))
                    fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig_gauge, use_container_width=True)
            
            if 'DayOfWeek' in filtered_df.columns and 'Month_Num' in filtered_df.columns:
                heat_df = filtered_df.groupby(['DayOfWeek', 'Month_Name', 'Month_Num']).size().reset_index(name='Count')
                heat_df = heat_df.sort_values('Month_Num')
                heat_pivot = heat_df.pivot(index='DayOfWeek', columns='Month_Name', values='Count').fillna(0)
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heat_pivot = heat_pivot.reindex(index=days_order)
                fig_heat = px.imshow(heat_pivot, title="Appointments by Day of Week vs Month", color_continuous_scale="Blues", template="plotly_white", aspect="auto")
                fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                st.plotly_chart(fig_heat, use_container_width=True)
        except Exception as e:
            st.warning(f"Chart could not be rendered — check data filters. ({e})")

# ---------------------------------------------------------
# PAGE 3: DEPARTMENT & THERAPIST
# ---------------------------------------------------------
elif selected_page == "Department & Therapist":
    st.title("Department & Therapist Analysis")
    if not check_empty(filtered_df):
        try:
            col1, col2 = st.columns(2)
            with col1:
                if 'department' in filtered_df.columns and 'satisfaction_score' in filtered_df.columns:
                    dept_df = filtered_df.groupby('department').agg(Count=('patient_id','count'), Avg_Sat=('satisfaction_score','mean')).reset_index()
                    fig_dept = go.Figure()
                    fig_dept.add_trace(go.Bar(x=dept_df['department'], y=dept_df['Count'], name='Appointments', marker_color='#2E75B6'))
                    fig_dept.add_trace(go.Scatter(x=dept_df['department'], y=dept_df['Avg_Sat'], name='Avg Satisfaction', yaxis='y2', mode='lines+markers', marker_color='red'))
                    fig_dept.update_layout(title="Department Performance & Satisfaction", template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'),
                                           yaxis=dict(title='Appointments'), yaxis2=dict(title='Avg Satisfaction', overlaying='y', side='right', range=[0,5]))
                    st.plotly_chart(fig_dept, use_container_width=True)
            with col2:
                if 'department' in filtered_df.columns and 'revenue' in filtered_df.columns:
                    tree_df = filtered_df.groupby('department').agg(Revenue=('revenue','sum'), Att_Rate=('attended','mean')).reset_index()
                    tree_df['Att_Rate'] = tree_df['Att_Rate'] * 100
                    fig_tree = px.treemap(tree_df, path=[px.Constant('Departments'), 'department'], values='Revenue', color='Att_Rate', color_continuous_scale='RdYlGn', title="Revenue & Attendance by Department", template="plotly_white")
                    fig_tree.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_tree, use_container_width=True)
            
            st.markdown("### Therapist Performance Table")
            if 'therapist_name' in filtered_df.columns:
                def is_crisis(val): return 'crisis' in str(val).lower() or 'emergency' in str(val).lower()
                filtered_df['is_crisis'] = filtered_df['appointment_type'].apply(is_crisis) if 'appointment_type' in filtered_df.columns else False
                
                tdf = filtered_df.groupby('therapist_name').agg(
                    Total_Sessions=('patient_id', 'count'),
                    Att_Rate=('attended', 'mean'),
                    Avg_Sat=('satisfaction_score', 'mean'),
                    Rev_Gen=('revenue', 'sum'),
                    Crisis_Sess=('is_crisis', 'sum')
                ).reset_index()
                
                tdf['Att_Rate'] = tdf['Att_Rate'] * 100
                tdf['Performance Band'] = pd.cut(tdf['Avg_Sat'], bins=[0, 3.5, 4.2, 5.0], labels=['Needs Improvement', 'Medium', 'High'])
                tdf = tdf.sort_values('Total_Sessions', ascending=False)
                
                def color_band(val):
                    if val == 'High': return 'background-color: lightgreen'
                    elif val == 'Medium': return 'background-color: lightyellow'
                    elif val == 'Needs Improvement': return 'background-color: lightcoral'
                    return ''
                
                st.dataframe(tdf.style.map(color_band, subset=['Performance Band']),
                             column_config={
                                 "therapist_name": "Therapist Name",
                                 "Total_Sessions": "Total Sessions",
                                 "Att_Rate": st.column_config.ProgressColumn("Attendance Rate", min_value=0, max_value=100, format="%.1f%%"),
                                 "Avg_Sat": st.column_config.NumberColumn("Avg Satisfaction", format="%.2f"),
                                 "Rev_Gen": st.column_config.NumberColumn("Revenue Generated", format="₹%d"),
                                 "Crisis_Sess": "Crisis Sessions",
                                 "Performance Band": "Performance Band"
                             }, use_container_width=True)
                
                csv = tdf.to_csv(index=False).encode('utf-8')
                st.download_button("Download Therapist Data as CSV", data=csv, file_name="therapist_performance.csv", mime="text/csv")
            
            col3, col4 = st.columns(2)
            with col3:
                if 'therapist_name' in filtered_df.columns:
                    fig_scat = px.scatter(tdf, x='Total_Sessions', y='Avg_Sat', size='Rev_Gen', color='Performance Band', hover_name='therapist_name', title="Therapist Workload vs Satisfaction", template="plotly_white", trendline="ols")
                    fig_scat.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_scat, use_container_width=True)
            with col4:
                if 'therapist_name' in filtered_df.columns:
                    crisis_df = tdf[['therapist_name', 'Crisis_Sess']].sort_values('Crisis_Sess', ascending=True).tail(10)
                    colors = ['#2E75B6'] * len(crisis_df)
                    if len(colors) > 0: colors[-1] = 'coral'
                    fig_cris = go.Figure(go.Bar(x=crisis_df['Crisis_Sess'], y=crisis_df['therapist_name'], orientation='h', marker_color=colors))
                    fig_cris.update_layout(title="Top Crisis Interventions by Therapist", template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_cris, use_container_width=True)
        except Exception as e:
            st.warning(f"Chart could not be rendered — check data filters. ({e})")

# ---------------------------------------------------------
# PAGE 4: DEMOGRAPHICS & GEOGRAPHY
# ---------------------------------------------------------
elif selected_page == "Demographics & Geography":
    st.title("Demographics & Geography")
    if not check_empty(filtered_df):
        try:
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'age_group' in filtered_df.columns:
                    fig_age = px.pie(filtered_df, names='age_group', hole=0.5, title="Age Group Distribution", template="plotly_white")
                    fig_age.update_traces(textinfo='percent+label')
                    fig_age.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), showlegend=False)
                    st.plotly_chart(fig_age, use_container_width=True)
            with col2:
                if 'patient_gender' in filtered_df.columns:
                    fig_gen = px.pie(filtered_df, names='patient_gender', hole=0.5, title="Gender Distribution", template="plotly_white")
                    fig_gen.update_traces(textinfo='percent+label')
                    fig_gen.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), showlegend=False)
                    st.plotly_chart(fig_gen, use_container_width=True)
            with col3:
                if 'appointment_type' in filtered_df.columns:
                    fig_typ = px.pie(filtered_df, names='appointment_type', title="Appointment Type Split", template="plotly_white")
                    fig_typ.update_traces(textinfo='percent+label')
                    fig_typ.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), showlegend=False)
                    st.plotly_chart(fig_typ, use_container_width=True)
            
            col4, col5 = st.columns(2)
            with col4:
                if 'city' in filtered_df.columns:
                    city_df = filtered_df.groupby('city').agg(Count=('patient_id','count'), Rev=('revenue','sum')).reset_index()
                    city_df['Rev_Per_Appt'] = city_df['Rev'] / city_df['Count']
                    city_df = city_df.sort_values('Count', ascending=True)
                    fig_city = go.Figure()
                    fig_city.add_trace(go.Bar(y=city_df['city'], x=city_df['Count'], name='Appointments', orientation='h', marker_color='#1F3864'))
                    fig_city.add_trace(go.Scatter(y=city_df['city'], x=city_df['Rev_Per_Appt'], name='Rev/Appt (₹)', mode='lines+markers', xaxis='x2'))
                    fig_city.update_layout(title="Appointments by City & Rev per Appt", template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'),
                                           xaxis2=dict(title='Rev per Appt', overlaying='x', side='top'))
                    st.plotly_chart(fig_city, use_container_width=True)
            with col5:
                if 'city' in filtered_df.columns and 'department' in filtered_df.columns:
                    fig_sun = px.sunburst(filtered_df, path=['department', 'city'], title="City -> Department Drill Down", template="plotly_white")
                    fig_sun.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_sun, use_container_width=True)
            
            if 'referral_source' in filtered_df.columns and 'attended' in filtered_df.columns:
                filtered_df['Attended_Str'] = filtered_df['attended'].astype(str).map({'True':'Attended', 'False':'Not Attended', 'Yes':'Attended', 'No':'Not Attended'})
                ref_eff = filtered_df.groupby(['referral_source', 'Attended_Str']).size().reset_index(name='Count')
                fig_refeff = px.bar(ref_eff, x='referral_source', y='Count', color='Attended_Str', barmode='group', text_auto='.0f', title="Referral Source vs Attendance Outcome", color_discrete_map={'Attended':'#2E75B6', 'Not Attended':'coral'}, template="plotly_white")
                fig_refeff.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                st.plotly_chart(fig_refeff, use_container_width=True)
                
            if 'age_group' in filtered_df.columns and 'appointment_type' in filtered_df.columns:
                age_type = filtered_df.groupby(['age_group', 'appointment_type']).size().reset_index(name='Count')
                fig_agetype = px.bar(age_type, x='age_group', y='Count', color='appointment_type', barmode='stack', title="Age Group vs Appointment Type", template="plotly_white")
                fig_agetype.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                st.plotly_chart(fig_agetype, use_container_width=True)
        except Exception as e:
            st.warning(f"Chart could not be rendered — check data filters. ({e})")

# ---------------------------------------------------------
# PAGE 5: FINANCIAL ANALYSIS
# ---------------------------------------------------------
elif selected_page == "Financial Analysis":
    st.title("Financial Analysis")
    if not check_empty(filtered_df):
        try:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            if 'revenue' in filtered_df.columns and 'session_fee' in filtered_df.columns and 'payment_status' in filtered_df.columns:
                tot_rev = filtered_df['revenue'].sum()
                kpi1.metric("Total Revenue Collected", format_indian_currency(tot_rev))
                
                leakage_df = filtered_df[filtered_df['payment_status'].isin(['Pending', 'Waived'])]
                leakage = leakage_df['session_fee'].sum()
                kpi2.metric("Revenue Leakage", format_indian_currency(leakage), delta="-"+format_indian_currency(leakage), delta_color="inverse")
                
                total_billed = filtered_df['session_fee'].sum()
                coll_rate = (tot_rev / total_billed * 100) if total_billed > 0 else 0
                kpi3.metric("Collection Rate", f"{coll_rate:.1f}%")
                
                avg_fee = filtered_df['session_fee'].mean()
                kpi4.metric("Average Session Fee", format_indian_currency(avg_fee))
                
                col1, col2 = st.columns(2)
                with col1:
                    pay_mon = filtered_df.groupby(['Month_Name', 'Month_Num', 'payment_status'])['session_fee'].sum().reset_index()
                    pay_mon = pay_mon.sort_values('Month_Num')
                    fig_paymon = px.bar(pay_mon, x='Month_Name', y='session_fee', color='payment_status', title="Monthly Revenue by Payment Status", template="plotly_white", color_discrete_map={'Paid': 'green', 'Pending': 'orange', 'Waived': 'red'})
                    fig_paymon.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'), barmode='stack')
                    st.plotly_chart(fig_paymon, use_container_width=True)
                with col2:
                    paid = filtered_df[filtered_df['payment_status']=='Paid']['session_fee'].sum()
                    pending = filtered_df[filtered_df['payment_status']=='Pending']['session_fee'].sum()
                    waived = filtered_df[filtered_df['payment_status']=='Waived']['session_fee'].sum()
                    wf_fig = go.Figure(go.Waterfall(
                        name="Revenue Flow", orientation="v",
                        measure=["relative", "relative", "relative", "total"],
                        x=["Total Billed", "Pending", "Waived", "Net Collected"],
                        textposition="outside",
                        text=[format_indian_currency(total_billed), format_indian_currency(-pending), format_indian_currency(-waived), format_indian_currency(paid)],
                        y=[total_billed, -pending, -waived, paid],
                        connector={"line":{"color":"rgb(63, 63, 63)"}},
                        decreasing={"marker":{"color":"coral"}},
                        increasing={"marker":{"color":"#2E75B6"}},
                        totals={"marker":{"color":"green"}}
                    ))
                    wf_fig.update_layout(title="Revenue Flow", paper_bgcolor="rgba(0,0,0,0)", template="plotly_white", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(wf_fig, use_container_width=True)
                
                col3, col4 = st.columns(2)
                with col3:
                    pay_dist = filtered_df.groupby('payment_status')['session_fee'].sum().reset_index()
                    fig_paypie = px.pie(pay_dist, names='payment_status', values='session_fee', title="Payment Status Distribution", template="plotly_white", color='payment_status', color_discrete_map={'Paid': 'green', 'Pending': 'orange', 'Waived': 'red'})
                    fig_paypie.update_traces(textinfo='percent+label')
                    fig_paypie.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_paypie, use_container_width=True)
                with col4:
                    if 'department' in filtered_df.columns:
                        leak_dept = leakage_df.groupby('department')['session_fee'].sum().reset_index().sort_values('session_fee', ascending=True)
                        fig_leak = px.bar(leak_dept, y='department', x='session_fee', orientation='h', title="Revenue Leakage by Department", template="plotly_white", color='session_fee', color_continuous_scale='Reds')
                        fig_leak.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                        st.plotly_chart(fig_leak, use_container_width=True)
                
                if 'WeekNum' in filtered_df.columns:
                    week_rev = filtered_df.groupby(['Year', 'WeekNum'])['revenue'].sum().reset_index()
                    fig_week = px.line(week_rev, x='WeekNum', y='revenue', color='Year', title="Weekly Revenue Trend", template="plotly_white")
                    avg_rev = week_rev['revenue'].mean()
                    fig_week.add_hline(y=avg_rev, line_dash="dash", line_color="gray", annotation_text="Avg Weekly Revenue")
                    fig_week.update_layout(paper_bgcolor="rgba(0,0,0,0)", title_font=dict(size=14, color='#1F3864'))
                    st.plotly_chart(fig_week, use_container_width=True)
                
                st.markdown("### Detailed Financial Table")
                fin_table = filtered_df.pivot_table(index='department', columns='payment_status', values='session_fee', aggfunc='sum', fill_value=0, margins=True, margins_name='Grand Total')
                
                req_cols = ['Paid', 'Pending', 'Waived']
                for c in req_cols:
                    if c not in fin_table.columns: fin_table[c] = 0
                
                fin_table['Total Billed'] = fin_table['Paid'] + fin_table['Pending'] + fin_table['Waived']
                fin_table['Collection Rate %'] = (fin_table['Paid'] / fin_table['Total Billed'] * 100).fillna(0)
                fin_table['Leakage ₹'] = fin_table['Pending'] + fin_table['Waived']
                
                fin_table = fin_table.reset_index()
                
                st.dataframe(fin_table, column_config={
                    "department": "Department",
                    "Total Billed": st.column_config.NumberColumn("Total Billed", format="₹%d"),
                    "Paid": st.column_config.NumberColumn("Paid", format="₹%d"),
                    "Pending": st.column_config.NumberColumn("Pending", format="₹%d"),
                    "Waived": st.column_config.NumberColumn("Waived", format="₹%d"),
                    "Collection Rate %": st.column_config.NumberColumn("Collection Rate %", format="%.1f%%"),
                    "Leakage ₹": st.column_config.NumberColumn("Leakage ₹", format="₹%d")
                }, use_container_width=True)
                
                csv_fin = fin_table.to_csv(index=False).encode('utf-8')
                st.download_button("Download Financial Table CSV", data=csv_fin, file_name="financial_summary.csv", mime="text/csv")
        except Exception as e:
            st.warning(f"Chart could not be rendered — check data filters. ({e})")
