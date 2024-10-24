# https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html
# https://deepbluembedded.com/uart-pic-microcontroller-tutorial/
# UART structure

# We will implement Simplex

# Start bit
#   From high to low for one clock
# Data frame
#   5 to 8 bits if parrity.
#   5 to 9 bits if not parrity
#   LSB first
# Parrity bit
#   The number of 1s to check errors
#   If the parity bit is a 0 the 1 bits in the data frame should total to an even number.
# Stop bit
#   From low to high for at least two-bit durations but most often only one bit is used.

# Example
# O -> 01001111
# O -> 11110010 (data frame)

# ...11111111 0 11110010 1 1 1111111...

import time
import random

FLAG = open("flag.txt", "r").read().strip()

DATA = """
BusyBox v1.19.4 (2020-10-20 22:02:10 CST) built-in shell (ash)
Enter 'help' for a list of built-in commands.

     MM           NM                    MMMMMMM          M       M
   $MMMMM        MMMMM                MMMMMMMMMMM      MMM     MMM
  MMMMMMMM     MM MMMMM.              MMMMM:MMMMMM:   MMMM   MMMMM
MMMM= MMMMMM  MMM   MMMM       MMMMM   MMMM  MMMMMM   MMMM  MMMMM'
MMMM=  MMMMM MMMM    MM       MMMMM    MMMM    MMMM   MMMMMMMMM
MMMM=   MMMM  MMMMM          MMMMM     MMMM    MMMM   MMMMMMM
MMMM=   MMMM   MMMMMM       MMMMM      MMMM    MMMM   MMMMMMMM
MMMM=   MMMM     MMMMMM,   NMMMMMMMM   MMMM    MMMM   MMMMMMMMMM
MMMM=   MMMM      MMMMMM   MMMMMMMM    MMMM    MMMM   MMMM  MMMMMM
MMMM=   MMMM   MM    MMMM    MMMM      MMMM    MMMM   MMMM    MMMM
MMMM$ ,MMMMM  MMMMM  MMMM    MMM       MMMM   MMMMM   MMMM    MMMM
  MMMMMMM:      MMMMMMM     M         MMMMMMMMMMMM  MMMMMMM MMMMMMM
    MMMMMM       MMMMM     M           MMMMMMMMM      MMMM    MMMM
     MMMM          M                    MMMMMMM        M       M
       M

 ---------------------------------------------------------------
   For those about to rock... (%C, %R)
 ---------------------------------------------------------------
root@ArcherC7v5:/# [LEO]uhttpd start
[error]: open file failed : /tmp/client_list.json
[error]: open file failed : /tmp/proxy_mac_list.json
[error]: open file failed : /tmp/"""

DATA += FLAG

DATA += """

root@ArcherC7v5:/# [   68.210000] fast-classifier: starting up
[   68.220000] fast-classifier: registered

SFE STARTED---
root@ArcherC7v5:/#
"""


class UARTTransmitter:

    def __init__(self, baud_rate=9600, data_bits=8, parity=False):
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.parity = parity
        self.bit_duration = 0 if baud_rate == 0 else 1 / baud_rate

    def calculate_parity(self, data):
        return sum([int(bit) for bit in data]) % 2 == 0

    def send_bit(self, bit):
        print(bit, end='', flush=True)  # Print the bit
        time.sleep(self.bit_duration)  # Simulate bit duration

    def halt(self):
        self.send_bit(1)

    def send_data(self, data):
        for char in data:
            # Idle mode (sending ones)
            for _ in range(random.randint(1, 5)):
                self.halt()

            # Start bit (high to low)
            self.send_bit(0)

            # Convert char to binary string
            binary_data = format(ord(char), f'0{self.data_bits}b')
            binary_data = binary_data[::-1]

            # Data bits (LSB first)
            for bit in binary_data:
                self.send_bit(int(bit))

            # Parity bit
            if self.parity:
                parity_bit = 0 if self.calculate_parity(binary_data) else 1
                self.send_bit(parity_bit)

            # Stop bit (low to high)
            self.send_bit(1)


def main():
    # Initialize transmitter with parity enabled, 8 data bits, and baud rate of 9600
    transmitter = UARTTransmitter(baud_rate=9600, data_bits=8, parity=True)

    # Start transmission
    transmitter.send_data(DATA)

    # Just for visuals
    transmitter.bit_duration = 0.01
    while True:
        transmitter.halt()


if __name__ == "__main__":
    main()
