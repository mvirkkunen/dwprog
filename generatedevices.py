#!/usr/bin/env python3

# converts Atmel device files into devices.py

from xml.etree import ElementTree
from fnmatch import fnmatch
from zipfile import ZipFile
import sys

def process_doc(doc):
    device = doc.find("devices/device")
    name = device.attrib["name"]

    flash = device.find("address-spaces/address-space[@name='prog']/memory-segment[@name='FLASH']")
    cpu = doc.find("modules/module[@name='CPU']")
    dwdr = doc.find(".//register[@name='DWDR']")
    spmcsr = doc.find(".//register[@name='SPMCSR']")

    errors = []

    if flash is None:
        errors.append("no flash segment")

    if dwdr is None:
        errors.append("no DWDR register")

    if spmcsr is None:
        errors.append("no SPMCSR register")

    if len(errors):
        print("Unsupported device: {} ({})".format(name, ", ".join(errors)), file=sys.stderr)
        return

    devid = name.lower()
    signature = int(
        device
            .find("property-groups/property-group[@name='SIGNATURES']/property[@name='JTAGID']")
            .attrib["value"],
        16)
    flash_size = int(flash.attrib["size"], 16)
    flash_pagesize = int(flash.attrib["pagesize"], 16)
    reg_dwdr = int(dwdr.attrib["offset"], 16) - 0x20
    reg_spmcsr = int(spmcsr.attrib["offset"], 16) - 0x20

    print("    Device(devid=\"{}\", name=\"{}\", signature=0x{:x}, flash_size=0x{:x}, flash_pagesize=0x{:x}, reg_dwdr=0x{:x}, reg_spmcsr=0x{:x}),"
        .format(devid, name, signature, flash_size, flash_pagesize, reg_dwdr, reg_spmcsr))

if len(sys.argv) < 2:
    print("USAGE: generatedevices.py *.atpack", file=sys.stderr)
    sys.exit(1)

print("""# Generated with generatedevices.py

class Device:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

devices = [""")

for packfile in sys.argv[1:]:
    with ZipFile(packfile) as zfile:
        for name in (n for n in zfile.namelist() if fnmatch(n, "*.atdf")):
            with zfile.open(name) as dfile:
                doc = ElementTree.fromstring(dfile.read())

                process_doc(doc)

print("]")