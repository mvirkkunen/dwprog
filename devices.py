# Generated with generatedevices.py

class Device:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

devices = [
    Device(devid="at90usb162", name="AT90USB162", signature=0x9482, flash_size=0x4000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="at90usb82", name="AT90USB82", signature=0x9682, flash_size=0x2000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="atmega16u2", name="ATmega16U2", signature=0x9489, flash_size=0x4000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="atmega32u2", name="ATmega32U2", signature=0x958a, flash_size=0x8000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="atmega8u2", name="ATmega8U2", signature=0x9389, flash_size=0x2000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="attiny13", name="ATtiny13", signature=0x9007, flash_size=0x400, flash_pagesize=0x20, reg_dwdr=0x2e, reg_spmcsr=0x37),
    Device(devid="attiny13a", name="ATtiny13A", signature=0x9007, flash_size=0x400, flash_pagesize=0x20, reg_dwdr=0x2e, reg_spmcsr=0x37),
    Device(devid="attiny167", name="ATtiny167", signature=0x9487, flash_size=0x4000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
    Device(devid="attiny25", name="ATtiny25", signature=0x9108, flash_size=0x800, flash_pagesize=0x20, reg_dwdr=0x22, reg_spmcsr=0x37),
    Device(devid="attiny261", name="ATtiny261", signature=0x910c, flash_size=0x800, flash_pagesize=0x20, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny261a", name="ATtiny261A", signature=0x910c, flash_size=0x800, flash_pagesize=0x20, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny45", name="ATtiny45", signature=0x9206, flash_size=0x1000, flash_pagesize=0x40, reg_dwdr=0x22, reg_spmcsr=0x37),
    Device(devid="attiny461", name="ATtiny461", signature=0x9208, flash_size=0x1000, flash_pagesize=0x40, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny461a", name="ATtiny461A", signature=0x9208, flash_size=0x1000, flash_pagesize=0x40, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny85", name="ATtiny85", signature=0x930b, flash_size=0x2000, flash_pagesize=0x40, reg_dwdr=0x22, reg_spmcsr=0x37),
    Device(devid="attiny861", name="ATtiny861", signature=0x930d, flash_size=0x2000, flash_pagesize=0x40, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny861a", name="ATtiny861A", signature=0x930d, flash_size=0x2000, flash_pagesize=0x40, reg_dwdr=0x20, reg_spmcsr=0x37),
    Device(devid="attiny87", name="ATtiny87", signature=0x9387, flash_size=0x2000, flash_pagesize=0x80, reg_dwdr=0x31, reg_spmcsr=0x37),
]
