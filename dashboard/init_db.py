import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = 'pulsepro.db'
CSV_PATH = '../Attendance_Report_Sheet.csv'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('''
    CREATE TABLE employees (
        emp_id TEXT PRIMARY KEY,
        name TEXT,
        department TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE daily_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        late_flag BOOLEAN,
        status TEXT DEFAULT 'Pending'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE monthly_counters (
        emp_id TEXT,
        month_year TEXT,
        late_count INTEGER,
        last_warning_date TEXT,
        PRIMARY KEY (emp_id, month_year)
    )
    ''')
    
    # Parse CSV and group by Employee and Date
    if not os.path.exists(CSV_PATH):
        print(f"File {CSV_PATH} not found. Please ensure it exists.")
        return
        
    grouped_data = {}
    employees = {}
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emp_id = row['Employee ID']
            name = row['Name']
            date = row['Date']
            time_str = row['Time']
            status = row['Punch Status']
            
            employees[emp_id] = name
            key = f"{emp_id}_{date}"
            
            if key not in grouped_data:
                grouped_data[key] = {'emp_id': emp_id, 'date': date, 'punches': []}
            grouped_data[key]['punches'].append({'time': time_str, 'status': status})
            
    # Process Grouped Data
    daily_records = []
    late_counters = {} # emp_id -> count
    
    for key, data in grouped_data.items():
        emp_id = data['emp_id']
        date_val = data['date']
        punches = data['punches']
        
        # We need to sort times to find earliest and latest.
        # Times are in '05:30 PM' format
        def parse_time(ts):
            return datetime.strptime(ts, '%I:%M %p')
            
        in_punches = [p['time'] for p in punches if p['status'].upper() == 'IN']
        out_punches = [p['time'] for p in punches if p['status'].upper() == 'OUT']
        
        in_punches.sort(key=parse_time)
        out_punches.sort(key=parse_time)
        
        check_in = in_punches[0] if in_punches else None
        check_out = out_punches[-1] if out_punches else None
        
        late_flag = False
        if check_in:
            in_dt = parse_time(check_in)
            if in_dt.hour >= 11:
                late_flag = True
                
        daily_records.append((emp_id, date_val, check_in, check_out, late_flag, 'Pending'))
        
        if late_flag:
            late_counters[emp_id] = late_counters.get(emp_id, 0) + 1
            
    # Insert Employees
    emp_tuples = [(eid, name, 'General') for eid, name in employees.items()]
    cursor.executemany('INSERT INTO employees VALUES (?, ?, ?)', emp_tuples)
    
    # Insert Daily Records
    cursor.executemany('INSERT INTO daily_records (emp_id, date, check_in, check_out, late_flag, status) VALUES (?, ?, ?, ?, ?, ?)', daily_records)
    
    # Insert Counters
    month_year = datetime.now().strftime('%B %Y')
    counter_tuples = []
    for eid in employees.keys():
        count = late_counters.get(eid, 0)
        counter_tuples.append((eid, month_year, count, None))
        
    cursor.executemany('INSERT INTO monthly_counters VALUES (?, ?, ?, ?)', counter_tuples)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully with REAL data!")

if __name__ == '__main__':
    init_db()
