#!/usr/bin/python3
import socket 
import json
import string
# import thread module
#from _thread import *
#import threading
import time
import random
import sqlite3


'''
Add logic got address and GPIOs
'''
HOST = '0.0.0.0'
PORT = 1337

CORRECT_PIN = '5052'

MSG_WIN = '[*] System is disarmed!\n'
FLAG = open('/app/flag.txt').readline().strip() + '\n'


CHALLENGE_SOLVED = False

GPIO_STATES = {i: 2 for i in range(1, 21)}

CURRENT_MODULE_ID = 0x00

# FOR PCF8574
# https://grobotronics.com/images/companies/1/PCF8574.pdf?1575374643960


ADDRESS_PINS = {
	0: 1,
	1: 1,
	2: 0
}

ADDR_GPIO_MAPPING = {
	1: 0,
	4: 1,
	8: 2, 
}


ADDRESS_SCHEME = lambda ADDRESS_PINS: f'0100{ADDRESS_PINS[2]}{ADDRESS_PINS[1]}{ADDRESS_PINS[0]}'
#Call as:
#ADDRESS_SCHEME(ADDRESS_PINS)


def create_database():
	conn = sqlite3.connect('communication.db')
	cursor = conn.cursor()
	
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS communication (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			IC_Address INTEGER,
			comm_module_address INTEGER
		)
	''')
	
	conn.commit()
	conn.close()
	print("Database and table created (if not exist already).")

def write_to_database(IC_Address, comm_module_address):
	conn = sqlite3.connect('communication.db')
	cursor = conn.cursor()
	
	# Check the number of rows in the table
	cursor.execute('SELECT COUNT(*) FROM communication')
	row_count = cursor.fetchone()[0]
	
	if row_count >= 1:
		# Delete the oldest entry (the one with the smallest id)
		cursor.execute('DELETE FROM communication WHERE id = (SELECT MIN(id) FROM communication)')

	cursor.execute('''
		INSERT INTO communication (IC_Address, comm_module_address)
		VALUES (?, ?)
	''', (IC_Address, comm_module_address))
	
	conn.commit()
	conn.close()
	print(f"Written IC_Address: {IC_Address}, comm_module_address: {comm_module_address} to database.")




def log_status():
	global ADDRESS_SCHEME, CURRENT_MODULE_ID

	ic_address = int(ADDRESS_SCHEME(ADDRESS_PINS), 2)

	write_to_database(ic_address, CURRENT_MODULE_ID)

	print(f'Challenge status {ic_address} {CURRENT_MODULE_ID}')


def read_latest_pin():
	conn = sqlite3.connect('communication.db')
	cursor = conn.cursor()
	
	# Fetch the latest row based on the highest id
	cursor.execute('SELECT * FROM pin_entries ORDER BY id DESC LIMIT 1')
	row = cursor.fetchone()
	
	conn.close()
	return row



def is_integer(s):
	"""
	Check if the input string is a single-digit integer.

	Parameters:
	s (str): The input string to check.

	Returns:
	bool: True if the string is a single-digit integer, False otherwise.
	"""
	if s.isdigit():
		return True
	return False


# GPIO 1 to 9
# Values: 0 to 1
def parse_and_verify_GPIO(input_string):
	# Split the string by space
	parts = input_string.split()

	# Check if we have exactly two parts
	if len(parts) != 2:
		return False, "Input does not consist of two parts separated by a space."

	# Check if both parts are integers
	try:
		number1 = int(parts[0])
		number2 = int(parts[1])


	except ValueError:
		return False, "Both parts must be valid integers."

	if number1 not in range (0,10):
		return False, "GPIO number out of range (0 to 9)"

	if number2 not in range (0,2):
		return False, "GPIO value out of range (0 to 1)"


	return True, (number1, number2)



def parse_pin(pin_entry):
	pin_entry = pin_entry.strip('#')
	print(pin_entry, CORRECT_PIN)
	print(pin_entry == CORRECT_PIN)
	if pin_entry == CORRECT_PIN:
		return True
	
	return False

def clean_pin_entry_db():

    conn = sqlite3.connect('communication.db')
    cursor = conn.cursor()
    
    # Clear the table
    cursor.execute('DELETE FROM pin_entries')
    
    conn.commit()
    conn.close()
    print("Table cleared.")


def interface(conn):

	global CHALLENGE_SOLVED, CURRENT_MODULE_ID, ADDRESS_PINS, ADDR_GPIO_MAPPING

	conn.send(b'Remote Command and Control Interface\n')
	conn.send(b'You can use this interface to configure and control the tools\nattached to the target remotly\n')
	conn.send(b'[*] Entering interactive mode.. [Press "H" for available commands]\n')
	
	while True:
		
		try:
			conn.send(b'cmd> ')

			option = conn.recv(1024).strip().decode()

			if option == 'system': 
				
				time.sleep(0.1)

				if CHALLENGE_SOLVED:
					conn.send(MSG_WIN.encode())
					conn.send(FLAG.encode())
					continue 


				latest_pin = read_latest_pin()
				
				if latest_pin:

					pin_entry = latest_pin[1]
					print(f"PIN: {pin_entry}")

					if pin_entry.endswith('#'):

						response = parse_pin(pin_entry)

						if response:

							CHALLENGE_SOLVED = True
							conn.send(MSG_WIN.encode())
							conn.send(FLAG.encode())

						else:

							conn.send('[!] Incorrect pin!\n'.encode())
							conn.send('[!] Try harder..\n'.encode())

						clean_pin_entry_db()

					else:
						conn.send(b'[!] System is armed!\n')
						conn.send(f'[*] Pin on LCD: {pin_entry}\n'.encode())



					
				else:
					print("No data found.")
					conn.send(b'[!] System is armed!\n')
					conn.send(f'[*] No pin on LCD\n'.encode())



			
			elif option == 'GPIO':
				
				conn.send(b'set> ') 
				gpio_data = conn.recv(1024).strip().decode()
				is_valid, result = parse_and_verify_GPIO(gpio_data)
				
				print(is_valid, result)

				if is_valid:
					print(f"The input is valid: {result}")

					gpio = result[0]
					state = result[1]
					GPIO_STATES[gpio] = state

					if gpio in ADDR_GPIO_MAPPING.keys():
						ADDRESS_PINS[ADDR_GPIO_MAPPING[gpio]] = state

					conn.send((f'GPIO-{str(gpio)} set to: {str(state)}\n').encode()) 
					
				else:
					print(f"Invalid input: {result}")
					conn.send(('Error: ' + result + '\n').encode()) 


			elif option == 'comm-module-id':
				
				conn.send(b'id> ') 
				slave_id = conn.recv(1024).strip().decode()
				is_valid = is_integer(slave_id)

				if is_valid:
					CURRENT_MODULE_ID = slave_id
					conn.send(f'Module ID set to {str(CURRENT_MODULE_ID)}\n'.encode()) 
					
				else:
					conn.send('Invalid ID type (range: 0 to 256)!\n'.encode()) 

			elif option == 'exit':
				conn.send(b'[!] Exiting..\n')
				#print_lock.release()
				conn.close()
				break
			elif option.upper() in ['H', 'HELP']:
				conn.send(b'[*] Available commands:\nsystem: Get system status, and text displayed on the LCD\n        (including the FLAG when the system is disarmed)\nGPIO: change state of a GPIO default is floating (0: LOW, 1: HIGH)\n      example: set> 1 1 (GPIO-1 set to HIGH) \ncomm-module-id: configure the ID of the I2C communication module (0 to 256)\nexit: Exit the interface\n')
			
			else:
				conn.send(b'[!] Not a valid command\n')
				#print_lock.release()
				#conn.close()
				#break


			log_status()

		except Exception as e:
			print(f'[!] Error: {e}')
			conn.close()
			break
		
		#conn.close()
		time.sleep(0.2)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

	s.bind((HOST, PORT))
	s.listen()
	
	create_database()

	while True:
		conn, addr = s.accept()

		#print_lock.acquire()
		print('Connected to :', addr[0], ':', addr[1])
		#start_new_thread( threaded, (conn,))
		interface(conn)

