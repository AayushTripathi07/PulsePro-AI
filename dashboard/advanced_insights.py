import sqlite3
import pandas as pd
from datetime import datetime

# In a real scenario, you would import openai or anthropic here.
# import openai

def get_connection():
    return sqlite3.connect('pulsepro.db') # Assuming it's in the same directory or dashboard/

def fetch_historical_data():
    """
    Fetches the daily records joined with employee info to build up a pattern dataset.
    """
    conn = get_connection()
    query = """
        SELECT d.date, d.emp_id, e.name, e.department, d.check_in, d.late_flag
        FROM daily_records d
        JOIN employees e ON d.emp_id = e.emp_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def generate_insights(df):
    """
    1. Identify employees consistently late on the same day of the week.
    2. Flag departments with highest late correlations.
    3. Generate the summary report prompt.
    """
    if df.empty:
        return "Not enough data to generate insights."
    
    # Convert date to datetime to get the day of the week
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    
    late_df = df[df['late_flag'] == 1]
    
    # Pattern 1: Late on specific days
    # Group by employee and day_of_week
    day_patterns = late_df.groupby(['name', 'day_of_week']).size().reset_index(name='count')
    consistent_lates = day_patterns[day_patterns['count'] >= 2] # Adjust threshold based on dataset size
    
    # Pattern 2: Department correlation
    dept_patterns = late_df.groupby('department').size().reset_index(name='late_count')
    dept_patterns = dept_patterns.sort_values(by='late_count', ascending=False)
    
    # AI Prompt Construction (Zero-shot / Chain-of-Thought style)
    prompt = f"""
    You are an expert HR Data Analyst. Review the following raw insights regarding employee attendance patterns 
    over the past month, and draft a professional, human-like weekly summary report for HR Leadership.
    
    Raw Data:
    - Employees consistently late on specific days: {consistent_lates.to_dict('records')}
    - Late arrivals by department: {dept_patterns.to_dict('records')}
    
    Task:
    1. Summarize the overall health of attendance.
    2. Highlight specific behavioral patterns (e.g., "Jane Doe has a pattern of being late on Mondays").
    3. Provide ONE proactive, actionable HR recommendation based on these patterns (e.g., checking in with specific departments about workload or proposing flexible start times).
    
    Ensure the output reads gracefully and professionally, without sounding like an obvious AI dump. Avoid hallucinating data not present in the Raw Data section.
    """
    
    return prompt

if __name__ == '__main__':
    # Simulating the execution
    # In a live environment, this script runs weekly via n8n cron node, feeding the DB output to the LLM.
    df = fetch_historical_data()
    prompt = generate_insights(df)
    print("----- GENERATED AI PROMPT -----")
    print(prompt)
    print("-------------------------------")
    print("\nNext Step: Pass this prompt to the OpenAI API to generate the final HR Leadership Report.")
