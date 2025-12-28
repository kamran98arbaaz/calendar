import sqlite3
import json
from datetime import datetime

# Connect to SQLite database
sqlite_conn = sqlite3.connect('instance/calendar.db')
sqlite_cursor = sqlite_conn.cursor()

# Export users
sqlite_cursor.execute("SELECT id, username, name, password_hash, role FROM user")
users = sqlite_cursor.fetchall()

# Export halls
sqlite_cursor.execute("SELECT id, name FROM hall")
halls = sqlite_cursor.fetchall()

# Export bookings
sqlite_cursor.execute("SELECT id, bid, hall_id, date, time_slot, client_name, phone, address, status, user_id, created_at, confirmed_at FROM booking")
bookings = sqlite_cursor.fetchall()

sqlite_conn.close()

# Convert to JSON-serializable format
data = {
    'users': [
        {
            'id': u[0],
            'username': u[1],
            'name': u[2],
            'password_hash': u[3],
            'role': u[4]
        } for u in users
    ],
    'halls': [
        {
            'id': h[0],
            'name': h[1]
        } for h in halls
    ],
    'bookings': [
        {
            'id': b[0],
            'bid': b[1],
            'hall_id': b[2],
            'date': b[3],
            'time_slot': b[4],
            'client_name': b[5],
            'phone': b[6],
            'address': b[7],
            'status': b[8],
            'user_id': b[9],
            'created_at': b[10],
            'confirmed_at': b[11]
        } for b in bookings
    ]
}

# Save to JSON file
with open('data_export.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)

print("Data exported to data_export.json")