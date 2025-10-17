# Attendance Processing Script

This Python script processes employee attendance logs, calculates daily working hours, flags late entries and early exits, and outputs data in **JSON** and **Excel/CSV** formats.

---

## Features

* Reads attendance log files (`.log` or `.csv`) with format:

  ```
  emp_code first_name last_name timestamp device
  ```
* Converts Unix timestamps to **Asia/Dhaka timezone** using `pytz`.
* Calculates:

  * First punch time
  * Last punch time
  * Total punches
  * Working hours (HH:MM)
  * Late entry flag (`1` = Yes, `0` = No)
  * Early exit flag (`1` = Yes, `0` = No)
* Outputs:

  * JSON summary grouped by date
  * Excel (`.xls`) or CSV summary
* Handles errors and logs invalid/malformed lines.
* Includes a search script `use_search.py` to find attendance records by **employee code** and/or **date**.

---

## Requirements

* Python 3.8+
* Python libraries:

  ```bash
  pip install pytz xlwt
  ```

  > `xlwt` is optional. If not installed, a CSV will be generated instead of Excel.

---

## Usage

1. Place your attendance log file in the `attendance_logs/` directory (or any path).
2. Update the paths in the script:

```python
csv_file = "attendance_logs/attendance_logs_2.log"
json_file = "attendance_summary.json"
excel_file = "attendance_summary.xls"
error_log_file = "error_log.txt"
```

3. Run the main script:

```bash
python attendance_processor.py
```

4. Outputs:

* `attendance_summary.json` → JSON summary of daily attendance.
* `attendance_summary.xls` → Excel summary (or CSV if `xlwt` not installed).
* `error_log.txt` → Contains any skipped or malformed rows.

---

## Search Attendance

A separate search script is included to query attendance records:

```bash
python use_search.py
```

* You can input **employee code** and/or **date** (YYYY-MM-DD) to search.
* If left blank, all records will be returned.

Example `use_search.py` logic:

```python
import os
import json
from datetime import datetime

# Load attendance summary from JSON
attendance = load_attendance()
found_records = search_attendance(attendance, emp_code='10023', date=datetime(2025,9,24).date())
```

* Displays records with first punch, last punch, total punches, working hours, late/early flags, and shift period.

---

## JSON Output Example

```json
{
  "2025-09-24": [
    {
      "emp_code": "10023",
      "first_punch": "09:05",
      "last_punch": "18:10",
      "total_punches": 4,
      "working_hours": "09:05",
      "late_entry": 1,
      "early_exit": 0
    },
    {
      "emp_code": "10024",
      "first_punch": "09:00",
      "last_punch": "17:55",
      "total_punches": 3,
      "working_hours": "08:55",
      "late_entry": 1,
      "early_exit": 0
    }
  ]
}
```

---

## Excel/CSV Output Example

| Date       | Emp Code | First Punch | Last Punch | Total Punches | Working Hours | Late Entry | Early Exit |
| ---------- | -------- | ----------- | ---------- | ------------- | ------------- | ---------- | ---------- |
| 2025-09-24 | 10023    | 09:05       | 18:10      | 4             | 09:05         | 1          | 0          |
| 2025-09-24 | 10024    | 09:00       | 17:55      | 3             | 08:55         | 1          | 0          |

---

## How It Works

1. **Read Logs** → The script reads each line and validates column count.
2. **Parse Timestamp** → Converts Unix timestamp to Asia/Dhaka time.
3. **Group by Employee & Date** → Collects all punches for each employee per day.
4. **Process Records** → Sorts punches, calculates working hours, and sets flags.
5. **Write Output** → Generates JSON and Excel/CSV summaries.
6. **Search** → `use_search.py` can query the JSON output for specific employees or dates.
7. **Error Handling** → Logs invalid or incomplete lines for review.

---

## Customization

* **Shift timings** can be adjusted at the top of the script:

```python
SHIFT_START = time(9, 0)
SHIFT_END = time(18, 0)
LATE_ENTRY_LIMIT = time(9, 30)
EARLY_EXIT_LIMIT = time(17, 0)
```

* **Timezone** can be changed:

```python
DHAKA_TZ = pytz.timezone('Asia/Dhaka')
```

---

## License

This project is open-source and free to use.
