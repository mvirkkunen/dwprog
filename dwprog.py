#!/usr/bin/env python3

import argparse
import sys
import time
from debugwire import DebugWire, DWException
from interfaces import FTDIInterface, SerialInterface
from devices import devices
from binparser import parse_binary

class DWProg:
    BAR_LEN = 50

    def main(self):
        parser = argparse.ArgumentParser()

        parser.add_argument("-p", "--port",
            help="port for interface to use (default=first USB serial adapter found)")
        parser.add_argument("-b", "--baudrate", type=int, default=None,
            help="communication baudrate (default=autodetect)")
        parser.add_argument("-d", "--device",
            help="target device ID (default=autodetect)")
        parser.add_argument("-s", "--stop", action="store_true",
            help="leave target stopped (default=false)")
        parser.add_argument("-q", "--quiet", action="count",
            help="specify once to hide progress bars, twice to hide everything except errors")
        parser.add_argument("-v", "--verbose", action="store_true",
            help="enable debug logging (default=false)")

        subp = parser.add_subparsers()

        pdisable = subp.add_parser("reset", help="reset the target")
        pdisable.set_defaults(func=self.cmd_reset)

        pdisable = subp.add_parser("disable", help="disable debugWIRE and enable ISP")
        pdisable.set_defaults(func=self.cmd_disable)

        pidentify = subp.add_parser("identify", help="identify target device")
        pidentify.set_defaults(func=self.cmd_identify)

        pflash = subp.add_parser("flash", help="flash program to target")
        pflash.add_argument("file", help="file (.hex or .elf) to flash")
        pflash.add_argument("-V", "--no-verify", action="store_true",
            help="skip verification")
        pflash.set_defaults(func=self.cmd_flash)

        pverify = subp.add_parser("verify", help="verify previously flashed program")
        pverify.add_argument("file", help="file (.hex or .elf) to verify")
        pverify.set_defaults(func=self.cmd_verify)

        preadfuses = subp.add_parser("readfuses", help="read and display fuse and lock bits")
        preadfuses.set_defaults(func=self.cmd_readfuses)

        args = parser.parse_args()
        if not hasattr(args, "func"):
            self.log_error("Specify a subcommand.")
            parser.print_usage()
            sys.exit(1)

        self._dev = None
        self.verbosity = 2 - (args.quiet or 0)
        self.stop_after_cmd = args.stop
        self.device_id = args.device

        self.log("Starting dwprog.")

        try:
            interface = SerialInterface(args.port, args.baudrate, timeout=2, enable_log=args.verbose)

            #with DebugWire(FTDIInterface(args.baudrate)) as dw:
            with DebugWire(interface, enable_log=args.verbose) as dw:
                self._dw = dw
                self._dw_is_open = False

                args.func(args)
                self.log("")

                if not self.stop_after_cmd:
                    self.log("Starting program on target.")
                    self.dw.run()
                else:
                    self.log("Target was left stopped.")
        except DWException as ex:
            self.log_error("ERROR: {}".format(str(ex)))
            return 1

        self.log("Existing dwprog successfully.")
        return 0

    def log(self, msg):
        if self.verbosity >= 1:
            print(msg)

    def log_error(self, msg):
        print(msg, file=sys.stderr)

    def progress_bar(self, current, count):
        if self.verbosity >= 2:
            progress = DWProg.BAR_LEN * (current + 1) // count

            print("\r[{0}] page {1}/{2}...".format(
                ("#" * progress) + " " * (DWProg.BAR_LEN - progress),
                current + 1,
                count), end="")
            sys.stdout.flush()

    @property
    def dw(self):
        if not self._dw_is_open:
            self.log("Opening debugWIRE interface...")

            if not self._dw.iface.baudrate:
                self.log("Attempting to auto-detect baudrate...")

            baudrate = self._dw.open()
            self.log("Successfully opened {} at baudrate {}\n".format(
                self._dw.iface.port, self._dw.iface.baudrate))

            self._dw_is_open = True

        return self._dw

    @property
    def dev(self):
        if not self._dev:
            self.log("Getting target device properties.")

            if self.device_id:
                self._dev = next((d for d in devices if d.devid == self.device_id), None)

                if not self._dev:
                    raise DWException("Device '{0}' is not supported.".format(self.device_id))

                sig = self.dw.read_signature()
                if sig != self._dev.signature:
                    raise DWException("Device signature mismatch (expected {0:04x}, got {1:04x})"
                        .format(self._dev.signature, sig))
            else:
                self.log("Auto-detecting target device...")

                sig = self.dw.read_signature()

                self._dev = next((d for d in devices if d.signature == sig), None)

                if not self._dev:
                    raise DWException("Device with signature {0:04x} is not supported."
                        .format(sig))

            self.log("Target is: {0} (signature 0x{1:04x})"
                .format(self._dev.name, self._dev.signature))

        return self._dev

    def cmd_reset(self, args):
        # opening the interface causes a reset
        self.dw

        self.log("Device reset.")

    def cmd_disable(self, args):
        self.dw.disable()

        self.log("debugWIRE is disabled and ISP is enabled until next power cycle.")

    def cmd_identify(self, args):
        self.log("Identifying target device...")

        sig = self.dw.read_signature()

        dev = next((d for d in devices if d.signature == sig), None)

        self.log("Target is: {0} (signature 0x{1:04x})"
            .format(dev.name if dev else "Unknown device", sig))

    def cmd_readfuses(self, args):
        self.log("Reading fuse and lock bits...")

        fuses = self.dw.read_fuses(self.dev)

        self.log("\nFuses: L 0x{0:02X} H 0x{1:02X} E 0x{2:02X}".format(
            fuses.low_fuse, fuses.high_fuse, fuses.extended_fuse))

        self.log("Lock bits: 0x{0:02X}".format(fuses.lock_bits))

    def split_into_pages(self, mem):
        if len(mem) > self.dev.flash_size:
            raise DWException("Binary too large for target.")

        pages = []

        for start in range(0, self.dev.flash_size, self.dev.flash_pagesize):
            page = mem[start:start+self.dev.flash_pagesize]

            if any(b is not None for b in page):
                pagebytes = bytes(0 if b is None else b for b in page)
                pagebytes += b"\00" * max(0, self.dev.flash_pagesize - len(pagebytes))

                pages.append((start, pagebytes))

        return pages

    def do_verify(self, pages):
        self.log("\nVerifying {0} pages ({1} bytes) against target.".format(
            len(pages), len(pages) * self.dev.flash_pagesize))

        start_time = time.time()

        for i, (start, pagebytes) in enumerate(pages):
            self.progress_bar(i, len(pages))

            devbytes = self.dw.read_flash(start, self.dev.flash_pagesize)

            if devbytes != pagebytes:
                self.log_error("\nERROR! Mismatch at 0x{:04x}-0x{:04x}."
                    .format(start, start + self.dev.flash_pagesize))
                return False

        self.log("\nNo errors detected! Verifying took {0}ms."
            .format(round((time.time() - start_time) * 1000)))

        return True

    def cmd_flash(self, args):
        # parse input binary file

        mem = parse_binary(args.file)

        # open and check target device

        pages = self.split_into_pages(mem)

        self.log("\nWriting {0} pages ({1} bytes) to target.".format(
            len(pages), len(pages) * self.dev.flash_pagesize))

        start_time = time.time()

        # write page by page

        for i, (start, pagebytes) in enumerate(pages):
            self.progress_bar(i, len(pages))

            self.dw.write_flash_page(self.dev, start, pagebytes)

        self.log("\nDone! Programming took {0}ms."
            .format(round((time.time() - start_time) * 1000)))

        # verify

        if not args.no_verify:
            if not self.do_verify(pages):
                self.log("Target will be left stopped due to a verification error.")
                self.stop_after_cmd = True
                return

        #self.dw.reset()

    def cmd_verify(self, args):
        # parse input binary file

        mem = parse_binary(args.file)

        # open and check target device

        pages = self.split_into_pages(mem)

        # verify page by page
        self.do_verify(pages)

        #self.dw.reset()

if __name__ == "__main__":
    sys.exit(DWProg().main())
