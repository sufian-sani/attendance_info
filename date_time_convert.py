import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# File paths
log_file = Path("attendance_logs/attendance_logs_2.log")
json_file = Path("converted.json")

# Timezones
UTC = timezone.utc
BST = timezone(timedelta(hours=6))

def convert_timestamp(ts: int):
    """Convert Unix timestamp to short UTC and BST strings."""
    utc_time = datetime.fromtimestamp(ts, tz=UTC).strftime("%y-%m-%d %H:%M")
    bst_time = datetime.fromtimestamp(ts, tz=BST).strftime("%y-%m-%d %H:%M")
    return utc_time, bst_time

def process_log_file(input_path: Path, output_path: Path):
    records = []
    with input_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.strip().split()
            if len(parts) < 4:
                print(f"Skipping malformed line {line_no}: {line.strip()}")
                continue

            emp_id = parts[0]
            # Name may have multiple parts, so join everything except emp_id, timestamp, device
            name = " ".join(parts[1:-1])
            ts = int(parts[-3])
            device = parts[-1]

            utc_time, bst_time = convert_timestamp(ts)

            records.append({
                "emp_id": emp_id,
                "name": name,
                "timestamp": ts,
                "utc": utc_time,
                "bst": bst_time,
                "device": device
            })

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)

    print(f"Processed {len(records)} records and saved to {output_path}")

if __name__ == "__main__":
    process_log_file(log_file, json_file)
