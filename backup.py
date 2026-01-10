import os
import json
import datetime
from sqlalchemy import create_engine, text, MetaData
from app.models import db, User, Hall, Booking  # Import models

# Load DATABASE_URL from .env
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+pg8000://')

def backup_database():
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export data to JSON
    data = {}
    with engine.connect() as conn:
        for table_name in ['user', 'hall', 'booking']:
            result = conn.execute(text(f'SELECT json_agg(row_to_json("{table_name}")) FROM "{table_name}"'))
            table_data = result.fetchone()[0]
            data[table_name] = table_data or []

    # Save data to JSON
    with open(f'backup_data_{timestamp}.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Export schema to SQL (DDL)
    schema_sql = ""
    for table in metadata.sorted_tables:
        schema_sql += str(table) + ";\n\n"

    with open(f'backup_schema_{timestamp}.sql', 'w') as f:
        f.write(schema_sql)

    print(f"Backup completed: backup_data_{timestamp}.json and backup_schema_{timestamp}.sql")

if __name__ == "__main__":
    backup_database()