import socket
import time 

# The keypad host
# This host won't return any data until the communication module is properly configured.
# Simulation notes:
#   To facilitate easier interaction, the IC handling the keypad-to-MCU communication
#   is not actively scanning at a set interval (as it would in real life). Instead,
#   it waits for user input before sending its next command. This way, any network
#   delays should not create problems when interacting with the module.

HOST_1 = 'localhost' # Server hostname or IP address
PORT_1 = 1338  # Server port

# The socker interface
HOST_2 = 'localhost'
PORT_2 = 1337


def interact_with_nc(sock_nc):
    sock_nc.sendall(b"system\n")  # Send 'system' command
    time.sleep(0.5)  # Allow some time for response
    response = sock_nc.recv(4096).decode('utf-8')
    print("Received from NC server:", response)
    return 'HTB{' in response


def simulate_keypad_read(command):
    print('\nNOTES: Simulate the keypad to MCU interaction here')
    print('To interact with the server you must first \nproperly configure the comm-module\n')

def run_client(server_host, server_port):


    # Set the host and port for the netcat server
    nc_host = HOST_2 
    nc_port = PORT_2

    # Create a socket
    sock_nc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the netcat server
    sock_nc.connect((nc_host, nc_port))
    print("Connected to NC interface.")
    
    # check for flag
    interact_with_nc(sock_nc)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        print("Connected to keypad interface")
        

        while True:

            data = sock.recv(1024).decode('utf-8').strip()
            
            if not data:
                print("Server closed the connection")
                break

            print(f"Received from server: {data}")

            # Process incoming data from the server and simulate keypad read
            response = simulate_keypad_read(data)

        

            # check for flag
            interact_with_nc(sock_nc)


if __name__ == "__main__":
    SERVER_HOST = HOST_1   
    SERVER_PORT = PORT_1
    run_client(SERVER_HOST, SERVER_PORT)
