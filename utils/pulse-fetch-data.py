#!/usr/bin/env python3
import sys
import requests
import time
import os
import csv
from datetime import datetime, timezone

LOG_FILE = "energy_log.csv"

RATE_PER_KWH = 0.30  # cost per kWh in dollars
PEAK_HOURS = range(16, 21)  # 4pm–9pm local time


def fetch_energy_value(device_name):
    """Fetch energy value (kWh) from the specified device."""
    url = f"http://{device_name}/sensor/total_energy"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data.get("value", 0.0))
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def write_csv_row(row):
    """Append a row to the CSV file, creating header if missing."""
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            # writer.writerow(["datetime_utc", "datetime_local", "total_watt_hours", "watt_hours", "cost_dollars", "is_peak"])
            writer.writerow(["datetime_utc", "datetime_local", "watt_hours", "cost_dollars", "is_peak"])
        writer.writerow(row)


def sleep_until_next_minute():
    """Sleep until the top of the next minute (e.g. xx:01:00)."""
    now = time.time()
    # seconds until next minute boundary
    next_minute = 60 - (now % 60)
    time.sleep(next_minute)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 energy_logger.py <device-name>")
        sys.exit(1)

    device_name = sys.argv[1]
    print(f"# Starting energy logger for device: {device_name}")
    print(f"# Starting energy logger — waiting to synchronize to the top of each minute.")
    sleep_until_next_minute()

    print("# Logging initial total energy reading.")
    value_kwh = fetch_energy_value(device_name)
    total_watt_hours_last = value_kwh * 1000
    sleep_until_next_minute()

    while True:
        value_kwh = fetch_energy_value(device_name)
        if value_kwh is not None:
            now_utc = datetime.now(timezone.utc)
            now_local = datetime.now()

            total_watt_hours = value_kwh * 1000

            # Calculate watt_hours for period
            watt_hours = total_watt_hours - total_watt_hours_last
            total_watt_hours_last = total_watt_hours

            cost_dollars = watt_hours * RATE_PER_KWH / 1000
            is_peak = "TRUE" if now_local.hour in PEAK_HOURS else "FALSE"

            row = [
                now_utc.strftime("%d/%m/%Y %H:%M"),
                now_local.strftime("%d/%m/%Y %H:%M"),
                # f"{total_watt_hours:.0f}",
                f"{watt_hours:.0f}",
                f"{cost_dollars:.6f}",
                is_peak,
            ]

            print(",".join(row))
            write_csv_row(row)

        # wait until the next minute boundary
        sleep_until_next_minute()


if __name__ == "__main__":
    main()
