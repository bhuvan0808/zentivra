import sqlite3

db = sqlite3.connect("zentivra.db")
c = db.cursor()

try:
    c.execute("DELETE FROM users;")
    db.commit()
    print("Users table cleared successfully")
except Exception as e:
    print(f"Failed to clear users table: {e}")
finally:
    db.close()
