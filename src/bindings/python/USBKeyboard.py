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

        self.devices = map(InputDevice, ('/dev/input/event1', '/dev/input/event0','/dev/input/event2))
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

        self.brakes_pressed = 0
        self.gas_pressed = 0
        self.reset_limiter()

        self.last_send_was_nil = 0

    def reset_limiter(self):
        self.hackBrakes = 5 #5 seconds of brakes
        self.hackGas = 5 #5 seconds of gas
        self.hackTimer = 0

    def update_rate_limiter_leds(self):
        if self.hackBrakes > 0:
            self.button1_rate_led.write('255\n')
        else:
            self.button1_rate_led.write('0\n')
        self.button1_rate_led.flush()

        if self.hackGas > 0:
            self.button2_rate_led.write('255\n')
        else:
            self.button2_rate_led.write('0\n')
        self.button2_rate_led.flush()

    def handle_buffer_available(self):
        r, w, x = select(self.devices, [], [])
        for fd in r:
            for event in self.devices[fd].read():
                if event.type != ecodes.EV_KEY:
                    continue

                if event.code == 3 and event.value != 1:
                    print("reset of the rate limiter")
                    self.reset_limiter()
                    self.update_rate_limiter_leds()

                    if self.brakes_pressed == 1 or self.gas_pressed == 1:
                        self.rate_limit()
                        return #always return after writing a packet
                    continue

                if event.code == 17 and event.value == 1: #17 co-opted for timer events in our select() loop
                    self.hackTimer += 1 #increase hackTimer by 1 every 1 seconds

                    if self.hackTimer >= 120 : #reset timer and allow button presses after 120
                        self.reset_limiter()

                    #TODO: either poll more frequently or measure time elapsed between code 1 and 2 keypresses to better measure the use of the buttons
                    if self.gas_pressed == 1:
                        self.hackGas -= 1
                    if self.brakes_pressed == 1:
                        self.hackBrakes -= 1

                    self.update_rate_limiter_leds()

                    if (
                            (self.hackBrakes == 0 and self.brakes_pressed == 1)
                            or (self.hackGas == 0 and self.gas_pressed == 1)
                            or (self.hackTimer == 0 and (self.brakes_pressed == 1 or self.gas_pressed == 1))
                        ):
                        #handle edge-transitions
                        self.rate_limit()
                        return #always return after writing a packet
                    continue

                if event.code != 1 and event.code != 2:
                    continue

                if event.code == 1 or event.code == 273:
                    self.brakes_pressed = event.value
                    #TODO collect time spent with brakes_pressed == 1; otherwise short keypresses aren't tracked in time event above
                    if self.brakes_pressed == 1:
                        self.button1_status_led.write('255\n')
                    else:
                        self.button1_status_led.write('0\n')
                    self.button1_status_led.flush()

                if event.code == 2 or event.code == 272:
                    self.gas_pressed = event.value
                    #TODO collect time spent with gas_pressed == 1 ; other short keypresses aren't tracked int timer events above
                    if self.gas_pressed == 1:
                        self.button2_status_led.write('255\n')
                    else:
                        self.button2_status_led.write('0\n')
                    self.button2_status_led.flush()
                
                self.rate_limit()
                return #always return after writing a packet

    def rate_limit(self):
        send_keys = []
        if self.brakes_pressed == 1 and self.hackBrakes > 0: #if brakes pressed and allowed to be so
            send_keys.append(0x4)

        if self.gas_pressed == 1 and self.hackGas > 0: #if gas pressed and allowed to be so
            send_keys.append(0x14)

        if not send_keys:
            if self.last_send_was_nil == 1:
                return
            self.last_send_was_nil = 1
        else:
            self.last_send_was_nil = 0

        self.endpoint.send(bytes([0,0] + send_keys + [0]*(6-len(send_keys)) ))

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

