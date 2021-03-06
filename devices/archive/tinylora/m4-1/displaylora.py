import time
import busio
import digitalio
import board
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa
import displayio
import terminalio
import adafruit_il0373
from adafruit_display_text import label

#
# Display Configuration
#

# Used to ensure the display is free in CircuitPython
displayio.release_displays()

# Define the pins needed for display use
# This pinout is for a Feather M4 and may be different for other boards
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
epd_cs = board.D9
epd_dc = board.D10
midbutton = digitalio.DigitalInOut(board.D12)
rightbutton = digitalio.DigitalInOut(board.D13)

# Set up middle button on display
midbutton.switch_to_input()
midbutton.direction = digitalio.Direction.INPUT
midbutton.pull = digitalio.Pull.UP

# Set up right button on display
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
RED = 0xFF0000

# Create the display object
display = adafruit_il0373.IL0373(
    display_bus,
    width=296,
    height=128,
    rotation=270,
    highlight_color=RED,
)

# Create a display group for our screen objects
g = displayio.Group()

# Change text colors, choose from the following values:
# BLACK, RED, WHITE
FOREGROUND_COLOR = RED
BACKGROUND_COLOR = WHITE

#
# Radio Configuration
#

# RFM9x Breakout Pinouts
cs = digitalio.DigitalInOut(board.D16)
irq = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D11)

# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x26, 0x0C, 0xE6, 0x1B])

# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray(
    [0x09, 0x00, 0x03, 0x71, 0x24, 0xBB, 0x35, 0x40, 0x43, 0xB6, 0xAC, 0x82, 0xD1, 0xF4, 0x0B, 0x9A]
)

# TTN Application Key, 16 Bytess, MSB
app = bytearray(
    [0xA3, 0xD1, 0x8C, 0x80, 0x6E, 0xDC, 0x6E, 0xCD, 0x7E, 0x0B, 0xB7, 0x09, 0xE8, 0x94, 0xAD, 0x3E]
)

ttn_config = TTN(devaddr, nwkey, app, country="US")

lora = TinyLoRa(spi, cs, irq, rst, ttn_config)

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
class Order:
    def __init__(self, name):
        self.num = name
        self.status = "created"
        self.updateStatus()

    def getMsg(self):
        msg = self.num + ": " + self.status
        print(msg)
        return msg

    # send a message over LoRa
    def sendStatus(self):
        msg = self.getMsg()
        msgbytes = bytes(msg, "utf-8")
        data = bytearray(msgbytes)
        print("Sending packet...")
        lora.send_data(data, len(data), lora.frame_counter)
        print("Packet sent!")
        lora.frame_counter += 1

    def updateDisplay(self):
        msg = self.getMsg()
        txt.text = msg

    def updateStatus(self):
        self.sendStatus()
        self.updateDisplay()


order = Order("98765")

display.show(g)
display.refresh()
print("display refreshed")

i = 0
while True:
    while True:
        if not midbutton.value:
            i += 1
            print("button pressed")
            print("i: " + str(i))
            order.status = str(i)
            order.updateStatus()
            break
        else:
            print(display.time_to_refresh)
        time.sleep(0.1)
        
        if display.time_to_refresh <= 0:
            display.show(g)
            display.refresh()
            print("display refreshed")

    time.sleep(3)
