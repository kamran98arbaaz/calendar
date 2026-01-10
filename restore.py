import os
import json
from sqlalchemy import create_engine, text

# Load DATABASE_URL from .env
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+pg8000://')

def restore_database(schema_file, data_file):
    engine = create_engine(DATABASE_URL)

    # Restore schema
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    with engine.connect() as conn:
        # Split and execute DDL statements
        statements = schema_sql.split(';')
        for stmt in statements:
            if stmt.strip():
                conn.execute(text(stmt))
        conn.commit()

    # Restore data
    with open(data_file, 'r') as f:
        data = json.load(f)

    with engine.connect() as conn:
        for table_name, rows in data.items():
            if rows:
                # Clear table
                conn.execute(text(f'DELETE FROM "{table_name}"'))
                # Insert data
                for row in rows:
                    columns = ', '.join(f'"{k}"' for k in row.keys())
                    placeholders = ', '.join([f':{k}' for k in row.keys()])
                    insert_sql = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
                    conn.execute(text(insert_sql), row)
        conn.commit()

    print("Restore completed")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python restore.py <schema_file> <data_file>")
        sys.exit(1)
    restore_database(sys.argv[1], sys.argv[2])