import socket

key_presses = '5254#'

current_key_to_send = 0

keymap = {
    '1': ['E0', '0E'],  # First row, first column
    '2': ['D0', '0E'],  # First row, second column
    '3': ['B0', '0E'],  # First row, third column
    'A': ['70', '0E'],  # First row, fourth column
    
    '4': ['E0', '0D'],  # First row, second column
    '5': ['D0', '0D'],  # Second row, second column
    '6': ['B0', '0D'],  # Third row, second column
    'B': ['70', '0D'],  # Fourth row, second column

    '7': ['E0', '0B'],  # First row, third column
    '8': ['D0', '0B'],  # Second row, third column
    '9': ['B0', '0B'],  # Third row, third column
    'C': ['70', '0B'],  # Fourth row, third column

    '*': ['E0', '07'],  # First row, fourth column
    '0': ['D0', '07'],  # Second row, fourth column
    '#': ['B0', '07'],  # Third row, fourth column
    'D': ['70', '07']   # Fourth row, fourth column
}



def simulate_keypad_read(command):
    global current_key_to_send
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

def run_client(server_host, server_port):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        print("Connected to server")

        while True:
            data = sock.recv(1024).decode('utf-8').strip()
            if not data:
                print("Server closed the connection")
                break

            print(f"Received from server: {data}")

            # Process incoming data from the server and simulate keypad read
            response = simulate_keypad_read(data)

            if response:
                sock.sendall(response.encode('utf-8'))  # Send response back to the server
                
            if len(key_presses) == current_key_to_send:
                break

            if data == 'quit':  # Optionally handle a quit command
                print("Quit command received")
                break

            

if __name__ == "__main__":
    SERVER_HOST = 'localhost'  # Server hostname or IP address
    SERVER_PORT = 1338  # Server port
    run_client(SERVER_HOST, SERVER_PORT)
