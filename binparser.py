# A list isn't the most efficient way to store a potentially sparse set of memory segments, but then
# again this isn't exactly designed for huge programs.

MAX_ADDRESS = 0xffff

class memlist(list):
    def __init__(self, max_size):
        self._max_size = max_size

    def write(self, offset, values):
        if offset + len(values) > self._max_size:
            raise Exception("Binary does not fit in memory")

        while len(self) < offset + len(values):
            self.append(None)

        for i, b in enumerate(values):
            self[offset + i] = b

def parse_hex(mem, f):
    for line in f:
        if line[0:1] != b":":
            raise Exception("Invalid hex line prefix")

        lb = bytes.fromhex(line.decode("ascii").strip(":\r\n"))

        count = lb[0]
        if count + 5 != len(lb):
            raise Exception("Invalid hex line length")

        addr = (lb[1] << 8) | lb[2]
        rtype = lb[3]

        checksum = 0x100 - (sum(lb[:-1]) & 0xff)
        if checksum != lb[-1]:
            raise Exception("Invalid hex line checksum")

        if rtype == 0x00:
            mem.write(addr, lb[4:-1])
        elif rtype == 0x01:
            pass
        else:
            raise Exception("Unknown hex line")

def parse_elf(mem, f):
    from elftools.elf.elffile import ELFFile
    from elftools.elf.enums import ENUM_E_MACHINE

    elf = ELFFile(f)

    if elf["e_machine"] != "EM_AVR":
        raise Exception("Invalid ELF architecture")

    for s in elf.iter_segments():
        if s["p_filesz"] > 0:
            mem.write(s["p_paddr"], s.data())

def parse_binary(filename, flash_size, flash_pagesize):
    with open(filename, "rb") as f:
        magic = f.read(9)
        f.seek(0)

        mem = memlist(flash_size)

        if magic[:4] == b"\x7fELF":
            parse_elf(mem, f)
        elif len(magic) == 9 and magic[0:1] == b":" and magic[7:9] in (b"00", b"01"):
            parse_hex(mem, f)
        else:
            raise Exception("Unknown binary file type.")

        pages = []

        for start in range(0, flash_size, flash_pagesize):
            page = mem[start:start+flash_pagesize]

            if any(b is not None for b in page):
                pagebytes = bytes(0 if b is None else b for b in page)
                pagebytes += b"\00" * max(0, flash_pagesize - len(pagebytes))

                pages.append((start, pagebytes))

        return pages
