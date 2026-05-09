import csv
import re
from datetime import datetime

# Input and Output files
INPUT_FILE = '../Attendance Muster Report (2).xlsx - Sheet0.csv'
OUTPUT_FILE = '../Attendance_Report_Sheet.csv'

def convert_to_flat_format():
    flat_records = []
    
    current_emp_id = None
    current_emp_name = None
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        lines = list(reader)
        
    for i in range(len(lines)):
        row = lines[i]
        if not row:
            continue
            
        # Check if this row is an Employee Header
        # The line before an employee data usually starts with "Employee  No"
        if row[0].strip() == 'Employee  No':
            # The next row contains the employee details
            if i + 1 < len(lines):
                emp_row = lines[i + 1]
                current_emp_id = emp_row[0].strip()
                current_emp_name = emp_row[1].strip()
                
        # Check if this row is an attendance record
        # Attendance records usually start with a serial number (1 to 31)
        elif current_emp_id and row[0].strip().isdigit():
            sno = row[0].strip()
            att_date = row[1].strip()
            in_time_str = row[4].strip()
            out_time_str = row[5].strip()
            
            # Format: '02 Feb 2026 12:11'
            if in_time_str:
                # Some dates are just the time if they didn't include date, but looking at data it's full string
                try:
                    dt_in = datetime.strptime(in_time_str, '%d %b %Y %H:%M')
                    date_val = dt_in.strftime('%Y-%m-%d')
                    time_val = dt_in.strftime('%I:%M %p') # Format as 12:11 PM
                    flat_records.append([current_emp_id, current_emp_name, date_val, time_val, 'IN'])
                except ValueError:
                    pass # Ignore unparseable or blank times
                    
            if out_time_str:
                try:
                    dt_out = datetime.strptime(out_time_str, '%d %b %Y %H:%M')
                    date_val = dt_out.strftime('%Y-%m-%d')
                    time_val = dt_out.strftime('%I:%M %p')
                    
                    # Prevent duplicate IN/OUT if in_time == out_time
                    if out_time_str != in_time_str:
                        flat_records.append([current_emp_id, current_emp_name, date_val, time_val, 'OUT'])
                except ValueError:
                    pass
                    
    # Write to the required flat format
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Employee ID', 'Name', 'Date', 'Time', 'Punch Status'])
        writer.writerows(flat_records)
        
    print(f"Successfully converted {len(lines)} raw lines into {len(flat_records)} flat punch records in {OUTPUT_FILE}")

if __name__ == '__main__':
    convert_to_flat_format()
