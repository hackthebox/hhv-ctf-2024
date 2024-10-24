import socket
import threading
import asyncio
import json
import time
import sqlite3



'''
Read/Set Address pins A0, A1 A2
Set your modules slave Address
Interact with MCU

If  correct address but IC undchanged still
 send data but the receive will return error

'''

HOST = '0.0.0.0'
PORT = 1338

CORRECT_PIN = '5052#'

CORRECT_ID = 0x23

# Constants representing the return values for no key pressed and failure to read
I2C_KEYPAD_NOKEY = None
I2C_KEYPAD_FAIL = -1
I2C_ID_CONFLICT = -2


CURRENT_PIN_ENTRY = ''


def create_database():
    conn = sqlite3.connect('communication.db')
    cursor = conn.cursor()
    
    # Drop the table if it exists
    cursor.execute('DROP TABLE IF EXISTS pin_entries')
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pin_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database and table created (existing table dropped).")


def write_pin_to_database(pin):
    conn = sqlite3.connect('communication.db')
    cursor = conn.cursor()
    
    # Check the number of rows in the table
    cursor.execute('SELECT COUNT(*) FROM pin_entries')
    row_count = cursor.fetchone()[0]
    
    if row_count >= 10:
        # Delete the oldest entry (the one with the smallest id)
        cursor.execute('DELETE FROM pin_entries WHERE id = (SELECT MIN(id) FROM pin_entries)')
    
    # Insert the new entry
    cursor.execute('''
        INSERT INTO pin_entries (pin)
        VALUES (?)
    ''', (pin,))
    
    conn.commit()
    conn.close()
    print(f"Written PIN: {pin} to database.")





