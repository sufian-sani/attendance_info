from datetime import datetime
import pytz
timestamp = 1757527532
timezone = pytz.timezone('Asia/Dhaka')
dt_object = datetime.fromtimestamp(timestamp, tz=timezone)
print("Datetime with Timezone:", dt_object)