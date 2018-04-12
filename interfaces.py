import time
from debugwire import DWException

def hexdump(data):
    return " ".join("{:02x}".format(b) for b in data)

class BaseInterface:
    def __init__(self, enable_log=False):
        self.enable_log = enable_log

    def _log(self, msg):
        if self.enable_log:
            print(msg)

class BaseSerialInterface(BaseInterface):
    def _detect_baudrate(self):
        # TODO: Make an actual auto-detection algorithm
        for guess in [62500, 12500, 7812, 5000, 6250]:
            self.dev.baudrate = guess

            if 0x55 in self.send_break():
                self._log("Baudrate detected as {}".format(guess))
                return self.dev.baudrate

        raise DWException("Failed to autodetect baudrate.")

    def close(self):
        if self.dev:
            self.dev.close()
            self.dev = None

    def write(self, data):
        data = bytes(data)

        self._log(">"+ hexdump(data))

        start = time.time()

        nwrite = 0
        while nwrite < len(data):
            nwrite += self.dev.write(data[nwrite:])

            if time.time() - start >= self.timeout:
                raise DWException("Write timeout. Check connections and make sure debugWIRE is enabled.")

        self.read(nwrite, _log=False)

    def read(self, nread, _log=True):
        start = time.time()

        buf = b""
        while len(buf) < nread:
            buf += self.dev.read(nread - len(buf))

            if time.time() - start >= self.timeout:
                raise DWException("Read timeout. Check connections and make sure debugWIRE is enabled.")

        if _log:
            self._log("<" + hexdump(buf))

        return buf

class FTDIInterface(BaseSerialInterface):
    def __init__(self, baudrate, timeout=2, enable_log=False):
        super().__init__(enable_log)

        self.port = "FTDI"
        self.baudrate = baudrate
        self.timeout = timeout
        self.dev = None

    def open(self):
        from pylibftdi.serial_device import SerialDevice

        self.dev = SerialDevice()

        if self.baudrate is None:
            self.baudrate = self._detect_baudrate()
        else:
            self.dev.baudrate = self.baudrate

        self.dev.read(1024)

        return self.dev.baudrate

    def send_break(self):
        self._log(">break")

        self.dev.ftdi_fn.ftdi_set_line_property2(8, 0, 0, 1)

        time.sleep(0.002)

        self.dev.ftdi_fn.ftdi_usb_purge_rx_buffer()
        self.dev.read(1024)

        self.dev.ftdi_fn.ftdi_set_line_property2(8, 0, 0, 0)

        time.sleep(0.002)

        return self.read(1)

class SerialInterface(BaseSerialInterface):
    def __init__(self, port, baudrate, timeout=2, enable_log=False):
        super().__init__(enable_log)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.dev = None

    def open(self):
        from serial import Serial

        if self.port is None:
            self._detect_port()

        self.dev = Serial(
            port=self.port,
            baudrate=self.baudrate or 9600,
            timeout=self.timeout,
            write_timeout=self.timeout)

        self.dev.reset_input_buffer()

        if self.baudrate is None:
            self.baudrate = self._detect_baudrate()

        return self.baudrate

    def _detect_port(self):
        from serial.tools.list_ports import comports

        for p in comports():
            if p.vid:
                self.port = p.device
                break
        else:
            raise DWException("Failed to find a USB serial adapter.")

    def send_break(self):
        self._log(">break")

        self.dev.break_condition = True
        time.sleep(0.002)
        self.dev.break_condition = False

        time.sleep(0.002)

        return self.read(2)

interfaces = {
    "serial": SerialInterface,
    "ftdi": FTDIInterface,
}
