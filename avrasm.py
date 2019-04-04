"""Extra simple AVR assembler used for some debugWIRE operations."""

def adiw(reg, val):
    return (0x9600
        | ((val & 0x30) << 2)
        | ((((reg - 24) >> 1) & 0x03) << 4)
        | (val & 0x0f))

def in_(addr, reg):
    return (0xb000
        | ((addr & 0x30) << 5)
        | ((reg & 0x1f) << 4)
        | (addr & 0x0f))

def ldi(reg, val):
    return (0xe000
        | ((val & 0xf0) << 4)
        | ((reg - 16) << 4)
        | (val & 0x0f))

def mov(dest, src):
    return (0x2c00
        | ((src & 0x10) << 5)
        | (dest << 4)
        | (src & 0x0f))

def movw(dest, src):
    return (0x0100
        | (((dest >> 1) & 0x0f) << 4)
        | ((src >> 1) & 0x0f))

def out(addr, reg):
    return (0xb800
        | ((addr & 0x30) << 5)
        | ((reg & 0x1f) << 4)
        | (addr & 0x0f))

def lpm():
    return 0x95c8

def spm():
    return 0x95e8
