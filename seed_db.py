#!/usr/bin/env python3
"""
Database seeding script for production deployment.
Run this after deploying to populate initial data from SQLite export.
"""

import json
from datetime import datetime
from app import create_app, db
from app.models import User, Hall, Booking

def seed_database():
    """Seed the database with initial data from export."""
    app = create_app()

    with app.app_context():
        print("Seeding database with exported data...")

        # Check if data already exists
        if Hall.query.first():
            print("Database already seeded. Skipping...")
            return

        try:
            # Load exported data
            with open('data_export.json', 'r') as f:
                data = json.load(f)

            print(f"Found {len(data['users'])} users, {len(data['halls'])} halls, {len(data['bookings'])} bookings")

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
                print(f"Added user: {user.username}")

            # Import halls
            for hall_data in data['halls']:
                hall = Hall(
                    id=hall_data['id'],
                    name=hall_data['name']
                )
                db.session.add(hall)
                print(f"Added hall: {hall.name}")

            # Commit users and halls first
            db.session.commit()

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

            # Final commit
            db.session.commit()

            print("✅ Database seeding completed successfully!")
            print(f"Imported: {len(data['users'])} users, {len(data['halls'])} halls, {len(data['bookings'])} bookings")

        except FileNotFoundError:
            print("❌ data_export.json not found. Using basic seeding...")

            # Fallback: Add basic halls only
            halls = [
                Hall(name='AR Garden'),
                Hall(name='Diamond Palace')
            ]

            for hall in halls:
                db.session.add(hall)

            db.session.commit()
            print(f"Added {len(halls)} basic halls")

        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    seed_database()