import csv
import json
from datetime import datetime, time

def process_attendance(csv_file_path, json_file_path, error_log_path):
    data = []
    error_lines = []

    # Define shift times and rules
    shift_start = time(9, 0)
    shift_end = time(18, 0)
    late_entry_limit = time(9, 30)
    early_exit_limit = time(17, 0)

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            parts = line.strip().split()

            # --- Validate row structure ---
            if len(parts) < 5:
                error_lines.append(f"Line {line_number}: Missing columns → {line.strip()}")
                continue
            
            elif len(parts) > 6:
                error_lines.append(f"Line {line_number}: Too many columns → {line.strip()}")
                continue

            emp_code = parts[0]
            first_name = parts[1]
            last_name = parts[2]

            # Find timestamp
            timestamp_index = None
            for i, p in enumerate(parts):
                if p.isdigit() and len(p) > 6:  # basic numeric timestamp check
                    timestamp_index = i
                    break

            if timestamp_index is None:
                error_lines.append(f"Line {line_number}: Missing or invalid timestamp → {line.strip()}")
                continue

            timestamp = parts[timestamp_index]
            device = " ".join(parts[timestamp_index + 1:])

            # --- Validate timestamp ---
            try:
                ts = int(timestamp)
                dt = datetime.fromtimestamp(ts)
                timestamp_readable = dt.isoformat()
                current_time = dt.time()
            except Exception as e:
                error_lines.append(f"Line {line_number}: Invalid timestamp '{timestamp}' → {e}")
                continue

            # --- Determine status ---
            if current_time > late_entry_limit and current_time < time(12, 0):
                status = "Late Entry"
            elif current_time < early_exit_limit and current_time > time(12, 0):
                status = "Early Exit"
            else:
                status = "On Time"

            # --- Add valid record ---
            data.append({
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "timestamp": timestamp_readable,
                "device": device,
                "shift_period": "09 AM - 6 PM",
                "status": status
            })

    # --- Write JSON output ---
    with open(json_file_path, "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=4)

    # --- Write error log ---
    if error_lines:
        with open(error_log_path, "w", encoding="utf-8") as err_file:
            err_file.write("\n".join(error_lines))
        print(f"⚠️ Some rows skipped. See log: {error_log_path}")
    else:
        print("✅ All rows processed successfully (no errors).")

    print(f"✅ JSON file created: {json_file_path}")



if __name__ == "__main__":
    csv_path = "attendance_logs/attendance_logs_2.log"
    json_path = "attendance.json"
    error_log = "error_log.txt"
    process_attendance(csv_path, json_path, error_log)
