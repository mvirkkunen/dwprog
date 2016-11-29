import time

def hexdump(data):
    return " ".join("{:02x}".format(b) for b in data)

# Schematic for serial-to-debugWIRE adapter:
#
# Serial                   AVR
#
#             1k
# TX   o----/\/\/\--\
#                    >---o Reset (pull-up should be 10k)
# RX   o------------/
#
# GND  o-----------------o GND

class BaseInterface:
    def __init__(self, enable_log=False):
        self.enable_log = enable_log

    def _log(self, msg):
        if self.enable_log:
            print(msg)

class FTDIInterface(BaseInterface):
    def __init__(self, baudrate, enable_log=False):
        super().__init__(enable_log)

        self.baudrate = baudrate
        self.dev = None

    def open(self):
        from pylibftdi.serial_device import SerialDevice

        self.dev = SerialDevice()
        self.dev.baudrate = self.baudrate
        self.dev.ftdi_fn.ftdi_usb_purge_rx_buffer()

    def close(self):
        if self.dev:
            self.dev.close()
            self.dev = None

    def stop(self):
        self._log(">stop")

        self.dev.ftdi_fn.ftdi_set_line_property2(8, 0, 0, 1)

        time.sleep(2000e-6)

        self.dev.ftdi_fn.ftdi_usb_purge_rx_buffer()

        time.sleep(200e-6)

        self.dev.ftdi_fn.ftdi_set_line_property2(8, 0, 0, 0)

        self.read(2)

        time.sleep(200e-6)

    def write(self, data):
        data = bytes(data)

        self._log(">"+ hexdump(data))

        nwrite = 0
        while nwrite < len(data):
            nwrite += self.dev.write(data[nwrite:])

        self.read(nwrite, _log=False)

    def read(self, nread, _log=True):
        buf = b""
        while len(buf) < nread:
            buf += self.dev.read(nread - len(buf))

        if _log:
            self._log("<" + hexdump(buf))

        return buf

# for some reason pySerial is about four times slower than pylibftdi

class SerialInterface(BaseInterface):
    def __init__(self, port, baudrate, timeout=2, enable_log=False):
        super().__init__(enable_log)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.dev = None

    def open(self):
        from serial import Serial

        self.dev = Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout)

        self.dev.reset_input_buffer()

    def close(self):
        if self.dev:
            self.dev.close()
            self.dev = None

    def stop(self):
        self._log(">stop")

        self.dev.send_break(0.002)

        #self.dev.reset_input_buffer()

        self.read(2)

        time.sleep(200e-6)

    def write(self, data):
        data = bytes(data)

        self._log(">"+ hexdump(data))

        nwrite = 0
        while nwrite < len(data):
            nwrite += self.dev.write(data[nwrite:])

        self.read(nwrite, _log=False)

    def read(self, nread, _log=True):
        buf = b""
        while len(buf) < nread:
            buf += self.dev.read(nread - len(buf))

        if _log:
            self._log("<" + hexdump(buf))

        return buf

interfaces = {
    "serial": SerialInterface,
    "ftdi": FTDIInterface,
}
