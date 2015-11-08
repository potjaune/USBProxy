# UDPKeyboard.py
#
# Contains class definitions to implement a USB keyboard.

from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *
from keymap import get_keycode
from evdev import InputDevice, categorize, ecodes
from select import select
from socket import *
import os

class UDPKeyboardInterface(USBInterface):
    name = "USB keyboard interface"

    hid_descriptor = b'\x09\x21\x10\x01\x00\x01\x22\x2b\x00'
    report_descriptor = b'\x05\x01\x09\x06\xA1\x01\x05\x07\x19\xE0\x29\xE7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x19\x00\x29\x65\x15\x00\x25\x65\x75\x08\x95\x06\x81\x00\xC0'

    def __init__(self, verbose=0):
        descriptors = { 
                USB.desc_type_hid    : self.hid_descriptor,
                USB.desc_type_report : self.report_descriptor
        }

        self.endpoint = USBEndpoint(
                3,          # endpoint number
                USBEndpoint.direction_in,
                USBEndpoint.transfer_type_interrupt,
                USBEndpoint.sync_type_none,
                USBEndpoint.usage_type_data,
                16384,      # max packet size
                10,         # polling interval, see USB 2.0 spec Table 9-13
                self.handle_buffer_available    # handler function
        )

        # TODO: un-hardcode string index (last arg before "verbose")
        USBInterface.__init__(
                self,
                0,          # interface number
                0,          # alternate setting
                3,          # interface class
                0,          # subclass
                0,          # protocol
                0,          # string index
                verbose,
                [ self.endpoint ],
                descriptors
        )

        #TODO: change to socket open
        self.udp = socket(AF_INET, SOCK_DGRAM)
        self.udp.bind(('',32008))
        self.devices =[self.udp]

        self.last_send_was_nil = 0

    def handle_buffer_available(self):
        send_keys = []
        r, w, x = select(self.devices, [], [])
        for fd in r:
            if fd == self.udp:
                send_keys = list(self.udp.recv(6))
            if not send_keys:
                if self.last_send_was_nil == 1:
                    return
                self.last_send_was_nil = 1
            else:
                self.last_send_was_nil = 0

            self.endpoint.send(bytes([0,0] + send_keys + [0]*(6-len(send_keys)) ))
            #always return after send
            return

class UDPKeyboardDevice(USBDevice):
    name = "USB keyboard device"

    def __init__(self, maxusb_app, verbose=0):
        config = USBConfiguration(
                1,                                          # index
                "Emulated Keyboard",    # string desc
                [ UDPKeyboardInterface() ]         # interfaces
        )

        USBDevice.__init__(
                self,
                maxusb_app,
                0,                      # device class
                0,                      # device subclass
                0,                      # protocol release number
                64,                     # max packet size for endpoint 0
                0x610b,                 # vendor id
                0x4653,                 # product id
                0x3412,                 # device revision
                "Move along",                # manufacturer string
                "This is not the USB device you're looking for",   # product string
                "00001",             # serial number string
                [ config ],
                verbose=verbose
        )

