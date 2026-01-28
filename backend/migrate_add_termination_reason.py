"""
Migration script to add termination_reason column to interviews table
Run this once to update your existing database
"""
import sqlite3
import os

# Database file path
db_path = "interview.db"

if not os.path.exists(db_path):
    print(f"Database file {db_path} not found!")
    exit(1)

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(interviews)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "termination_reason" in columns:
        print("Column 'termination_reason' already exists. No migration needed.")
    else:
        # Add the column
        cursor.execute("ALTER TABLE interviews ADD COLUMN termination_reason VARCHAR")
        conn.commit()
        print("Successfully added 'termination_reason' column to interviews table!")
    
    conn.close()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {str(e)}")
    exit(1)

