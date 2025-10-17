import csv
import json
import os
from datetime import datetime, time
from collections import defaultdict
import pytz


SHIFT_START = time(9, 0)
SHIFT_END = time(18, 0)
LATE_ENTRY_LIMIT = time(9, 30)
EARLY_EXIT_LIMIT = time(17, 0)

DHAKA_TZ = pytz.timezone('Asia/Dhaka')


def convert_to_bst(ts: int) -> datetime:
    """Convert Unix timestamp to Asia/Dhaka timezone."""
    return datetime.fromtimestamp(ts, tz=DHAKA_TZ)


def validate_row(parts: list, line_number: int, line: str) -> str | None:
    """this function validates each row of the CSV file to ensure it has the correct number of columns."""
    if len(parts) < 4:
        return f"Line {line_number}: Missing columns → {line.strip()}"
    elif len(parts) > 6:
        return f"Line {line_number}: Too many columns → {line.strip()}"
    return None


def parse_timestamp(parts: list, line_number: int, line: str):
    ts_index = next((i for i, p in enumerate(parts) if p.isdigit() and len(p) > 6), None)
    if ts_index is None:
        return None, None, f"Line {line_number}: Missing or invalid timestamp: {line.strip()}"
    ts_str = parts[ts_index]
    device = " ".join(parts[ts_index + 1:])
    return ts_str, device, None


def calculate_working_hours(first_punch: datetime, last_punch: datetime, total_punches: int) -> str:
    if total_punches > 1:
        duration = last_punch - first_punch
        total_seconds = max(0, duration.total_seconds())
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes = remainder // 60
        return f"{hours:02}:{minutes:02}"
    return "00:00"


def check_attendance_flags(first_punch: datetime, last_punch: datetime):
    late = "Yes" if first_punch.time() > LATE_ENTRY_LIMIT else "No"
    early = "Yes" if last_punch.time() < EARLY_EXIT_LIMIT else "No"
    return late, early


def read_and_parse_data(csv_file_path: str):
    data, errors = [], []

    if not os.path.exists(csv_file_path):
        errors.append(f"File not found: {csv_file_path}")
        return data, errors

    with open(csv_file_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.strip().split()
            error = validate_row(parts, line_no, line)
            if error:
                errors.append(error)
                continue

            emp_code, first_name, last_name = parts[:3]
            ts_str, device, ts_error = parse_timestamp(parts, line_no, line)
            if ts_error:
                errors.append(ts_error)
                continue

            try:
                ts = int(ts_str)
                dt = datetime.fromtimestamp(ts, tz=DHAKA_TZ)
            except Exception as e:
                errors.append(f"Line {line_no}: Invalid timestamp '{ts_str}' → {e}")
                continue

            data.append({
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "datetime": dt,
                "device": device,
                "timestamp": ts
            })
    return data, errors


def remove_duplicates(data: list) -> list:
    unique = {(d["emp_code"], d["datetime"], d["device"]): d for d in data}
    return list(unique.values())


def group_by_employee_and_date(data: list) -> dict:
    grouped = defaultdict(list)
    for record in data:
        key = (record["emp_code"], record["datetime"].date())
        grouped[key].append(record)
    return grouped


def process_daily_records(grouped_data: dict):
    final_output = defaultdict(list)
    excel_data = []

    for (emp_code, date_), records in grouped_data.items():
        records.sort(key=lambda r: r["datetime"])
        first, last = records[0], records[-1]
        total_punches = len(records)
        working_hours = calculate_working_hours(first["datetime"], last["datetime"], total_punches)
        late, early = check_attendance_flags(first["datetime"], last["datetime"])

        late_flag = 1 if late == "Yes" else 0
        early_flag = 1 if early == "Yes" else 0
        
        final_output[str(date_)].append({
            "emp_code": emp_code,
            "first_punch": first["datetime"].strftime("%H:%M"),
            "last_punch": last["datetime"].strftime("%H:%M"),
            "total_punches": total_punches,
            "working_hours": working_hours,
            "late_entry": late_flag,
            "early_exit": early_flag
        })

        excel_data.append({
            "Date": str(date_),
            "Emp Code": emp_code,
            "First Punch": first["datetime"].strftime("%H:%M"),
            "Last Punch": last["datetime"].strftime("%H:%M"),
            "Total Punches": total_punches,
            "Working Hours": working_hours,
            "Late Entry": late_flag,
            "Early Exit": early_flag
        })

    return final_output, excel_data


def write_json_output(json_file_path: str, data: dict):
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"JSON file created: {json_file_path}")


def write_excel_output(excel_file_path: str, excel_data: list):
    try:
        import xlwt
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Attendance Summary")
        headers = ["Date", "Emp Code", "First Punch", "Last Punch", "Total Punches",
                   "Working Hours", "Late Entry", "Early Exit"]
        style = xlwt.easyxf("font: bold on")
        for col, h in enumerate(headers):
            ws.write(0, col, h, style)
        for row_idx, rec in enumerate(excel_data, 1):
            for col_idx, h in enumerate(headers):
                ws.write(row_idx, col_idx, rec[h])
        wb.save(excel_file_path)
        print(f"Excel file created: {excel_file_path}")
    except ImportError:
        print("xlwt not found, creating CSV instead...")
        csv_path = excel_file_path.replace(".xls", ".csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(excel_data)
        print(f"CSV file created: {csv_path}")


def write_error_log(error_log_path: str, errors: list):
    if errors:
        with open(error_log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(errors))
        print(f"Some rows skipped. Check: {error_log_path}")
    else:
        print("All rows processed successfully.")


def process_attendance(csv_path, json_path, excel_path, error_log):
    data, errors = read_and_parse_data(csv_path)
    if not data:
        print("No valid data to process.")
        return

    data = remove_duplicates(data)
    grouped = group_by_employee_and_date(data)
    final_json, excel_data = process_daily_records(grouped)
    final_json = {date: sorted(records, key=lambda r: r["emp_code"]) for date, records in final_json.items()}

    write_json_output(json_path, final_json)
    write_excel_output(excel_path, excel_data)
    write_error_log(error_log, errors)


if __name__ == "__main__":
    csv_file = "attendance_logs/attendance_logs_1.log"
    json_file = "attendance_summary.json"
    excel_file = "attendance_summary.xls"
    error_log_file = "error_log.txt"
    process_attendance(csv_file, json_file, excel_file, error_log_file)
