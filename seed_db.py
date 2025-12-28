#!/usr/bin/env python3
"""
Database seeding script for production deployment.
Run this after deploying to populate initial data.
"""

from app import create_app, db
from app.models import Hall

def seed_database():
    """Seed the database with initial data."""
    app = create_app()

    with app.app_context():
        print("Seeding database...")

        # Check if halls already exist
        if Hall.query.first():
            print("Database already seeded. Skipping...")
            return

        # Add initial halls
        halls = [
            Hall(name='AR Garden'),
            Hall(name='Diamond Palace')
        ]

        for hall in halls:
            db.session.add(hall)

        db.session.commit()
        print(f"Added {len(halls)} halls to database")

if __name__ == '__main__':
    seed_database()