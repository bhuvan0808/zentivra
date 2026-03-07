import sqlite3

db = sqlite3.connect("zentivra.db")
c = db.cursor()

try:
    c.execute("ALTER TABLE runs ADD COLUMN email_recipients JSON;")
    db.commit()
    print("Migration successful")
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    db.close()
