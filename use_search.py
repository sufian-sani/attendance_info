import os
import json
from datetime import datetime

def load_attendance(file_name='attendance_summary.json'):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_name}' not found in {current_dir}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON file '{file_name}'")
        return []

    summary = []
    if isinstance(data, dict):
        for date_str, records in data.items():
            try:
                record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            for row in records:
                row['date'] = record_date
                summary.append(row)
    else:
        print("Error: JSON structure is not a dictionary of dates")
    return summary

# Search function
def search_attendance(summary, emp_code=None, date=None):
    results = summary
    if emp_code:
        results = [r for r in results if emp_code == r.get('emp_code', '')]
    if date:
        results = [r for r in results if r['date'] == date]
    return results

if __name__ == "__main__":
    attendance = load_attendance()

    if not attendance:
        print("No attendance data to search.")
        exit(1)

    # Take input from user
    emp_code = input("Enter employee code (or leave blank to skip): ").strip()
    date_input = input("Enter date (YYYY-MM-DD) (or leave blank to skip): ").strip()

    date_search = None
    if date_input:
        try:
            date_search = datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            exit(1)

    found_records = search_attendance(attendance, emp_code=emp_code or None, date=date_search)

    if found_records:
        print(f"\nFound {len(found_records)} record(s):")
        for r in found_records:
            print(f"Emp Code: {r.get('emp_code','')}, Date: {r.get('date','')}, "
                  f"First Punch: {r.get('first_punch','')}, Last Punch: {r.get('last_punch','')}, "
                  f"Total Punches: {r.get('total_punches','')}, Working Hours: {r.get('working_hours','')}, "
                  f"Late Entry: {r.get('late_entry','')}, Early Exit: {r.get('early_exit','')}, "
                  f"Shift: {r.get('shift_period','')}")
    else:
        print("\nNo records found.")