def read_latest_row():
    conn = sqlite3.connect('communication.db')
    cursor = conn.cursor()
    
    # Fetch the latest row based on the highest id
    cursor.execute('SELECT * FROM communication ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    
    conn.close()
    return row


def comm_module_id():
    latest_row = read_latest_row()

    if latest_row:
       
        comm_module_address = latest_row[2]
    
        return comm_module_address

    return None

def conflicting_IDs():
    latest_row = read_latest_row()

    if latest_row:
        ic_address = latest_row[1]
        comm_module_address = latest_row[2]
    
        print(f"ID: {latest_row[0]}, IC_Address: {ic_address}, comm_module_address: {comm_module_address}")
        
        if ic_address == comm_module_address:
            return True
        else:
            return False

    else:

        return None
        print("No data found.")



def _is_connection_alive(connection):
    try:
        # This sends zero bytes over the connection, effectively a no-op but checks the connection's status
        connection.sendall(b'')
    except socket.error as e:
        print(f"Socket error: {e}")
        return False

    return True


class I2CKeyPad:
    def __init__(self, connection):
        self.connection = connection
        self._lastKey = None
        self.normal_keymap = "123A456B789C*0#D"  # 16 characters for the 4x4 keypad


    def _read(self, address):
        
        # Send the address as a string command
        self.connection.send(f'{address:02X}'.encode('utf-8') + b'\n')  # Send address ending with newline as a separator

        #self.connection.send(bytes(address) + b'\n') 

        # Read the response from the client
        data = b''
        while True:
            print('waiting')

            part = self.connection.recv(1024)
            print(part)

            if b'\n' in part:
                data += part[:part.index(b'\n')]
                break
            
            if part == b'':
                print('[!] Connection broken')
                break

            data += part

        if len(data) > 2:
            print('Too much data')
            return None  # Error handling
        elif len(data) <= 1:
            print('Too little data')
            return None  # Error handling

        # Convert received data back to integer
        try:
            return int(data, 16)
        except ValueError:
            print('Invalid data')
            return None

    def _getKey4x4(self):

        key = 0

        rows = self._read(0xF0)

        if rows == 0xF0:
            return I2C_KEYPAD_NOKEY
        elif rows == 0xE0:
            key = 0
        elif rows == 0xD0:
            key = 1
        elif rows == 0xB0:
            key = 2
        elif rows == 0x70:
            key = 3
        else:
            return I2C_KEYPAD_FAIL

        if conflicting_IDs():
            print('conflicting_IDs')
            return I2C_ID_CONFLICT

        cols = self._read(0x0F)

        if cols == 0x0F:
            return I2C_KEYPAD_NOKEY
        elif cols == 0x0E:
            key += 0
        elif cols == 0x0D:
            key += 4
        elif cols == 0x0B:
            key += 8
        elif cols == 0x07:
            key += 12
        else:
            return I2C_KEYPAD_FAIL

        
        key = self.normal_keymap[key]
        print(f'[!] Key pressed: {key}')

        self._lastKey = key

        return key



def process_pin(pin_code):
    global CURRENT_PIN_ENTRY

    pin_code = pin_code.strip('#')
    print(f'Pin code entered: {pin_code}')
    if pin_code == CORRECT_PIN:
        print('[*] YOU GET THE FLAG!!!!')

    CURRENT_PIN_ENTRY = ''
    return 


def client_handler(connection):
    global CURRENT_PIN_ENTRY

    print('Client connected')

    # Create an instance of I2CKeyPad with the current connection
    keypad = I2CKeyPad(connection)

    while True:
        
        # Check if the connection is alive before sending
        if not _is_connection_alive(connection):
            print("Connection not alive")
            return None  # Could also handle reconnection or throw an exception



        current_module_id = comm_module_id()
        if current_module_id == CORRECT_ID:
            key = keypad._getKey4x4()


            if key is None:
                print("[-] No key is pressed")
                continue  # Handle error or break if needed

            elif key == I2C_KEYPAD_FAIL:
                print("[!] Failed to get a valid key")
                continue  # Handle error or break if needed
            elif key == I2C_ID_CONFLICT:
                print("[!] Failed to read due to ID conflict!")
                continue  # Handle error or break if needed
            else:

                print("[*] Key is pressed!")
                CURRENT_PIN_ENTRY += key
                write_pin_to_database(CURRENT_PIN_ENTRY)

                print(f'CURRENT_PIN_ENTRY: {CURRENT_PIN_ENTRY}')

                if key == "#":

                    result = process_pin(CURRENT_PIN_ENTRY)

                print(f'Key pressed: {key}')
        


        '''

            try:
                packet = json.loads(data.decode('utf-8'))
                device_address = packet["address"]
                operation = packet["operation"]  # "read" or "write"
                data_bytes = [int(x, 16) for x in packet.get("data_out", [])]
                bytes_to_read = packet.get("readlen", 0)

                print(f"Received operation: {operation}, Address: {device_address}, Data: {data_bytes}")

                if operation == "write":
                    response = simulate_i2c_write(device_address, data_bytes)
                elif operation == "read":
                    response = simulate_i2c_read(device_address, bytes_to_read)
                else:
                    response = "Invalid operation"

                connection.send(json.dumps(response).encode('utf-8'))
            except Exception as e:
                print(f"Error: {e}")
                response = "Error processing request"
                connection.sendall(json.dumps(response).encode('utf-8'))
            '''

'''
def simulate_i2c_write(address, data):
    # Simulation of writing data to a device at a given address
    return {"status": "success", "message": f"Data {data} written to address {address}"}

def simulate_i2c_read(address, length):
    # Simulation of reading data from a device at a given address
    return {"status": "success", "data": [0xFF] * length}
'''

def server():
    host = HOST  # Localhost
    port = PORT          # Port to listen on (non-privileged ports are > 1023)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f'Server listening on {host}:{port}')
       
        while True:
       
            conn, addr = s.accept()
            #client_handler(conn)
            thread = threading.Thread(target=client_handler, args=(conn,))
            thread.start()

# Run the server
if __name__ == '__main__':
    create_database()
    server()
