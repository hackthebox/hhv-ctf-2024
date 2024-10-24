import string

from cpu import CPU
from mmu import *
from generate import generate_rom_bytecode

WELCOME = """    
   \033[94m**** 6502 FLASHING TOOL V3 ****\033[0m
  \033[94m16K RAM SYSTEM 32K ROM BYTES FREE\033[0m"""

HELP = """\033[94m PRINTL    .PRINTS THE LAYOUT OF THE COMPUTER\033[0m
\033[94m FLASH B   .LOAD HEXADECIMAL BYTECODE INTO THE ROM\033[0m
\033[94m            THE CPU IS RESET AFTER EVERY FLASH\033[0m
\033[94m            EXAMPLE: FLASH FFFFFFFF....FFFFF\033[0m
\033[94m RUN X     .EXECUTE X NUMBER OF OPCODES ON THE CPU\033[0m
\033[94m            EXAMPLE: RUN 10\033[0m
\033[94m CONSOLE   .DISPLAYS THE OUTPUT CONSOLE\033[0m
\033[94m HELP      .DISPLAYS THIS MENU\033[0m"""

READY = """\n\033[94mREADY.\033[0m"""

LAYOUT = """\033[94m
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
 +----------------+                              +-------------+\033[0m"""

ROM = generate_rom_bytecode()


class Emulator:

    def __init__(self):
        self.mmu = MMU([
            (0x0000, 0x4000),  # RAM
            (0x4000, 0x1000, True, ROM),  # FLAG ROM
            (0x6969, 0x20),  # Output Console
            (0x8000, 0x8000, True)  # ROM
        ])
        self.cpu = CPU(self.mmu)

    def print_error(self, e):
        print(f" \033[94mERROR: {e}\033[0m")
        print(READY)

    def parse_bytecode(self, value):
        if not value:
            raise Exception("FLASH COMMAND NEEDS AN ARGUMENT")
        if not (all(c in string.hexdigits
                    for c in value) and len(value) % 2 == 0):
            raise Exception("INVALID HEX FORMAT")
        if len(value) != 2 * 0x8000:
            raise Exception("INCORRECT BYTECODE LENGTH FOR ROM")
        return bytes.fromhex(value)

    def parse_steps(self, value):
        if not value:
            raise Exception("RUN COMMAND NEEDS AN ARGUMENT")
        if not value.isdigit():
            raise Exception("STEP COUNT MUST BE A POSITIVE INTEGER")
        return abs(int(value))

    def print_console(self):
        memory = self.mmu.getBlock(0x6969)['memory']
        row_length = 16
        rows = [
            " ".join(f"{byte:02X}" for byte in memory[i:i + row_length])
            for i in range(0, len(memory), row_length)
        ]
        formatted_output = "\n ".join(rows)
        print(f" \033[94m{formatted_output}\033[0m")

    def flash_rom(self, bytecode):
        self.mmu = MMU([(0x0000, 0x4000), (0x4000, 0x1000, True, ROM),
                        (0x6969, 0x20), (0x8000, 0x8000, True, bytecode)])
        self.cpu = CPU(self.mmu)

    def run_cpu(self, steps):
        print(" \033[94mOC PC\033[0m")
        for _ in range(steps):
            rs = self.cpu.r
            pc = rs.pc
            self.cpu.step()
            print(f" \033[94m{self.cpu.current_opcode:02X}\033[0m", end=' ')
            print(f"\033[94m{pc:04X}\033[0m")

    def handle_command(self, command, value=None):
        if command == "PRINTL":
            print(LAYOUT)
        elif command == "CONSOLE":
            self.print_console()
        elif command == "FLASH" and value:
            bytecode = self.parse_bytecode(value)
            self.flash_rom(bytecode)
        elif command == "RUN" and value:
            steps = self.parse_steps(value)
            self.run_cpu(steps)
        elif command == "HELP":
            print(HELP)
        else:
            raise Exception("INVALID COMMAND")
        print(READY)

    def start(self):
        print(WELCOME)
        print(READY)
        print("HELP")
        self.handle_command("HELP")

        while True:
            try:
                user_input = input().strip().split(maxsplit=1)
                command = user_input[0] if len(user_input) > 0 else ""
                value = user_input[1] if len(user_input) > 1 else None
                self.handle_command(command, value)
            except KeyboardInterrupt:
                exit()
            except ReadOnlyError:
                e = "TRIED TO WRITE A READ ONLY MEMORY"
                self.print_error(e)
            except InvalidBlockError:
                e = "ACCESSED AN INVALID MEMORY ADDRESS"
                self.print_error(e)
            except Exception as e:
                self.print_error(e)


if __name__ == "__main__":
    emulator = Emulator()
    emulator.start()
