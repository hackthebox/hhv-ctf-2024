from pwn import args, remote
import os

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


def toAscii(data):
    return data.decode().strip()


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


def pwn():
    r.recvuntil(b"READY.")
    bytecode = assembler(ASSEMBLY)
    flash_rom(bytecode)
    run_cpu(163)
    print_console()
    flag = get_flag()
    flag = parse_flag(flag)
    print(flag)


if __name__ == "__main__":
    ip, port = args.HOST.split(":")
    r = remote(ip, int(port))
    pwn()
