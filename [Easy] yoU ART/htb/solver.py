from pwn import remote, args, process


class UARTReceiver:

    def __init__(self, connection, baud_rate=9600, data_bits=8, parity=False):
        self.connection = connection
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.parity = parity
        self.bit_duration = 1 / baud_rate

    def calculate_parity(self, data):
        return sum([int(bit) for bit in data]) % 2 == 0

    def receive_bit(self):
        bit = self.connection.recv(1).decode('utf-8')
        return int(bit)

    def receive_byte(self):
        # Wait for start bit (high to low transition)
        bit = self.receive_bit()
        while bit != 0:
            bit = self.receive_bit()

        # Read data bits
        data_bits = []
        for _ in range(self.data_bits):
            bit = self.receive_bit()
            data_bits.append(str(bit))

        binary_data = ''.join(data_bits[::-1])  # Reversed to LSB first
        char = chr(int(binary_data, 2))

        # Read parity bit
        if self.parity:
            parity_bit = self.receive_bit()
            expected_parity = 0 if self.calculate_parity(data_bits) else 1
            if parity_bit != expected_parity:
                print("Error: Parity bit mismatch")

        # Read stop bit
        _ = self.receive_bit()
        return char


def pwn(connection):
    receiver = UARTReceiver(connection,
                            baud_rate=100,
                            data_bits=8,
                            parity=True)
    while True:
        print(receiver.receive_byte(), end='')


if __name__ == "__main__":
    if args.REMOTE:
        ip, port = args.HOST.split(":")
        connection = remote(ip, int(port))
    else:
        connection = process("python3 server.py",
                             shell=True,
                             cwd="../challenge")

    pwn(connection)
