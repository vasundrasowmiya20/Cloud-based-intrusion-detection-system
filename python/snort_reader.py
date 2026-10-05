import time
import re
import os
import sqlite3
from datetime import datetime

# CSV file setup
if not os.path.exists("alerts.csv"):
    with open("alerts.csv", "w") as log:
        log.write("timestamp,message,src,dst\n")

# SQLite setup
conn = sqlite3.connect("/var/lib/grafana/alerts.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    message TEXT,
    src TEXT,
    dst TEXT
)
''')
conn.commit()

file_path = "/var/log/snort/alert"

def follow(file):
    file.seek(0, 2)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.5)
            continue
yield line

with open(file_path, "r") as f:
    for line in follow(f):
        match = re.search(
            r'(\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+).*?\[\*\*\] \[.*?\] (.*?) \[\*\*\]',
            line
        )

        if match:
            raw_time, message = match.groups()
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+).*->.*(\d+\.\d+\.\d+\.\d+)', line)

            if ip_match:
                src, dst = ip_match.groups()
            else:
                src, dst = "N/A", "N/A"

            try:
                parsed_time = datetime.strptime(raw_time, "%m/%d-%H:%M:%S.%f")
                parsed_time = parsed_time.replace(year=datetime.now().year)
                timestamp = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp = None

            print(f"{message} | {src} → {dst} | {timestamp}")

            # Write to CSV
            with open("alerts.csv", "a") as log:
                log.write(f"{timestamp},{message},{src},{dst}\n")

            # Insert into SQLite
            try:
cursor.execute(
                   "INSERT INTO alerts (timestamp, message, src, dst) VALUES (?, ?, ?, ?)",
                   (timestamp, message, src, dst)
                )
                conn.commit()
                print("Inserted into DB")
            except Exception as e:
                print(" DB ERROR:", e)
