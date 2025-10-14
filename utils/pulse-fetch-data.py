#!/usr/bin/env python3
import sys
import requests
import time
import os
import csv
from datetime import datetime, timezone

LOG_FILE    = "energy_log.csv"
LOG_VERSION = "powershare 1.0.0"

def fetch_energy_values(device_name):
    """Fetch energy value (Wh) from the specified device."""
    url = f"http://{device_name}/sensor/total_energy"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {"total_watt_hours_in": int(data.get("value", 0) * 1000),
                "total_watt_hours_out": 0 }

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def write_csv_row(row):
    """Append a row to the CSV file, creating header if missing."""
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([f"# Version: {LOG_VERSION}"])
            writer.writerow(["datetime_utc", "datetime_local", "total_watt_hours_in", "total_watt_hours_out"])
        writer.writerow(row)

def sleep_until_next_minute():
    """Sleep until the top of the next minute (e.g. xx:01:00)."""
    now = time.time()
    # seconds until next minute boundary
    next_minute = 60 - (now % 60)
    time.sleep(next_minute)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <device-name>")
        sys.exit(1)

    device_name = sys.argv[1]
    print(f"# Version: {LOG_VERSION}")
    print(f"# Starting energy logger — synchronizing to the top of each minute.")

    while True:
        values_wh = fetch_energy_values(device_name)
        if values_wh is not None:
            now_utc = datetime.now(timezone.utc)
            now_local = datetime.now()

            total_watt_hours_in = values_wh["total_watt_hours_in"]
            total_watt_hours_out = values_wh["total_watt_hours_out"]

            row = [
                now_utc.strftime("%d/%m/%Y %H:%M:%S"),
                now_local.strftime("%d/%m/%Y %H:%M:%S"),
                f"{total_watt_hours_in}",
                f"{total_watt_hours_out}"
            ]

            print(",".join(row))
            write_csv_row(row)

        # wait until the next minute boundary
        sleep_until_next_minute()


if __name__ == "__main__":
    main()
