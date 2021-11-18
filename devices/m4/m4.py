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

# Set up right button on display
rightbutton = digitalio.DigitalInOut(board.D13)
rightbutton.switch_to_input()
rightbutton.direction = digitalio.Direction.INPUT
rightbutton.pull = digitalio.Pull.UP

# Create the displayio connection to the display pins
display_bus = displayio.FourWire(
    spi, command=epd_dc, chip_select=epd_cs, baudrate=1000000
)
time.sleep(1)  # Wait a bit

# Set colors
BLACK = 0x000000
WHITE = 0xFFFFFF
# RED = 0xFF0000

# Create the display object - the third color is red (0xff0000)
display = adafruit_il0373.IL0373(
    display_bus,
    width=296,
    height=128,
    rotation=270,
    # highlight_color=0xFF0000,
    grayscale=True,
    seconds_per_frame=10,
    black_bits_inverted=False,
    color_bits_inverted=False
)

# Create a display group for our screen objects
g = displayio.Group()

# Change text colors, choose from the following values:
# BLACK, RED, WHITE

FOREGROUND_COLOR = BLACK
BACKGROUND_COLOR = WHITE

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

#
# Main code
#

# Set a background
background_bitmap = displayio.Bitmap(296, 128, 1)
# Map colors in a palette
palette = displayio.Palette(1)
palette[0] = BACKGROUND_COLOR
# Create a Tilegrid with the background and put in the displayio group
t = displayio.TileGrid(background_bitmap, pixel_shader=palette)
g.append(t)

txt_group = displayio.Group(scale=3, x=20, y=40)
txt = label.Label(terminalio.FONT, text="0", color=FOREGROUND_COLOR)
txt_group.append(txt)  # Add this text to the text group
g.append(txt_group)

# hold and display/send information about an order
class Message:
    def __init__(self, num, status):
        self.id = BOARD_ID
        self.dest = "pi"
        self.counter = 0
        self.body = num + ", " + status

    def __str__(self):
        return "MSG, " + self.id + ", " + self.dest + ", " + str(self.counter) + ", " + self.body
    
    def send(self):
        while True:
            print("Sending packet...")
            rfm9x.send(bytes(str(self), "utf-8"), destination=255, node=255)
            print(self)
            time.sleep(0.1)
            print("Packet sent!")

            # get acknowledgement
            packet = rfm9x.receive(timeout=5.0)
            # Optionally change the receive timeout from its default of 0.5 seconds:
            # packet = rfm9x.receive(timeout=5.0)
            # If no packet was received during the timeout then None is returned.
            if packet is not None:
                packet_text = str(packet, "ascii")
                print("received " + packet_text)
                data = packet_text.split(", ")
                # data = [type (ack or msg), from, to, counter]
                if data[0] == "ACK" and data[2] == BOARD_ID and data[3] == str(self.counter):
                    print("Received acknowledgement!")
                    self.counter += 1
                    return
                    
            print("Didn't receive acknowledgement! Sending again...")


class Order:
    def __init__(self, name):
        self.num = name
        self.statusArr = ["created", "cut", "stripped", "soldered", "completed"]
        self.counter = 0
        self.status = self.statusArr[self.counter]
        # self.sendStatus()
        self.sendStatus()

    def updateDisplay(self):
        txt.text = self.num + " " + self.status
        
    def updateStatus(self):
        self.counter += 1
        self.status = self.statusArr[self.counter]
        self.sendStatus()

    def sendStatus(self):
        msg = Message(self.num, self.status)
        msg.send()
        self.updateDisplay()


order = Order("98765")
order.sendStatus()

display.show(g)
display.refresh()
print("display refreshed")

i = 0
while True:
    while True:
        try:
            packet = rfm9x.receive(timeout=1.0)
        except RuntimeError:
            print("I hit that weird runtime error. Check if this affected anything.")

        # Optionally change the receive timeout from its default of 0.5 seconds:
        # packet = rfm9x.receive(timeout=5.0)
        # If no packet was received during the timeout then None is returned.
        packet_text = ""
        if packet is None:
            print("Received nothing! Listening again...")
        else:
            try:
                packet_text = str(packet, "ascii")
            except UnicodeError:
                packet_text = str(packet)

            data = packet_text.split(", ")
            print(data)

            # data = [type (ack or msg), from, to, counter, (ordernum)]
            if data[0] == "MSG" and data[2] == BOARD_ID:
                print("uhuhh")
                # send acknowledgement
                time.sleep(2)
                ack = "ACK, " + data[2] + ", " + data[1] + ", " + data[3]
                print(ack)
                rfm9x.send(bytes(ack, "utf-8"), destination=255, node=255) 
                time.sleep(0.1)

                order = Order(data[4]) # generate a new order from message
            packet = None
        if not midbutton.value:
            order.updateStatus()
            break
        else:
            print(display.time_to_refresh)

        if display.time_to_refresh <= 0:
            display.show(g)
            display.refresh()
            print("display refreshed")

        time.sleep(0.5)

    time.sleep(3)
