import os

with open("flag.txt", "r") as f:
    FLAG = f.read().strip()

ASSEMBLY = """
        code
        org $4000
        db "PLACEHOLDER"

        org $4300
        ldx #$00
LOOP    lda $4000,x
        sta $6969,x
        inx
        cmp #$20
        bne LOOP

        org $40ff
        dw $4300
"""

ASSEMBLY = ASSEMBLY.replace("PLACEHOLDER", FLAG)


def generate_rom_bytecode():
    with open("flag.a65", "w") as f:
        f.write(ASSEMBLY)

    os.system("./as65  -l -m -w -h0 flag.a65 -oflag.rom >/dev/null 2>&1")
    os.system("rm flag.a65")
    os.system("rm flag.lst")

    with open("flag.rom", "rb") as f:
        bytecode = f.read()

    return bytecode
