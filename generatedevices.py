#!/usr/bin/env python3

# converts Atmel device files into devices.py

from xml.etree import ElementTree
from fnmatch import fnmatch
from zipfile import ZipFile
import sys

spmcsr_bits = {
    0x01: ["SPMEN", "SELFPRGEN"],
    0x02: ["PGERS"],
    0x04: ["PGWRT"],
}

def process_doc(doc):
    device = doc.find("devices/device")
    name = device.attrib["name"]

    jtagid = device.find("property-groups/property-group[@name='SIGNATURES']/property[@name='JTAGID']")
    flash = device.find("address-spaces/address-space[@name='prog']/memory-segment[@name='FLASH']")
    cpu = doc.find("modules/module[@name='CPU']")
    dwdr = doc.find(".//register[@name='DWDR']")
    spmcsr = doc.find(".//register[@name='SPMCSR']")
    if spmcsr is None:
        spmcsr = doc.find(".//register[@name='SPMCR']")

    errors = []

    if jtagid is None:
        errors.append("no JTAGID")

    if flash is None:
        errors.append("no flash segment")

    if spmcsr is None:
        errors.append("no SPMCSR register")
    else:
        for bmask, bname in spmcsr_bits.items():
            field = next(
                (f for f in spmcsr.findall("bitfield") if int(f.attrib["mask"], 16) == bmask),
                None)

            if field is None:
                errors.append("missing " + str(bname) + " bit")
            elif field.attrib["name"] not in bname:
                errors.append(str(bname) + " field has a weird name")

    if len(errors):
        print("Unsupported device: {} ({})".format(name, ", ".join(errors)), file=sys.stderr)
        return

    devid = name.lower()
    signature = int(jtagid.attrib["value"], 16)
    flash_size = int(flash.attrib["size"], 16)
    flash_pagesize = int(flash.attrib["pagesize"], 16)
    reg_dwdr = (int(dwdr.attrib["offset"], 16) - 0x20) if dwdr is not None else None
    reg_spmcsr = int(spmcsr.attrib["offset"], 16) - 0x20

    print("    Device(devid=\"{}\", name=\"{}\", signature=0x{:x}, flash_size=0x{:x}, flash_pagesize=0x{:x}, reg_dwdr={}, reg_spmcsr=0x{:x}),"
        .format(
            devid,
            name,
            signature,
            flash_size,
            flash_pagesize,
            "0x{:x}".format(reg_dwdr) if reg_dwdr else "None",
            reg_spmcsr))

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