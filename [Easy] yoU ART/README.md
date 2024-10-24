![img](assets/images/banner.png)

<img src='assets/images/htb.png' style='margin-left: 20px; zoom: 80%;' align=left /> <font size='10'>yoU ART</font>

28<sup>th</sup> 2022 / Document No. D22.102.16

Prepared By: WizardAlfredo

Challenge Author(s): WizardAlfredo

Difficulty: <font color=green>Easy</font>

Classification: Official

# Synopsis

- Decode Dynamic UART data.

## Description

- We've discovered that the recent patch deleted critical files from the cybernetic enhancements. To restore functionality, we need to identify which files were removed. Diagnostics checks run during the device's boot process and should reveal that information. We've connected our serial debugger to the device's debugging interface, capturing the output from the transmitting pin. Can you analyze the data and help us pinpoint the missing files?

## Skills Required

- Basic research skills.
- Basic coding skills.

## Skills Learned

- Combining online resources to implement a protocol decoder.
- Improved understanding of communication between embedded devices.
- Enhanced understanding of the UART protocol.

# Enumeration

## Analyzing the source code

There is no source code to analyze, so we will proceed directly to the nc instance.

## Connecting to nc

Connecting to the server results in an output of bits for several seconds before it outputs a stream of 1s.

```txt
11100101000001111001000010011111010101110111111011001110111110100111101111111001000010011110111101100111110000111100110000001001111100110111011111101000110011110011101000111010001100111010011100011111<SNIP>111111111111111111111111111111111111111111111111111111111111111
```

Since we know this is a UART connection, we can start by researching the protocol further.

# Solution

## Finding the vulnerability

Typically, developers include a login prompt in UART, but here, we do not have such a prompt, allowing us to read the data being sent.

## Exploitation

### Connecting to the server

A pretty basic script for connecting to the server with `pwntools`:

```python
if __name__ == "__main__":
    r = remote("0.0.0.0", 1337)
    pwn()
```

### UARTReceiver

To receive the actual data, we can create a class called `UARTReceiver` and implement a function to receive its bits separately, allowing us to analyze them.

```python
    def receive_bit(self):
        bit = self.connection.recv(1).decode('utf-8')
        return int(bit)
```

#### Decoding

It is time to examine UART more closely, particularly its data transmission process. By searching online, we can find numerous articles on the subject, such as [this one](https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html). When sending data using the protocol, encoding is required before and after the actual data:

![uart](https://www.analog.com/en/_/media/images/analog-dialogue/en/volume-54/number-4/articles/uart-a-hardware-communication-protocol/335962-fig-03.svg?w=900&rev=ad33a0f741fd40a79887152fcf0b7944)

##### Start bit

As depicted, the start bit is 1 bit, representing a transition from a high to low bit for one clock cycle. Observing our first byte transfer:

```txt
111001010000011
```

We see that the server is initially at a logic high for 3 clocks, and the first zero, or logic low, is transmitted, indicating our start bit. We can implement this in code as follows:

```py
    def receive_byte(self):
        # Wait for start bit (high to low transition)
        bit = self.receive_bit()
        while bit != 0:
            bit = self.receive_bit()
```

##### Data bits

The data frame contains the actual data being transferred. It can be 5 to 8 bits long if a parity bit is used. Without a parity bit, the data frame can be 9 bits long. Typically, data is sent with the least significant bit first. In our case, we have 8-bit-long data frames.

```txt
Halt | start | data     |
111  | 0     | 01010000 | 01
111  | 0     | 01000010 | 01
1111 | 0     | 10101110 | 11
1111 | 0     | 11001110 | 11
111  | 0     | 10011110 | 11
<SNIP>
```

And the code:

```py
        # Read data bits
        data_bits = []
        for _ in range(self.data_bits):
            bit = self.receive_bit()
            data_bits.append(str(bit))

        binary_data = ''.join(data_bits[::-1])  # Reversed to LSB first
        char = chr(int(binary_data, 2))
```

##### Parity

Parity describes the evenness or oddness of a number. The parity bit allows the receiving UART to verify if any data has changed during transmission. After reading the data frame, the receiving UART counts the number of bits with a value of 1 and checks if the total is even or odd. If the parity bit is 0 (even parity), the 1 or logic-high bits in the data frame should total an even number. If the parity bit is 1 (odd parity), the 1 bits or logic highs in the data frame should total an odd number.

In our example, we confirm the presence of a parity bit:

```txt
111001010000011 ->

Halt | start | data     | parity |
111  | 0     | 01010000 | 0  	 | 1
```

```python
    def calculate_parity(self, data):
        return sum([int(bit) for bit in data]) % 2 == 0

<SNIP>

        # Read parity bit
        if self.parity:
            parity_bit = self.receive_bit()
            expected_parity = 0 if self.calculate_parity(data_bits) else 1
            if parity_bit != expected_parity:
                print("Error: Parity bit mismatch")

```

##### Stop bit

Finally, we have the stop bit. To signal the end of the data packet, the sending UART drives the data transmission line from a low voltage to a high voltage for one (1) to two (2) bits in duration. In this case, we have one bit. We can implement this as follows:

```py
        # Read stop bit
        _ = self.receive_bit()
        return char
```

### Getting the flag

We can repeat the process of receiving a byte while we retrieve the flag.

A final summary of all that was said above:

1. Fetch each bit.
2. Decode each packet based on the protocol specifications.
3. Print the decoded ouptut.

This recap can be represented by code with the `pwn()` function:

```python
def pwn(connection):
    receiver = UARTReceiver(connection,
                            baud_rate=100,
                            data_bits=8,
                            parity=True)
    while True:
        print(receiver.receive_byte(), end='')
```
