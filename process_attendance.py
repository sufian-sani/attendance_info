import os
import json
from datetime import datetime, time, timedelta
from collections import defaultdict
from zoneinfo import ZoneInfo


# --- Shift Configuration ---
SHIFT_START = time(9, 0)
SHIFT_END = time(18, 0)
LATE_ENTRY_LIMIT = time(9, 30)
EARLY_EXIT_LIMIT = time(17, 0)
SHIFT_PERIOD = "09 AM - 6 PM"


def convert_to_bangladesh_time(timestamp: int) -> datetime:
    """Convert UTC timestamp to Bangladesh Standard Time (UTC+6)."""
    return datetime.fromtimestamp(int(timestamp), tz=ZoneInfo("Asia/Dhaka"))


def determine_status(current_time: time) -> str:
    """Determine attendance status based on punch time."""
    if LATE_ENTRY_LIMIT < current_time < time(12, 0):
        return "Late Entry"
    elif time(12, 0) < current_time < EARLY_EXIT_LIMIT:
        return "Early Exit"
    return "On Time"


def parse_log_line(line: str, line_number: int, errors: list):
    """Parse a single log line safely and return structured data."""
    parts = line.strip().split()

    if len(parts) < 5:
        errors.append(f"Line {line_number}: Missing columns → {line.strip()}")
        return None
    elif len(parts) > 6:
        errors.append(f"Line {line_number}: Too many columns → {line.strip()}")
        return None

    emp_code, first_name, last_name = parts[:3]
    timestamp_index = next((i for i, p in enumerate(parts) if p.isdigit() and len(p) > 6), None)

    if timestamp_index is None:
        errors.append(f"Line {line_number}: Missing or invalid timestamp → {line.strip()}")
        return None

    timestamp = parts[timestamp_index]
    device = " ".join(parts[timestamp_index + 1:])

    try:
        dt_bd = convert_to_bangladesh_time(int(timestamp))
    except Exception as e:
        errors.append(f"Line {line_number}: Invalid timestamp '{timestamp}' → {e}")
        return None

    status = determine_status(dt_bd.time())

    return {
        "emp_code": emp_code,
        "first_name": first_name,
        "last_name": last_name,
        "datetime": dt_bd,
        "device": device,
        "status": status,
        "shift_period": SHIFT_PERIOD,
    }


def summarize_attendance(records):
    """Summarize grouped attendance data for each employee-date."""
    final_output = defaultdict(list)

    for (emp_code, date), punches in records.items():
        punches.sort(key=lambda r: r["datetime"])

        first_punch = punches[0]["datetime"]
        last_punch = punches[-1]["datetime"]
        total_punches = len(punches)

        # Calculate working duration
        if total_punches > 1:
            duration = last_punch - first_punch
            hours, remainder = divmod(duration.seconds, 3600)
            minutes = remainder // 60
            working_hours = f"{hours:02}:{minutes:02}"
        else:
            working_hours = "00:00"

        late_entry = 1 if first_punch.time() > LATE_ENTRY_LIMIT else 0
        early_exit = 1 if last_punch.time() < EARLY_EXIT_LIMIT else 0

        final_output[str(date)].append({
            "emp_code": emp_code,
            "first_punch": first_punch.strftime("%I:%M %p"),
            "last_punch": last_punch.strftime("%I:%M %p"),
            "total_punches": total_punches,
            "working_hours": working_hours,
            "late_entry": late_entry,
            "early_exit": early_exit,
            "shift_period": SHIFT_PERIOD,
        })

    # Sort by date and emp_code
    sorted_output = {
        date: sorted(records, key=lambda x: x["emp_code"])
        for date, records in sorted(final_output.items())
    }
    return sorted_output


def process_attendance(csv_file_path, json_file_path, error_log_path):
    """Main attendance processing pipeline."""
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return

    data = []
    error_lines = []

    # --- Step 1: Parse all lines ---
    with open(csv_file_path, "r", encoding="utf-8") as file:
        for i, line in enumerate(file, start=1):
            parsed = parse_log_line(line, i, error_lines)
            if parsed:
                data.append(parsed)

    # --- Step 2: Group by emp_code and date ---
    grouped = defaultdict(list)
    for entry in data:
        grouped[(entry["emp_code"], entry["datetime"].date())].append(entry)

    # --- Step 3: Summarize attendance ---
    result = summarize_attendance(grouped)

    # --- Step 4: Save results ---
    with open(json_file_path, "w", encoding="utf-8") as out:
        json.dump(result, out, indent=4)
    print(f"✅ JSON file created: {json_file_path}")

    # --- Step 5: Log errors if any ---
    if error_lines:
        with open(error_log_path, "w", encoding="utf-8") as err:
            err.write("\n".join(error_lines))
        print(f"⚠️ Some rows skipped. Check: {error_log_path}")
    else:
        print("✅ All rows processed successfully (no errors).")


if __name__ == "__main__":
    csv_path = "attendance_logs/attendance_logs_2.log"
    json_path = "attendance.json"
    error_log = "error_log.txt"
    process_attendance(csv_path, json_path, error_log)
