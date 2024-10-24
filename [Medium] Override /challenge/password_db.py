import sqlite3
import ast
import time

DB_NAME = 'hashvalues.db'

# Function to create a table
def create_table(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS HashValues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_value TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to insert an entry (limit to 10 total entries)
def insert_entry(db_name, hash_value):
    print('Insert hash list to DB!')
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Insert the new hash value
    cursor.execute('''
        INSERT INTO HashValues (hash_value)
        VALUES (?)
    ''', (hash_value,))
    
    # Check the total number of entries
    cursor.execute('SELECT COUNT(*) FROM HashValues')
    count = cursor.fetchone()[0]
    
    # If more than 10 entries, delete the oldest entry
    if count > 10:
        cursor.execute('''
            DELETE FROM HashValues
            WHERE id = (
                SELECT id FROM HashValues
                ORDER BY timestamp ASC
                LIMIT 1
            )
        ''')
    
    conn.commit()
    conn.close()

# Function to read the latest entry
def read_latest_entry(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT hash_value
        FROM HashValues
        ORDER BY id DESC
        LIMIT 1
    ''')
    latest_entry = cursor.fetchone()
    conn.close()
    return latest_entry

# Example usage
if __name__ == '__main__':
    db_name = DB_NAME
    create_table(db_name)
    
    # Insert a hash value
    insert_entry(db_name, 'abc123hash')
    insert_entry(db_name, 'def456hash')

    insert_entry(db_name, '[163, 163, 14, 93, 198, 187, 162, 32, 171, 216, 135, 177, 74, 183, 96, 63]')
    
    # Read the latest entry
    latest = read_latest_entry(db_name)[0]
    print('Latest entry:', latest)

    if latest:
            hash_value_list = ast.literal_eval(latest)  # Convert the string back to a list
            timestamp = latest[1]
            print('First entry:', hash_value_list, timestamp)
            print(hash_value_list[1])
