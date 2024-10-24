![img](assets/banner.png)

<img src='assets/htb.png' style='margin-left: 20px; zoom: 80%;' align=left /> <font size='10'>FF Jump Street</font>

28<sup>th</sup> 2022 / Document No. D22.102.16

Prepared By: WizardAlfredo

Challenge Author(s): WizardAlfredo

Difficulty: <font color=green>Easy</font>

Classification: Official

# Synopsis

- Bypass a hardware bug on the 6502 by writing 6502 assembly.

## Description

- We found a heavily modified module containing legacy hardware merged with corrupted components. We believe the legacy module can access the memory area where the secret key is stored and output it to its console. Unfortunately, the legacy IC we have is unable to reach that address due to a hardware bug.

## Skills Required

- Basic research skills.
- Basic understanding of computer operations.

## Skills Learned

- Integrating online resources to write 6502 assembly code.
- Enhanced understanding of the 6502 CPU.
- Improved comprehension of CPU communication with ROMs and I/O.

# Enumeration

## Analyzing the source code

There is no source code to analyze except for the template provided for the solver, so we will connect to the instance.

## Connecting to nc

### The HELP menu

Upon connecting, we are presented with the following HELP menu:

```

   **** 6502 FLASHING TOOL V3 ****
  16K RAM SYSTEM 32K ROM BYTES FREE

READY.
HELP
 PRINTL    .PRINTS THE LAYOUT OF THE COMPUTER
 FLASH B   .LOAD HEXADECIMAL BYTECODE INTO THE ROM
            THE CPU IS RESET AFTER EVERY FLASH
            EXAMPLE: FLASH FFFFFFFF....FFFFF
 RUN X     .EXECUTE X NUMBER OF OPCODES ON THE CPU
            EXAMPLE: RUN 10
 CONSOLE   .DISPLAYS THE OUTPUT CONSOLE
 HELP      .DISPLAYS THIS MENU

READY.
```

This interface resembles that of a C64. It appears to be a tool for flashing a 6502 CPU. We have several options to choose from. Let us begin by viewing the layout of the computer we intend to program.

```
PRINTL

     +------------+                              +-----------+
     |       HTB{ |                 $0000-$3FFF  |           |
     |  ROM  .... |--------------..--------------|    RAM    |
     |       ...} |              ||              |           |
     +------------+              ||              +-----------+
                    +--------------------------+
                    |                          |
                    |       MOS 6502           |
                    |       1 MHz, 8-bit       |             HERE IS WHERE
                    |       Microprocessor     |             WE FLASH OUR
                    |                          |             BYTECODE.
                    +--------------------------+                   |
 +----------------+              ||              +-------------+   |
 |         .----. |              ||              |        .... |   |
 | CONSOLE |>   | |--------------''--------------|   ROM  .... |<--'
 |         '----' |                 $8000-$FFFF  |        .... |
 +----------------+                              +-------------+

READY.
```

We observe two **ROM** chips: one that can be programmed and one that contains the routine that outputs the flag to the console. There is also some **RAM** and a **console**. Referring back to the help menu, we note that we can program the ROM using the `FLASH` command, execute a number of opcodes with the `RUN` command, and display the console output using the `CONSOLE` command. For a proof of concept, let’s try these commands.

`RUN 1`:

```
RUN 1
 PC   OC
 0000 00

READY.
```

The RUN command also shows the program counter's position and the opcode being executed.

`CONSOLE`:

```
CONSOLE
 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00

READY.
```

### Address mappings

It is important to understand the address spaces reserved for each component:

\$0000 to \$3fff - **RAM**
\$???? to \$???? - **ROM** containing the flag routine
\$???? to \$???? - **Console**
\$8000 to \$ffff - Programmable **ROM**

We are missing some of them, but hopefully, we will not need them.

### The reset vector

