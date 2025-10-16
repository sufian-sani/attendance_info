import csv
import json
from datetime import datetime, time

def process_attendance(csv_file_path, json_file_path):
    # write your code here
    # fieldnames = ['emp_code', 'first_name', 'last_name', 'timestamp', 'device']
    data = []
        # Define shift times
    shift_start = time(9, 0)
    shift_end = time(18, 0)
    late_entry_limit = time(9, 30)
    early_exit_limit = time(17, 0)

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            emp_code = parts[0]
            first_name = parts[1]
            last_name = parts[2]

            # Find timestamp index
            timestamp_index = None
            for i, p in enumerate(parts):
                if p.isdigit() and len(p) > 6:
                    timestamp_index = i
                    break
            if timestamp_index is None:
                continue

            timestamp = parts[timestamp_index]
            device = " ".join(parts[timestamp_index + 1:])

            # Convert timestamp
            try:
                ts = int(timestamp)
                dt = datetime.fromtimestamp(ts)
                timestamp_readable = dt.isoformat()
                current_time = dt.time()

                # Determine status
                if current_time > late_entry_limit and current_time < time(12, 0):
                    status = "Late Entry"
                elif current_time < early_exit_limit and current_time > time(12, 0):
                    status = "Early Exit"
                else:
                    status = "On Time"

                shift_period = "09 AM - 6 PM"

            except ValueError:
                timestamp_readable = timestamp
                status = "Unknown"
                shift_period = "Unknown"

            data.append({
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "timestamp": timestamp_readable,
                "device": device,
                "shift_period": shift_period,
                "status": status
            })

    # Save to JSON
    with open(json_file_path, "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=4)

    print(f"✅ JSON file created: {json_file_path}")





if __name__ == "__main__":
    csv_path = "attendance_logs/attendance_logs_1.log"
    json_path = "attendance.json"
    process_attendance(csv_path, json_path)
