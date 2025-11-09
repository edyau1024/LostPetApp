import sqlite3

conn = sqlite3.connect("names.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE name_entry ADD COLUMN formatted_address TEXT;")
    print("Added formatted_address")
except sqlite3.OperationalError as e:
    print("formatted_address already exists or error:", e)

try:
    cursor.execute("ALTER TABLE name_entry ADD COLUMN timestamp TEXT;")
    print("Added timestamp")
except sqlite3.OperationalError as e:
    print("timestamp already exists or error:", e)

conn.commit()
conn.close()
