import os
import json
from datetime import datetime
from app import create_app, db
from app.models import User, Hall, Booking

def import_data():
    # Load data from JSON
    with open('data_export.json', 'r') as f:
        data = json.load(f)

    # Create app with PostgreSQL
    app = create_app()

    with app.app_context():
        # Clear existing data (optional, for clean import)
        db.session.query(Booking).delete()
        db.session.query(Hall).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Import users
        for user_data in data['users']:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                name=user_data['name'],
                password_hash=user_data['password_hash'],
                role=user_data['role']
            )
            db.session.add(user)

        # Import halls
        for hall_data in data['halls']:
            hall = Hall(
                id=hall_data['id'],
                name=hall_data['name']
            )
            db.session.add(hall)

        db.session.commit()  # Commit halls and users first

        # Import bookings
        for booking_data in data['bookings']:
            booking = Booking(
                id=booking_data['id'],
                bid=booking_data['bid'],
                hall_id=booking_data['hall_id'],
                date=datetime.fromisoformat(booking_data['date']).date(),
                time_slot=booking_data['time_slot'],
                client_name=booking_data['client_name'],
                phone=booking_data['phone'],
                address=booking_data['address'],
                status=booking_data['status'],
                user_id=booking_data['user_id'],
                created_at=datetime.fromisoformat(booking_data['created_at']) if booking_data['created_at'] else None,
                confirmed_at=datetime.fromisoformat(booking_data['confirmed_at']) if booking_data['confirmed_at'] and booking_data['confirmed_at'] != 'null' else None
            )
            db.session.add(booking)

        db.session.commit()
        print("Data imported successfully!")

if __name__ == '__main__':
    import_data()