Now, we need to research the 6502 CPU. Fortunately, there are numerous emulators and guides available online. We will start with [this](http://www.6502.org/users/obelisk/6502/) page. Let us explore the [architecture](http://www.6502.org/users/obelisk/6502/architecture.html) of the 6502. Importantly:

> The only other reserved locations in the memory map are the very last 6 bytes of memory \$FFFA to \$FFFF which must be programmed with the addresses of the non-maskable interrupt handler (\$FFFA/B), the power on reset location (\$FFFC/D) and the BRK/interrupt request handler (\$FFFE/F) respectively.

As mentioned in the help menu, after a `FLASH` command, the CPU resets, jumping to the reset vector \$FFFC/D. Additional details about the reset process can be found on [this](https://www.pagetable.com/?p=410) page:

> On a RESET, the CPU loads the vector from \$FFFC/$FFFD into the program counter and continues fetching instructions from there.

We are also provided with a `template.py` script and a `as65` binary file. The template.py script includes several utility functions to assist with communication with the nc instance. These functions include:

```py
def flash_rom(bytecode):
    r.sendlineafter(b"READY.", b"FLASH " + bytecode.encode())

def run_cpu(steps):
    r.sendlineafter(b"READY.", b"RUN " + str(steps).encode())

def print_console():
    r.sendlineafter(b"READY.", b"CONSOLE")

def get_flag():
    r.recvuntil(b"\x1b[94m")
    first = toAscii(r.recvline())
    second = toAscii(r.recvuntil(b"\x1b[0m")[1:-4])
    return first + " " + second


def parse_flag(flag):
    flag = "".join([bytes.fromhex(byte).decode() for byte in flag.split(" ")])
    return flag
```

It also contains some 6502 assembly and a function to assemble it:

```py
ASSEMBLY = """
        code
        org $8000

        ; main function
        jmp ($40ff) ; fix this

        ; reset vector
        org $fffc
        dw $8000
        dw $ffff
"""


def assembler(assembly):
    with open("solver.a65", "w") as f:
        f.write(assembly)

    os.system("./as65  -l -m -w -h0 solver.a65 -osolver.rom")

    with open("solver.rom", "rb") as f:
        bytecode = f.read().hex()
    return bytecode

```

We can see that the reset vector is handled for us, and the only task remaining is to address the `; fix this` line.

### Recap

To summarize our findings:

- We can flash our own bytecode to the CPU using the `FLASH` command.
- We can run our code using the `RUN` command.
- Upon reset, the CPU jumps to the address at $FFFC/FFFD and fetches instructions from there.
- Everything is handled by the `template.py` script so we have to focus on the `fix this` comment

# Solution

## Finding the vulnerability

Given the challenge description, which mentions a hardware bug, and the presence of a `jmp ($40ff)` instruction, we can search for a known jump indirect hardware bug in the 6502. There are many discussions regarding this bug, such as [this one](https://atariwiki.org/wiki/Wiki.jsp?page=6502%20bugs):

> An indirect JMP (xxFF) will fail because the MSB will be fetched from address xx00 instead of page xx+1.

## Exploitation

Having reviewed the `template.py` script, let us proceed directly to the assembly code.

### The assembly

Let us revisit the provided assembly code.

```assembly
        code
        org $8000

        ; main function
        jmp ($40ff) ; fix this

        ; reset vector
        org $fffc
        dw $8000
        dw $ffff
```

The primary issue lies with the `jmp ($40ff)` instruction. Let us examine the expected and actual behavior of the CPU.

When performing a JMP indirect instruction to \$40ff, we expect the following sequence:

1. Fetch a byte `yy` from address \$40ff
2. Fetch a byte `xx` from address \$40ff + 1 = \$4100
3. Jump to memory address `xxyy`.

Unfortunately, the 6502 behaves differently:

1. Fetch a byte `yy` from address \$40ff
2. Fetch a byte `xx` from address \$4000
3. Jump to memory address `xxyy`.

We observe that when crossing a memory page boundary, the 6502 incorrectly wraps around and fetches the MSB byte from \$4000 instead of \$4100. We need to address this issue to ensure the code jumps to the correct routine. To achieve this, we will manually implement the expected behavior.

First, load the values from \$40ff and \$4100 into our registers:

```assembly
        lda $40ff
        ldx $4100
```

Then, store these values in RAM:

```assembly
        sta $3000
        stx $3001
```

Finally, perform an indirect jump to this new memory location that does not cross a memory page boundary:

```assembly
        jmp ($3000)
```

The final code will be:

```assembly
        code
        org $8000

        ; main function
        ; jmp ($40ff)
        lda $40ff
        ldx $4100
        sta $3000
        stx $3001
        jmp ($3000)

        ; reset vector
        org $fffc
        dw $8000
        dw $ffff
```

### Flash and Run

Finally, flash the code to the ROM and execute it using the helper functions provided.

### Getting the flag

The final summary of the steps:

1. Write the assembly code and assemble it.
2. Flash the code to the ROM.
3. Run the code.
4. Parse the flag from the console output.

This can be represented in code by the `pwn()` function:

```python
def pwn():
    r.recvuntil(b"READY.")
    bytecode = assembler()
    flash_rom(bytecode)
    run_cpu(160)
    print_console()
    flag = parse_flag()
    print(flag)
```
