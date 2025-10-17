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


def validate_row(parts, line_number, line):
    """Validate row structure and return error message if invalid."""
    if len(parts) < 5:
        return f"Line {line_number}: Missing columns → {line.strip()}"
    elif len(parts) > 6:
        return f"Line {line_number}: Too many columns → {line.strip()}"
    return None


def parse_timestamp(parts, line_number, line):
    """Extract and validate timestamp from row parts."""
    timestamp_index = next((i for i, p in enumerate(parts) if p.isdigit() and len(p) > 6), None)
    if timestamp_index is None:
        return None, None, f"Line {line_number}: Missing or invalid timestamp → {line.strip()}"
    
    timestamp_str = parts[timestamp_index]
    device = " ".join(parts[timestamp_index + 1:])
    return timestamp_str, device, None


def calculate_working_hours(first_punch, last_punch, total_punches):
    """Calculate working hours between first and last punch."""
    if total_punches > 1:
        duration = last_punch - first_punch
        total_seconds = max(0, duration.total_seconds())  # Ensure non-negative
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes = remainder // 60
        return f"{hours:02}:{minutes:02}"
    return "00:00"


def check_attendance_flags(first_punch, last_punch):
    """Check late entry and early exit conditions."""
    late_entry = "Yes" if first_punch.time() > LATE_ENTRY_LIMIT else "No"
    early_exit = "Yes" if last_punch.time() < EARLY_EXIT_LIMIT else "No"
    return late_entry, early_exit


def process_daily_records(grouped_data):
    """Process grouped records into daily attendance summaries."""
    final_output = defaultdict(list)
    excel_data = []
    
    for (emp_code, date_), records in grouped_data.items():
        # Sort punches by time
        records.sort(key=lambda r: r["datetime"])
        first_punch = records[0]["datetime"]
        last_punch = records[-1]["datetime"]
        total_punches = len(records)

        working_hours = calculate_working_hours(first_punch, last_punch, total_punches)
        late_entry, early_exit = check_attendance_flags(first_punch, last_punch)

        # JSON output record
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

        # Excel data record
        excel_data.append({
            "Date": str(date_),
            "Emp Code": emp_code,
            "First Punch": first_punch.strftime("%H:%M"),
            "Last Punch": last_punch.strftime("%H:%M"),
            "Total Punches": total_punches,
            "Working Hours": working_hours,
            "Late Entry": late_entry,
            "Early Exit": early_exit
        })
    
    return final_output, excel_data


