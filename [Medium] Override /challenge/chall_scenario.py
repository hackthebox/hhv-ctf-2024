import random
import hashlib
from config import *
from password_db import *

def ascii_to_list(data):
    if not data:
        return []

    return [ord(char) for char in data]

def all_ascii(data):
    # Check if all integers are within the ASCII range
    all_ascii = all(0 <= num <= 127 for num in data)
    return all_ascii

def create_data_with_hash(secret_value, insert_address):
    # Initialize an empty list to store the data
    data = []
    # Define the total size of the data
    total_size = 16 * 1024
    data_size = 2 * 1024
    # Continue adding random data until the size is reached
    while len(data) < data_size:
        # Generate a random length for the next chunk of data (1 to 100 bytes)
        length = random.randint(1, 10)
        # Generate random data for this chunk
        chunk = [random.randint(1, 254) for _ in range(length)]
        # Append the chunk and a null terminator to the list
        data.extend(chunk + [0])
        
        # Ensure we do not exceed 2MB
        if len(data) > total_size:
            data = data[:total_size]
            break

    # Hash the secret value using SHA-256
    hash_object = hashlib.md5()
    hash_object.update(secret_value.encode())  # Convert secret to bytes and hash it
    hashed_value = hash_object.digest()  # Get the hash as bytes

    hashed_value = list(hashed_value)

    # INSERT FIRST TO DB
    create_table(DB_NAME)
    insert_entry(DB_NAME, str(hashed_value))

    # Convert hash to a list of integers
    hashed_value_list =  [0] + hashed_value + [0]

    print(hashed_value_list)
    # Insert the hash at the specified address within the data
    # Ensure the insertion does not exceed the data bounds
    if insert_address + len(hashed_value_list) > len(data):
        raise ValueError("Insert address exceeds data bounds")
    data[insert_address:insert_address + len(hashed_value_list)] = hashed_value_list
    
    return data


#data = create_data_with_hash('erijiuhriuhrurehrehreu', 1024)
#print(data)