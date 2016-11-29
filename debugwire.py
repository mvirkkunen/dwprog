import time
import avrasm as asm

# used as pointer for r/w operations
REG_Z = 30

# debugWIRE commands
CMD_DISABLE = 0x06
CMD_RESET = 0x07
CMD_GO = 0x20
CMD_STEP = 0x23
CMD_RUN = 0x30
CMD_RW = 0x66
CMD_RW_MODE = 0xc2
CMD_SET_PC = 0xd0
CMD_SET_BP = 0xd1
CMD_SET_IR= 0xd2
CMD_READ_SIG = 0xf3

# CMD_RW_MODE modes
RW_MODE_READ_SRAM = 0x00
RW_MODE_READ_REGS = 0x01
RW_MODE_READ_FLASH = 0x02
RW_MODE_WRITE_SRAM = 0x04
RW_MODE_WRITE_REGS = 0x05

# SPMCSR register bits
SPMEN = 0x01
PGERS = 0x02
PGWRT = 0x04
CTPB = 0x10

# Mostly everything courtesy of http://www.ruemohr.org/docs/debugwire.html
class DebugWire:
    def __init__(self, iface):
        self.iface = iface

    def open(self):
        """Open the interface and verify the device signature."""

        self.iface.open()
        self.reset()

    def close(self):
        self.iface.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def reset(self):
        """Reset the target device."""

        self.iface.stop()
        #self.iface.write([0x83])
        #self.iface.read(1)
        self.iface.write([CMD_RESET])
        self.iface.read(3)

    def run(self):
        """Run the code on the target device."""

        self.iface.write([CMD_RUN])

    def disable(self):
        """Disable DebugWire and enable ISP until the next power cycle."""

        self.iface.write([CMD_DISABLE])

    def read_signature(self):
        """Returns the device debugWIRE signature as an integer."""

        self.iface.write([CMD_READ_SIG])
        sig = self.iface.read(2)

        return (sig[0] << 8) | sig[1]

    def read_regs(self, start, count):
        """Read registers from the target and return a list."""

        self.iface.write([
            CMD_RW,
            CMD_RW_MODE, RW_MODE_READ_REGS,
            CMD_SET_PC, 0x00, start,
            CMD_SET_BP, 0x00, start + count,
            CMD_GO])

        return self.iface.read(count)

    def write_regs(self, start, values):
        """Write a list of register values to the target."""

        self.iface.write([
            CMD_RW,
            CMD_RW_MODE, RW_MODE_WRITE_REGS,
            CMD_SET_PC, 0x00, start,
            CMD_SET_BP, 0x00, start + len(values),
            CMD_GO] + list(values))

    def read_sram(self, start, count):
        """Read a segment of SRAM memory from the target."""

        end = count * 2

        self.write_regs(REG_Z, [start & 0xff, (start >> 8) & 0xff])

        self.iface.write([
            CMD_RW,
            CMD_RW_MODE, RW_MODE_READ_SRAM,
            CMD_SET_PC, 0x00, 0x00,
            CMD_SET_BP, (end >> 8) & 0xff, end & 0xff,
            CMD_GO])

        return self.iface.read(count)

    def write_sram(self, start, values):
        """Write a segment of SRAM memory to the target."""

        end = len(values) * 2 + 1

        self.write_regs(REG_Z, [start & 0xff, (start >> 8) & 0xff])

        self.iface.write([
            CMD_RW,
            CMD_RW_MODE, RW_MODE_WRITE_SRAM,
            CMD_SET_PC, 0x00, 0x01,
            CMD_SET_BP, (end >> 8) & 0xff, end & 0xff,
            CMD_GO] + list(values))

    def read_flash(self, start, count):
        """Read a segment of flash memory from the target."""

        end = count * 2

        self.write_regs(REG_Z, [start & 0xff, (start >> 8) & 0xff])

        self.iface.write([
            CMD_RW,
            CMD_RW_MODE, RW_MODE_READ_FLASH,
            CMD_SET_PC, 0x00, 0x00,
            CMD_SET_BP, (end >> 8) & 0xff, end & 0xff,
            CMD_GO])

        return self.iface.read(count)

    def _in(self, addr, reg):
        return (0xb000
            | ((addr & 0x30) << 5)
            | ((reg & 0x1f) << 4)
            | (addr & 0x0f))

    def _out(self, addr, reg):
        return (0xb800
            | ((addr & 0x30) << 5)
            | ((reg & 0x1f) << 4)
            | (addr & 0x0f))

    def _exec(self, code):
        for inst in code:
            if type(inst) == bytes:
                self.iface.write(inst)
            else:
                self.iface.write([
                    CMD_SET_IR, (inst >> 8) & 0xff, inst & 0xff, CMD_STEP])

    def write_flash_page(self, dev, start, data):
        if start % dev.flash_pagesize != 0:
            raise Exception("Bad page offset")

        if len(data) != dev.flash_pagesize:
            raise Exception("Bad page size")

        t = time.time()

        # set up constants in registers

        self.write_regs(26, [
            SPMEN,                            # r26
            PGERS | SPMEN,                    # r27
            PGWRT | SPMEN,                    # r28
            CTPB | SPMEN,                     # r29
            start & 0xff, (start >> 8) & 0xff # r30:r31(Z)
        ])

        # clear self-programming buffer

        #self.iface.write([CMD_SET_PC, 0, 0]) # is this necessary...?

        self._exec([
            asm.movw(24, 30),            # movw r24, r30
            asm.out(dev.reg_spmcsr, 29), # out SPMCSR, r29 ; CTPB | SPMEN
            asm.spm()])                  # spm

        self.iface.stop()

        # erase flash page

        self._exec([
            #0x01fc,                     # movw r30, r24 (retrieve address)
            asm.out(dev.reg_spmcsr, 27), # out SPMCSR, r27 ; PGERS | SPMEN
            asm.spm(),                   # spm
        ])

        # wait for erase to complete
        self.iface.stop()

        # write data to buffer

        for i in range(0, len(data), 2):
            self._exec([
                asm.in_(dev.reg_dwdr, 0), bytes([data[i]]),     # in r0, DWDR ; low byte)
                asm.in_(dev.reg_dwdr, 1), bytes([data[i + 1]]), # in r1, DWDR ; high byte)
                asm.out(dev.reg_spmcsr, 26),                    # out SPMCSR, r26 ; SPMEN
                asm.spm(),                                      # spm
                asm.adiw(30, 2)])                               # adiw Z, 2

        # write buffer to flash

        self._exec([
            asm.movw(30, 24),            # movw r30, r24
            asm.out(dev.reg_spmcsr, 28), # out SPMCSR, r28 ; PGWRT | SPMEN
            asm.spm()])                  # spm

        # wait for write to complete
        self.iface.stop()
