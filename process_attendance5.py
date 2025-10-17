from datetime import datetime, timezone, timedelta

# Example: Convert timestamp -> datetime
ts = 1758786340

# UTC conversion
utc_time = datetime.fromtimestamp(ts, tz=timezone.utc)
print("UTC:", utc_time.strftime("%Y-%m-%d %H:%M:%S"))

# Bangladesh Standard Time (UTC+6)
bst = timezone(timedelta(hours=6))
bst_time = datetime.fromtimestamp(ts, tz=bst)
print("BST:", bst_time.strftime("%Y-%m-%d %H:%M:%S"))