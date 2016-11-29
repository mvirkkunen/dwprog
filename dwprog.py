#!/usr/bin/env python3

import argparse
import sys
import time
from debugwire import DebugWire
from interfaces import FTDIInterface, SerialInterface
from devices import devices
from binparser import parse_binary

BAR_LEN = 40

def panic(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def cmd_reset(args):
    dw.open()
    dw.reset()

    print("Device reset.")

def cmd_disable(args):
    dw.open()
    dw.reset()
    dw.disable()

    print("debugWIRE is disabled and ISP is enabled until next power cycle.")

def cmd_readsig(args):
    dw.open()
    print("Device signature: {:04x}".format(dw.read_signature()))

def cmd_flash(args):
    if not args.device:
        panic("Device must be specified for programming.")

    if not args.device in devices:
        panic("Unsupported device: " + args.device)

    dev = devices[args.device]

    # parse input binary file

    try:
        mem = parse_binary(args.file)
    except Exception as e:
        panic(e.strerror)

    # convert binary file to a list of pages to write

    pages = []

    for start in range(0, dev.flash_size, dev.flash_pagesize):
        page = mem[start:start+dev.flash_pagesize]

        if any(b is not None for b in page):
            pagebytes = bytes(0 if b is None else b for b in page)
            pagebytes += b"\00" * max(0, dev.flash_pagesize - len(pagebytes))

            pages.append((start, pagebytes))

    print("Writing {0} pages ({1} bytes) to target.".format(
        len(pages), len(pages) * dev.flash_pagesize))

    start_time = time.time()

    # open and reset device

    dw.open()
    dw.reset()

    # ensure device signature is corect

    sig = dw.read_signature()
    if sig != dev.signature:
        panic("Device signature mismatch (expected {:04x}, got {:04x})"
            .format(self.dev.signature, sig))

    # write page by page

    for i, (start, pagebytes) in enumerate(pages):
        progress = BAR_LEN * (i + 1) // len(pages)

        print("\r[{0}] page {1}/{2}...".format(
            ("#" * progress) + " " * (BAR_LEN - progress),
            i + 1,
            len(pages)), end="")
        sys.stdout.flush()

        dw.write_flash_page(dev, start, pagebytes)

    dw.reset()

    print("\nDone! Programming took {0}ms.".format(round((time.time() - start_time) * 1000)))

parser = argparse.ArgumentParser()

#parser.add_argument("-i", "--interface",
#    help="interface type (serial:/dev/ttyX, ftdi[:device_id])")
parser.add_argument("-b", "--baudrate", type=int, default=62500,
    help="communication baudrate (default=62500)")
parser.add_argument("-d", "--device",
    help="target device ID")
parser.add_argument("-s", "--stop", action="store_true",
    help="leave execution stopped")

subp = parser.add_subparsers()

pdisable = subp.add_parser("reset", help="reset the target")
pdisable.set_defaults(func=cmd_reset)

pdisable = subp.add_parser("disable", help="disable debugWIRE and enable ISP")
pdisable.set_defaults(func=cmd_disable)

preadsig = subp.add_parser("readsig", help="read target device signature")
preadsig.set_defaults(func=cmd_readsig)

pflash = subp.add_parser("flash", help="flash program to target")
pflash.add_argument("file", help="file (.hex or .elf) to flash")
pflash.set_defaults(func=cmd_flash)

args = parser.parse_args()
if not hasattr(args, "func"):
    print("Specify a subcommand.")
    parser.print_usage()
    sys.exit(1)

print("dwprog starting")

with DebugWire(FTDIInterface(args.baudrate)) as dw:
    args.func(args)

    if not args.stop:
        dw.run()
