class Device:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

devices = [
    Device(
        devid="attiny85",
        name="ATtiny85",
        signature=0x930b,
        flash_size=0x2000,
        flash_pagesize=0x40,
        ram_start=0x60,
        ram_size=0x200,
        reg_dwdr=0x42 - 0x20,
        reg_spmcsr=0x57 - 0x20),
]
