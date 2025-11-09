import sqlite3

conn = sqlite3.connect("names.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(name_entry);")
columns = cursor.fetchall()

for col in columns:
    print(col)

conn.close()