def read_and_parse_data(csv_file_path):
    """Read CSV file and parse data with error handling."""
    data = []
    error_lines = []
    
    if not os.path.exists(csv_file_path):
        error_lines.append(f"❌ File not found: {csv_file_path}")
        return data, error_lines

    with open(csv_file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            parts = line.strip().split()

            # Validate row structure
            validation_error = validate_row(parts, line_number, line)
            if validation_error:
                error_lines.append(validation_error)
                continue

            emp_code, first_name, last_name = parts[0], parts[1], parts[2]

            # Parse timestamp
            timestamp_str, device, timestamp_error = parse_timestamp(parts, line_number, line)
            if timestamp_error:
                error_lines.append(timestamp_error)
                continue

            # Convert timestamp
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
    
    return data, error_lines


def remove_duplicates(data):
    """Remove duplicate records based on emp_code, datetime, and device."""
    unique_data = {(d["emp_code"], d["datetime"], d["device"]): d for d in data}
    return list(unique_data.values())


def group_by_employee_and_date(data):
    """Group records by employee code and date."""
    grouped = defaultdict(list)
    for record in data:
        key = (record["emp_code"], record["datetime"].date())
        grouped[key].append(record)
    return grouped


def sort_output_data(final_output):
    """Sort output by date and employee code."""
    return {
        date: sorted(records, key=lambda x: x["emp_code"])
        for date, records in sorted(final_output.items())
    }


def write_json_output(json_file_path, sorted_output):
    """Write JSON output file."""
    with open(json_file_path, "w", encoding="utf-8") as out_file:
        json.dump(sorted_output, out_file, indent=4)
    print(f"✅ JSON file created: {json_file_path}")


def write_excel_output(excel_file_path, excel_data):
    """Write Excel output file using built-in libraries."""
    if not excel_data:
        print("❌ No data available for Excel export")
        return
    
    # Use xlwt which is usually available or can be easily installed
    try:
        import xlwt
        
        # Create workbook
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Attendance Summary')
        
        # Define headers
        headers = ["Date", "Emp Code", "First Punch", "Last Punch", 
                  "Total Punches", "Working Hours", "Late Entry", "Early Exit"]
        
        # Write headers with bold style
        header_style = xlwt.easyxf('font: bold on')
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_style)
        
        # Sort data
        sorted_data = sorted(excel_data, key=lambda x: (x["Date"], x["Emp Code"]))
        
        # Write data rows
        for row_idx, record in enumerate(sorted_data, 1):
            sheet.write(row_idx, 0, record["Date"])
            sheet.write(row_idx, 1, record["Emp Code"])
            sheet.write(row_idx, 2, record["First Punch"])
            sheet.write(row_idx, 3, record["Last Punch"])
            sheet.write(row_idx, 4, record["Total Punches"])
            sheet.write(row_idx, 5, record["Working Hours"])
            sheet.write(row_idx, 6, record["Late Entry"])
            sheet.write(row_idx, 7, record["Early Exit"])
        
        # Save the file
        workbook.save(excel_file_path)
        print(f"✅ Excel file created: {excel_file_path}")
        
    except ImportError:
        print("❌ xlwt not available. Creating CSV file instead...")
        # Fallback to CSV
        csv_path = excel_file_path.replace('.xlsx', '.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["Date", "Emp Code", "First Punch", "Last Punch", 
                         "Total Punches", "Working Hours", "Late Entry", "Early Exit"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            sorted_data = sorted(excel_data, key=lambda x: (x["Date"], x["Emp Code"]))
            writer.writerows(sorted_data)
        print(f"✅ CSV file created: {csv_path}")


def write_error_log(error_log_path, error_lines):
    """Write error log if any errors occurred."""
    if error_lines:
        with open(error_log_path, "w", encoding="utf-8") as err_file:
            err_file.write("\n".join(error_lines))
        print(f"⚠️ Some rows skipped. Check: {error_log_path}")
    else:
        print("✅ All rows processed successfully (no errors).")


def generate_statistics(data, final_output, error_lines):
    """Generate and display processing statistics."""
    total_employees = len(set(record["emp_code"] for record in data))
    total_days = len(final_output)
    total_records = sum(len(records) for records in final_output.values())
    
    # Calculate late entries and early exits
    late_entries = 0
    early_exits = 0
    for records in final_output.values():
        for record in records:
            if record["late_entry"] == "Yes":
                late_entries += 1
            if record["early_exit"] == "Yes":
                early_exits += 1
    
    print(f"\n📊 Processing Statistics:")
    print(f"   • Total employees: {total_employees}")
    print(f"   • Total days: {total_days}")
    print(f"   • Attendance records: {total_records}")
    print(f"   • Late entries: {late_entries}")
    print(f"   • Early exits: {early_exits}")
    print(f"   • Errors encountered: {len(error_lines)}")


def process_attendance(csv_file_path, json_file_path, excel_file_path, error_log_path):
    # --- Step 1: Read CSV and parse data ---
    data, error_lines = read_and_parse_data(csv_file_path)
    
    if not data and not error_lines:
        print(f"❌ No data found in file: {csv_file_path}")
        return
    elif not data:
        print(f"❌ No valid data found after parsing")
        return

    # --- Step 2: Remove duplicate entries ---
    initial_count = len(data)
    data = remove_duplicates(data)
    duplicates_removed = initial_count - len(data)
    if duplicates_removed > 0:
        print(f"✅ Removed {duplicates_removed} duplicate records")

    # --- Step 3: Group by employee and date ---
    grouped_data = group_by_employee_and_date(data)

    # --- Step 4: Process daily summaries ---
    final_output, excel_data = process_daily_records(grouped_data)

    # --- Step 5: Sort output by date and employee code ---
    sorted_output = sort_output_data(final_output)

    # --- Step 6: Write output files ---
    write_json_output(json_file_path, sorted_output)
    write_excel_output(excel_file_path, excel_data)
    write_error_log(error_log_path, error_lines)

    # --- Step 7: Display statistics ---
    generate_statistics(data, final_output, error_lines)


if __name__ == "__main__":
    csv_path = "attendance_logs/attendance_logs_1.log"
    json_path = "attendance_summary.json"
    excel_path = "attendance_summary.xls"  # Using .xls format which xlwt supports
    error_log = "error_log.txt"
    process_attendance(csv_path, json_path, excel_path, error_log)