#!/usr/bin/env python3
#
# usbproxy-fd-keyboard.py

from USBProxyApp import USBProxyApp
from UDPKeyboard import UDPKeyboardDevice
import sys

u = USBProxyApp(verbose=0)
d = UDPKeyboardDevice(u, verbose=0)

d.connect()

try:
    d.run()
# SIGINT raises KeyboardInterrupt
except KeyboardInterrupt:
    d.disconnect()
