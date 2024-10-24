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
from password_db import *
import hashlib
import ast
from config import FLAG

'''
Add logic got address and GPIOs
'''
HOST = '0.0.0.0'
PORT = 1338




CHALLENGE_SOLVED = False


def interface(conn):

	global CHALLENGE_SOLVED, CURRENT_MODULE_ID, ADDRESS_PINS, ADDR_GPIO_MAPPING

	conn.send(b'Remote Command and Control Interface\n')
	
	


	while True:
		
		try:

			conn.send(b'enter password: ')

			password = conn.recv(1024).strip().decode()

			# Hash the secret value using SHA-256
			hash_object = hashlib.md5()
			hash_object.update(password.encode())  # Convert secret to bytes and hash it
			hashed_value = list(hash_object.digest())  # Get the hash as bytes


			db_hash = read_latest_entry(DB_NAME)[0]
			
	
			db_hash = ast.literal_eval(db_hash)  # Convert the string back to a list
		 

			print(db_hash, hashed_value)

			time.sleep(2)

			if db_hash == hashed_value:
				print('Password match!')
				CHALLENGE_SOLVED = True
				conn.send(f'[*] Connecting to interface..\n'.encode())
				time.sleep(1)
				conn.send(f'[*] Retrieving data..\n'.encode())
				time.sleep(2)
				conn.send(f'[*] Data: {FLAG}\n'.encode())
				conn.close()

			else:
				print('Password failed!')
				conn.send('[!] Wrong password!\n'.encode())

			

		except Exception as e:
			print(f'[!] Error: {e}')
			conn.close()
			break
		
		#conn.close()
		time.sleep(0.2)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

	s.bind((HOST, PORT))
	s.listen()
	
	

	while True:
		conn, addr = s.accept()

		#print_lock.acquire()
		print('Connected to :', addr[0], ':', addr[1])
		#start_new_thread( threaded, (conn,))
		interface(conn)

