# USBKeyboard.py
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
import os

class USBKeyboardInterface(USBInterface):
    name = "USB keyboard interface"

    hid_descriptor = b'\x09\x21\x10\x01\x00\x01\x22\x2b\x00'
    report_descriptor = b'\x05\x01\x09\x06\xA1\x01\x05\x07\x19\xE0\x29\xE7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x19\x00\x29\x65\x15\x00\x25\x65\x75\x08\x95\x06\x81\x00\xC0'

    def __init__(self, verbose=0, text=None):
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

        self.devices = map(InputDevice, ('/dev/input/event1', '/dev/input/event0'))
        self.devices = {dev.fd: dev for dev in self.devices}
        for dev in self.devices.values(): print(dev)
        self.current_keys = [0]

        #clear all the LEDs
        for ledpath in os.listdir('/sys/class/leds/'):
            contents = open('/sys/class/leds/' + ledpath + '/trigger', 'w')
            contents.write('none\n');
            contents.close()
            contents = open('/sys/class/leds/' + ledpath + '/brightness', 'w')
            contents.write('0\n')
            contents.close()

        #TODO
        #self.button1_rate_led = open('/sys/class/leds/switch:green:led_A/brightness', 'w')
        self.button1_rate_led = open('/sys/class/leds/beaglebone:green:usr3/brightness', 'w')
        self.button1_status_led = open('/sys/class/leds/beaglebone:green:usr2/brightness', 'w')
        self.button2_status_led = open('/sys/class/leds/beaglebone:green:mmc0/brightness', 'w')
        #TODO
        #self.button2_rate_led = open('/sys/class/leds/switch:green:led_B/brightness', 'w')
        self.button2_rate_led = open('/sys/class/leds/beaglebone:green:heartbeat/brightness', 'w')

    def handle_buffer_available(self):
        
        hackBrakes = 0
        hackTimer = 0
        hackGas = 0
        
        r, w, x = select(self.devices, [], [])
        for fd in r:
            for event in self.devices[fd].read():
                if event.type != ecodes.EV_KEY:
                    continue
                if event.code == 3 and event.value != 1:
                    print("TODO: do a reset of the rate limiter")
                    hackBrakes = 0
                    hackGas = 0
                    hackTimer = 0
                    continue 
                    
                if event.code == 17 and event.value == 1: #increase hackTimer by 1 every 1 seconds
                        hackTimer += 1
                        
                if event.code != 1 and event.code != 2:
                    continue
                if event.code == 1 and event.value == 1: #brakes is pressed
                    self.brakes_pressed = 1
                if event.code == 1 and event.value == 0: #no brakes pressed
                    self.brakes_pressed = 0
                if event.code == 2 and event.value == 1: #throttle is pressed
                    self.gas_pressed == 1
                if event.code == 2 and event.value == 0: #no throttle pressed
                    self.gas_pressed == 0

                if hackTimer >= 120 : #reset timer and allow button presses after 120
                    hackTimer = 0
                    hackGas = 4
                    hackBrakes = 4
        
                if self.brakes_pressed == 1 and hackBrakes > 0: #if brakes pressed and allowed to be so
                    if 0 in self.current_keys:
                        self.current_keys.remove(0)
                    if not 0x4 in self.current_keys:
                        self.current_keys.append(0x4)
                        self.button1_status_led.write('255\n')
                        self.button1_status_led.flush()
                    if event.code == 17 and event.value == 1:
                        hackBrakes -= 1
        
                if self.brakes_pressed == 0: 
                    if 0x4 in self.current_keys:
                        self.current_keys.remove(0x4)
                        self.button1_status_led.write('0\n')
                        self.button1_status_led.flush()
                    if not self.current_keys:
                        self.current_keys = [0]
        
                if self.gas_pressed == 1 and hackGas > 0: #if gas pressed and allowed to be so
                    if 0 in self.current_keys:
                        self.current_keys.remove(0)
                    if not 0x14 in self.current_keys:
                        self.current_keys.append(0x14)
                        self.button2_status_led.write('255\n')
                        self.button2_status_led.flush()
                if event.code == 17 and event.value == 1:
                        hackGas -= 1
        
                if self.gas_pressed == 0:
                    if 0x14 in self.current_keys:
                        self.current_keys.remove(0x14)
                        self.button2_status_led.write('0\n')
                        self.button2_status_led.flush()
                    if not self.current_keys:
                        self.current_keys = [0]
"""            
                if event.value == 1: #key pressed
                    if 0 in self.current_keys:
                        self.current_keys.remove(0)
                    if event.code == 1 and hackBrakes > 0: #only disable brakes when hackBrake is not 0
                        if not 0x4 in self.current_keys:
                            self.current_keys.append(0x4)
                            self.button1_status_led.write('255\n')
                            self.button1_status_led.flush()
                            if event.code == 17: #decrease hackBrakes by 1 for every second until reaches 0
                                if event.value == 1:
                                    hackBrakes -= 1
                    elif event.code == 2 and hackGas > 0: #only send throttle when hackGas is not 0
                        if not 0x14 in self.current_keys:
                            self.current_keys.append(0x14)
                            self.button2_status_led.write('255\n')
                            self.button2_status_led.flush()
                            if event.code == 17:   #decrease hackGas by 1 for every second until reaches 0
                                if event.value == 1:
                                    hackGas -= 1
                
                else: #key released
                    if event.code == 1:
                        if 0x4 in self.current_keys:
                            self.current_keys.remove(0x4)
                            self.button1_status_led.write('0\n')
                            self.button1_status_led.flush()
                    elif event.code == 2:
                        if 0x14 in self.current_keys:
                            self.current_keys.remove(0x14)
                            self.button2_status_led.write('0\n')
                            self.button2_status_led.flush()
                    if not self.current_keys:
                        self.current_keys = [0]
"""
                self.endpoint.send(bytes([0,0] + self.current_keys + [0]*(6-len(self.current_keys)) ))

    def type_letter(self, keycode, modifiers=0):
        data = bytes([ modifiers, 0, keycode ])

        if self.verbose > 2:
            print(self.name, "sending keypress 0x%02x" % keycode)

        self.endpoint.send(data)


class USBKeyboardDevice(USBDevice):
    name = "USB keyboard device"

    def __init__(self, maxusb_app, verbose=0, text=None):
        config = USBConfiguration(
                1,                                          # index
                "Emulated Keyboard",    # string desc
                [ USBKeyboardInterface(text=text) ]         # interfaces
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

