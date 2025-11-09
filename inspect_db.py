import sqlite3

conn = sqlite3.connect("names.db")
cursor = conn.cursor()

print("Tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table)

conn.close()
