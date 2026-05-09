import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime

# Configure page
st.set_page_config(page_title="PulsePro AI Dashboard", page_icon="⏱️", layout="wide")

# Auto-refresh logic (every 60 seconds)
# Streamlit experimental rerun can be simulated using st_autorefresh if installed, 
# but we can use a simpler approach or just rely on a manual button for this prototype,
# or we use st.empty and a while loop, or query parameters.
# A simpler auto-refresh pattern in Streamlit:
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# We will use a standard markdown meta tag for auto-refresh as a hack, or just a simple button.
st.markdown(
    """
    <meta http-equiv="refresh" content="60">
    <style>
    .big-font { font-size:30px !important; font-weight: bold; }
    .safe { color: #28a745; font-weight: bold; padding: 5px; border-radius: 5px; background: #e6f4ea; }
    .risk { color: #ffc107; font-weight: bold; padding: 5px; border-radius: 5px; background: #fff8e1; }
    .critical { color: #dc3545; font-weight: bold; padding: 5px; border-radius: 5px; background: #fce8e6; }
    </style>
    """,
    unsafe_allow_html=True
)

DB_PATH = "pulsepro.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_daily_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM daily_records")
    latest_date_row = cursor.fetchone()
    today = latest_date_row[0] if latest_date_row and latest_date_row[0] else datetime.now().strftime('%Y-%m-%d')
    
    query = f"SELECT late_flag, COUNT(*) as count FROM daily_records WHERE date='{today}' GROUP BY late_flag"
    df = pd.read_sql(query, conn)
    conn.close()
    
    on_time = 0
    late = 0
    for _, row in df.iterrows():
        if row['late_flag'] == 1:
            late = row['count']
        else:
            on_time = row['count']
    return on_time, late, today

def fetch_strike_rankings():
    conn = get_connection()
    query = """
        SELECT e.name, m.late_count, d.department, m.emp_id
        FROM monthly_counters m
        JOIN employees e ON m.emp_id = e.emp_id
        WHERE m.late_count >= 2
        ORDER BY m.late_count DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def fetch_all_employees():
    conn = get_connection()
    query = """
        SELECT e.name, m.late_count, e.emp_id
        FROM employees e
        LEFT JOIN monthly_counters m ON e.emp_id = m.emp_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df['late_count'] = df['late_count'].fillna(0).astype(int)
    return df

def mark_excused(emp_id, target_date):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if late today
    cursor.execute(f"SELECT late_flag FROM daily_records WHERE emp_id='{emp_id}' AND date='{target_date}'")
    res = cursor.fetchone()
    if res and res[0] == 1:
        # Update daily record
        cursor.execute(f"UPDATE daily_records SET late_flag=0, status='Excused' WHERE emp_id='{emp_id}' AND date='{target_date}'")
        # Decrement counter
        cursor.execute(f"UPDATE monthly_counters SET late_count = late_count - 1 WHERE emp_id='{emp_id}' AND late_count > 0")
        conn.commit()
    conn.close()

# UI Layout
st.title("⏱️ PulsePro AI - Real-Time Dashboard")
st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Top Cards
on_time, late, latest_date = fetch_daily_stats()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div style="background:#e6f4ea;padding:20px;border-radius:10px;">', unsafe_allow_html=True)
    st.metric(label=f"✅ On-Time Arrivals ({latest_date})", value=on_time)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div style="background:#fce8e6;padding:20px;border-radius:10px;">', unsafe_allow_html=True)
    st.metric(label=f"🚨 Late Arrivals ({latest_date})", value=late)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.button("🔄 Manual Refresh")

st.markdown("---")

# Main Content
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("⚠️ Employees at Risk (2+ Strikes)")
    risk_df = fetch_strike_rankings()
    
    if risk_df.empty:
        st.success("No employees currently at risk!")
    else:
        for _, row in risk_df.iterrows():
            with st.container():
                rc1, rc2, rc3 = st.columns([3, 1, 1])
                rc1.write(f"**{row['name']}** ({row['department']})")
                
                badge_class = "critical" if row['late_count'] >= 3 else "risk"
                status = "CRITICAL" if row['late_count'] >= 3 else "AT RISK"
                rc2.markdown(f'<span class="{badge_class}">{status} (Strike {row["late_count"]})</span>', unsafe_allow_html=True)
                
                if st.button("Mark Excused Today", key=f"excuse_{row['emp_id']}"):
                    mark_excused(row['emp_id'], latest_date)
                    st.rerun()
                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

with colB:
    st.subheader("👥 Live Status Board")
    all_df = fetch_all_employees()
    
    for _, row in all_df.iterrows():
        count = row['late_count']
        if count <= 1:
            badge = '<span class="safe">Safe</span>'
        elif count == 2:
            badge = '<span class="risk">At Risk</span>'
        else:
            badge = '<span class="critical">Critical</span>'
            
        st.markdown(f"{row['name']} &mdash; {badge}", unsafe_allow_html=True)

