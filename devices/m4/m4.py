import board
import busio
import digitalio
import time
import adafruit_rfm9x
import displayio
import terminalio
import adafruit_il0373
from adafruit_display_text import label

# TODO put this stuff in config file
# https://docs.python.org/3/library/configparser.html
BOARD_ID = "m4-1"

#
# Display Setup
#

# Used to ensure the display is free in CircuitPython
displayio.release_displays()

# Define the pins needed for display use
# This pinout is for a Feather M4 and may be different for other boards
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)  # Uses SCK and MOSI
epd_cs = board.D9
epd_dc = board.D10

# Set up middle button on display
midbutton = digitalio.DigitalInOut(board.D12)
midbutton.switch_to_input()
midbutton.direction = digitalio.Direction.INPUT
midbutton.pull = digitalio.Pull.UP

# Create the displayio connection to the display pins
display_bus = displayio.FourWire(
    spi, command=epd_dc, chip_select=epd_cs, baudrate=1000000
)
time.sleep(1)  # Wait a bit

# Create the display object - the third color is red (0xff0000)
display = adafruit_il0373.IL0373(
    display_bus,
    width=296,
    height=128,
    rotation=270,
    grayscale=True,
    seconds_per_frame=10,
    black_bits_inverted=False,
    color_bits_inverted=False
)

# Create a display group for our screen objects
displaygroup = displayio.Group()

# Set colors
BLACK = 0x000000
WHITE = 0xFFFFFF

FOREGROUND_COLOR = BLACK
BACKGROUND_COLOR = WHITE

# Set a background
background_bitmap = displayio.Bitmap(296, 128, 1)
# Map colors in a palette
palette = displayio.Palette(1)
palette[0] = BACKGROUND_COLOR
# Create a Tilegrid with the background and put in the displayio group
t = displayio.TileGrid(background_bitmap, pixel_shader=palette)
displaygroup.append(t)

txtgroup = displayio.Group(scale=3, x=20, y=40)
displaytxt = label.Label(terminalio.FONT, text="0", color=FOREGROUND_COLOR)
txtgroup.append(displaytxt)  # Add this text to the text group
displaygroup.append(txtgroup)

#
# Radio Setup
#

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.D16)
RESET = digitalio.DigitalInOut(board.D5)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
rfm9x.tx_power = 13 # default

# convert a packet to a parsed message
def toMsg(data):
    msg = {
            "type": data[0],
            "from": data[1],
            "to": data[2],
            "counter": data[3],
            "ordernum": data[4]
            }
    return msg

# convert a packet to a parsed acknowledgement
def toAck(data):
    ack = {
            "type": data[0],
            "from": data[1],
            "to": data[2],
            "counter": data[3],
            }
    return ack

# receive a packet over LoRa, then parse it and send an ack if needed
def receive():
    packet = None
    order = None

    # check for packet rx
    try:
        packet = rfm9x.receive(timeout=1)
    except RuntimeError:
        pass

    if packet is not None:
        print()
        
        try:
            packet_text = str(packet, "utf-8")
        except UnicodeError:
            packet_text = str(packet)
        
        data = packet_text.split(", ")
        print(data)

        try:
            msg = toMsg(data)
        except IndexError:
            # the message is an ack, the # of data items won't match
            # don't bother with acks here (these get handled in sendLora)
            return

        # if a packet isn't an ack and the destination is the pi, send an ack
        # and then send the packet over MQTT (to the application)
        if msg["to"] == BOARD_ID:
            time.sleep(2)
            ack = "ACK, " + BOARD_ID + ", " + msg["from"] + ", " + msg["counter"]
            try:
                rfm9x.send(bytes(ack, "utf-8"), destination=255, node=255)
            except RuntimeError:
                return None
            print("ack sent!")
            time.sleep(1)
            order = Order(msg["ordernum"])
        
    return order


#
# Main code
#


class Message:
    def __init__(self, num, status):
        self.dest = "pi"
        self.body = num + ", " + status

    def __str__(self):
        global counter
        # counter may be useful in confirming acks 

        return "MSG, " + BOARD_ID + ", " + self.dest + ", " + str(counter) + ", " + self.body
    
    def send(self):
        while True:
            global counter
            m = bytes(str(self), "utf-8")
            try:
                rfm9x.send(m, destination=255, node=255)
            except RuntimeError:
                time.sleep(0.1)
                continue
            print(self)
            time.sleep(0.1)
            print("Packet sent!")

            # get acknowledgement
            packet = None
            try:
                packet = rfm9x.receive(timeout=5.0)
            except RuntimeError:
                pass

            # Optionally change the receive timeout from its default of 0.5 seconds:
            # packet = rfm9x.receive(timeout=5.0)
            # If no packet was received during the timeout then None is returned.
            if packet is not None:
                packet_text = str(packet, "ascii")
                data = packet_text.split(", ")
                ack = toAck(data)

                # data = [type (ack or msg), from, to, counter]
                if ack["type"] == "ACK" and ack["to"] == BOARD_ID and ack["counter"] == str(counter):
                    print("ack received!")
                    counter += 1
                    return # ack received, exit the function
                    
            print("no ack received! trying again") # no ack, loop again

class Order:
    def __init__(self, name):
        self.num = name
        self.statusArr = ["created", "cut", "stripped", "soldered", "completed"]
        self.statusCounter = 0
        self.status = self.statusArr[self.statusCounter]
        self.sendStatus()

    def updateDisplay(self):
        displaytxt.text = self.num + " " + self.status
        
    def updateStatus(self):
        self.statusCounter += 1
        self.status = self.statusArr[self.statusCounter]
        self.sendStatus()

    def sendStatus(self):
        msg = Message(self.num, self.status)
        msg.send()
        self.updateDisplay()

def eventloop():
    order = None
    changed = False
    while True:
        time.sleep(0.1)
        o = receive()

        # if we received an order number from the server ...
        if o is not None:
            changed = True
            # change the order that we're managing
            order = o
            continue
            
        # if the button is pressed ...
        if not midbutton.value and order is not None:
            print()
            changed = True
            # send an order status update to the server
            order.updateStatus()
            continue

        if changed and display.time_to_refresh <= 0:
            print()
            display.show(displaygroup)
            # display.time_to_refresh = 10
            # print(display.time_to_refresh)
            display.refresh()
            print("time to refresh:", display.time_to_refresh)
            print("display refreshed")
            changed = False
            continue

        print(".", end = '')

def main():
    global counter
    counter = 0
    eventloop()

main()
