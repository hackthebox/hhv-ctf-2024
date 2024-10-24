import time
import random
#from tqdm import tqdm


#from serialized import *
from address_calc import * 


import socket
import threading
import asyncio
from config import *



from chall_scenario import *

'''
SCENARIO:
Similar memory to W25Q128JV 
ex. W25Q128JV-X

'''
#TODO:

'''
1. Verify correct operation of simulation
2. Instruction set executiong function
3. Wrapper for players
4. Make class async
5. Socket interface for users to communicate
6. Scenario
7. Material to support scenario
'''

#   Registers
#   Security
#   Protection
#   SFDP
#   Single, Dual and Quad is the same

'''
When are they volatile when not ?
 Volatile/Non-Volatile Writable

Check if self.write_disable() is everywhere it should be (ie in every function before all Returns if WE is needed to run )

TypeError: write_enable() missing 1 required positional argument: 'instruction_code'


Dummy bytes count?
'''






# For registers that shift out until CS is low
def wrap_arround_out(register, bytes_to_return):

    # Output buffer
    data_out = []
    # Fill the output buffer with the repeated security register content
    while len(data_out) < bytes_to_return:
        data_out.extend(register)
    
    # Trim the output buffer to the requested length
    data_out = data_out[:bytes_to_return]

    return data_out


from flash_memory import *
       
# Example usage of the FlashMemorySimulation class

flash = FlashMemorySimulation()

'''
data = flash.execute_instruction([0x9F], 3)
data = flash.execute_instruction([0x9F], 3)
print(data)

data = flash.execute_instruction([0x06], 0)

data = flash.execute_instruction([0x02, 0x00, 0x00, 0x12, 0x01, 0x02, 0x03, 0x04])

data = flash.execute_instruction([0x03, 0x00, 0x00, 0x00], 256)
print(data)


UID = flash.execute_instruction([0x4B, 0x00, 0x00, 0x00, 0x00], 8)
print('DEVICE ID:', UID)
'''

'''
# program_security_register
random_data = [random.randint(0, 0xff) for _ in range(256)]
data = flash.execute_instruction([0x06])
flash.execute_instruction([0x42, 0x00, 0x10, 0x00]+random_data)


# get KEY from security register
security_register_data = flash.execute_instruction([0x48, 0x00, 0x10, 0x52], 12)
print('security_register:', security_register_data)

key = security_register_data

logs_to_write = generate_memory_data(key)
addresses = get_log_addresses()

for i in range(0,len(logs_to_write)):
    log = logs_to_write[i]
    address = addresses[i]
    print(address, log)
    flash.execute_instruction([0x06])
    flash.execute_instruction([0x02] + address + log)


data = flash.execute_instruction([0x03, 0x00, 0x00, 0x00], 256*12)

bytes_list = data
# Printing the list as lines of 16 bytes each
pages = 0
for i in range(0, len(bytes_list), 16):
    line = bytes_list[i:i+16]
    print(' '.join(f'{byte:02x}' for byte in line))

    if not i % 256 and i != 0:
        pages += 1
        print('\n')

print('Total pages:', pages)
print('Total sectors:', pages/16)

flash.execute_instruction([0x06])

#flash.execute_instruction([0x20, 0x00, 0x00, 0x00])

data = flash.execute_instruction([0x03, 0x00, 0x00, 0x00], 256*16)

bytes_list = data
# Printing the list as lines of 16 bytes each
pages = 0
for i in range(0, len(bytes_list), 16):
    line = bytes_list[i:i+16]
    print(' '.join(f'{byte:02x}' for byte in line))

    if not i % 256 and i != 0:
        pages += 1
        print('\n')


mem = copy.deepcopy(flash.memory[:4096])



for i in range(0, len(mem), 16):
    line = mem[i:i+16]
    print(' '.join(f'{byte:02x}' for byte in line))

    if not i % 256 and i != 0:
        pages += 1
        print('\n')


#original_data = mem[:LOG_ENTRIES*LOG_ENTRY_LEN]

flash.execute_instruction([0x04])
'''




import socket
import threading
import json
import time

counter = 0


from check_challenge import *

def client_handler(connection):
    global flash, counter
    # Configure according to your setup
    correst_cs_pin=0 
    correct_usb_device_urls = ['ftdi://ftdi:2232h/0','ftdi://ftdi:2232h/1']

    with connection:
        print('Client connected')
        while True:
            data = b''
            
            while True:
                #print('waitinggg')
                data += connection.recv(1024)
                #print(data)
                if b'}' in data:
                    break
            
    
            #counter = incrimenter_yio(counter)
            
            # Deserialize the data from JSON
            try:
                packet = json.loads(data.decode('utf-8'))
                command = packet["tool"]
                cs_pin = packet["cs_pin"]
                device_url = packet["url"]

                #memory = get_spi_port(cs_pin, device_url)

                hex_data = [int(x, 16) for x in packet["data_out"]]  # Convert hex strings back to integers
                bytes_to_read = packet["readlen"]
                print(f"Received command: {command}, hex_data: {hex_data}, value: {bytes_to_read}")
                
                # Simulate processing the command
                if command == "pyftdi":
                    if cs_pin == correst_cs_pin and device_url in correct_usb_device_urls:
                        response = f"Data exchanged with hex values {hex_data} and integer {bytes_to_read}"
                        
                        mem_out = flash.execute_instruction(hex_data, bytes_to_read)                       
                        print(mem_out)

                        response = list(mem_out)
                    else:
                        response = [0xFF]*bytes_to_read
                else:
                    response = "Invalid command"


                check_challenge(flash)

                connection.send(json.dumps(response).encode('utf-8'))
            

            except Exception as e:
                print(f"Error: {e}")
                response = "Error processing request"

                connection.sendall(json.dumps(response).encode('utf-8'))

def server():
    host = HOST  # Localhost
    port = PORT   # Port to listen on (non-privileged ports are > 1023)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f'Server listening on {host}:{port}')
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=client_handler, args=(conn,))
            thread.start()

# Run the server
server()
