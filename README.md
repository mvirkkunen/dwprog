dwprog
======

Program AVR devices with debugWIRE over just the RESET pin. For tiny projects where putting in a
full ISP header is either cumbersome or impossible.

Documentation is somewhat lacking at the moment. Device support is also pretty limited but
extensible.

Prerequisites
-------------

* pylibftdi - for the FTDI interface
* Optionally:
  * pyelftools - for ELF file support
