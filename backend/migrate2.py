import sqlite3

db = sqlite3.connect("zentivra.db")
c = db.cursor()

try:
    c.execute("UPDATE users SET email = username || '@example.com' WHERE email = '';")
    c.execute("CREATE UNIQUE INDEX ux_users_email ON users(email);")
    db.commit()
    print("Migration successful")
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    db.close()
