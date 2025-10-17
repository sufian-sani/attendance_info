import csv
import json
from datetime import datetime, time, timedelta
from collections import defaultdict
import os

# --- Shift rules ---
SHIFT_START = time(9, 0)
SHIFT_END = time(18, 0)
LATE_ENTRY_LIMIT = time(9, 30)
EARLY_EXIT_LIMIT = time(17, 0)

# Bangladesh UTC offset
BDT_OFFSET = timedelta(hours=6)


def convert_to_bdt(ts):
    """Convert Unix timestamp to Bangladesh datetime."""
    return datetime.utcfromtimestamp(ts) + BDT_OFFSET


def process_attendance(csv_file_path, json_file_path, error_log_path):
    data = []
    error_lines = []

    # --- Step 1: Read CSV and parse data ---
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return

    with open(csv_file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            parts = line.strip().split()

            # Validate row structure
            if len(parts) < 5:
                error_lines.append(f"Line {line_number}: Missing columns → {line.strip()}")
                continue
            elif len(parts) > 6:
                error_lines.append(f"Line {line_number}: Too many columns → {line.strip()}")
                continue

            emp_code, first_name, last_name = parts[0], parts[1], parts[2]

            # Detect timestamp
            timestamp_index = next((i for i, p in enumerate(parts) if p.isdigit() and len(p) > 6), None)
            if timestamp_index is None:
                error_lines.append(f"Line {line_number}: Missing or invalid timestamp → {line.strip()}")
                continue

            timestamp_str = parts[timestamp_index]
            device = " ".join(parts[timestamp_index + 1:])

            try:
                dt = convert_to_bdt(int(timestamp_str))
            except Exception as e:
                error_lines.append(f"Line {line_number}: Invalid timestamp '{timestamp_str}' → {e}")
                continue

            data.append({
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "datetime": dt,
                "device": device
            })

    # --- Step 2: Remove duplicate entries (emp_code, datetime, device) ---
    unique_data = {(d["emp_code"], d["datetime"], d["device"]): d for d in data}
    data = list(unique_data.values())

    # --- Step 3: Group by employee and date ---
    grouped = defaultdict(list)
    for record in data:
        key = (record["emp_code"], record["datetime"].date())
        grouped[key].append(record)

    # --- Step 4: Process daily summaries ---
    final_output = defaultdict(list)

    for (emp_code, date_), records in grouped.items():
        # Sort punches by time
        records.sort(key=lambda r: r["datetime"])
        first_punch = records[0]["datetime"]
        last_punch = records[-1]["datetime"]
        total_punches = len(records)

        # Working hours
        if total_punches > 1:
            duration = last_punch - first_punch
            hours, remainder = divmod(duration.seconds, 3600)
            minutes = remainder // 60
            working_hours = f"{hours:02}:{minutes:02}"
        else:
            working_hours = "00:00"

        # Late/Early flags
        late_entry = 1 if first_punch.time() > LATE_ENTRY_LIMIT else 0
        early_exit = 1 if last_punch.time() < EARLY_EXIT_LIMIT else 0

        # Append record
        final_output[str(date_)].append({
            "emp_code": emp_code,
            "first_punch": first_punch.strftime("%H:%M"),
            "last_punch": last_punch.strftime("%H:%M"),
            "total_punches": total_punches,
            "working_hours": working_hours,
            "late_entry": late_entry,
            "early_exit": early_exit,
            "shift_period": "09:00 - 18:00"
        })

    # --- Step 5: Sort output by date and employee code ---
    sorted_output = {
        date: sorted(records, key=lambda x: x["emp_code"])
        for date, records in sorted(final_output.items())
    }

    # --- Step 6: Write JSON output ---
    with open(json_file_path, "w", encoding="utf-8") as out_file:
        json.dump(sorted_output, out_file, indent=4)

    # --- Step 7: Write error log if any ---
    if error_lines:
        with open(error_log_path, "w", encoding="utf-8") as err_file:
            err_file.write("\n".join(error_lines))
        print(f"⚠️ Some rows skipped. Check: {error_log_path}")
    else:
        print("✅ All rows processed successfully (no errors).")

    print(f"✅ JSON file created: {json_file_path}")


if __name__ == "__main__":
    csv_path = "attendance_logs/attendance_logs_1.log"
    json_path = "attendance_summary.json"
    error_log = "error_log.txt"
    process_attendance(csv_path, json_path, error_log)
