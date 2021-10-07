# super secret api key
# ***REMOVED***

# second one mqtt
# ***REMOVED***

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

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
# Display Setup
#

# Used to ensure the display is free in CircuitPython
displayio.release_displays()

# Define the pins needed for display use
# This pinout is for a Feather M4 and may be different for other boards
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
epd_cs = board.D9
epd_dc = board.D10
leftbutton = digitalio.DigitalInOut(board.D12)
rightbutton = digitalio.DigitalInOut(board.D13)
leftbutton.switch_to_input()
rightbutton.switch_to_input()
leftbutton.direction = digitalio.Direction.INPUT
leftbutton.pull = digitalio.Pull.UP

# Create the displayio connection to the display pins
display_bus = displayio.FourWire(
    spi, command=epd_dc, chip_select=epd_cs, baudrate=1000000
)
time.sleep(1)  # Wait a bit

# Set colors
BLACK = 0x000000
WHITE = 0xFFFFFF
RED = 0xFF0000

# Create the display object - the third color is red (0xff0000)
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
# Radio Setup
#

# RFM9x Breakout Pinouts
cs = digitalio.DigitalInOut(board.D16)
irq = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D11)

# Feather M0 RFM9x Pinouts
# cs = digitalio.DigitalInOut(board.RFM9X_CS)
# irq = digitalio.DigitalInOut(board.RFM9X_D0)
# rst = digitalio.DigitalInOut(board.RFM9X_RST)

# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x00, 0x7B, 0x60, 0xA7])

# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray(
    [0xFA, 0x3F, 0xF8, 0x86, 0x5F, 0xA6, 0xFF, 0xF8, 0x01, 0xD5, 0xAC, 0x0C, 0x0A, 0xBC, 0xF3, 0xDD]
)

# TTN Application Key, 16 Bytess, MSB
app = bytearray(
    [0xD0, 0x25, 0x40, 0xB5, 0xB9, 0x55, 0x8B, 0xC8, 0x7C, 0x21, 0xE3, 0xE1, 0x13, 0xFC, 0x0B, 0x3E]
)

ttn_config = TTN(devaddr, nwkey, app, country="US")

lora = TinyLoRa(spi, cs, irq, rst, ttn_config)


ordernum = "12345" 

# Set a background
background_bitmap = displayio.Bitmap(296, 128, 1)
# Map colors in a palette
palette = displayio.Palette(1)
palette[0] = BACKGROUND_COLOR
# Create a Tilegrid with the background and put in the displayio group
t = displayio.TileGrid(background_bitmap, pixel_shader=palette)
g.append(t)

# Draw simple text using the built-in font into a displayio group
text_group = displayio.Group(scale=3, x=20, y=40)
text = ordernum
text_area = label.Label(terminalio.FONT, text=text, color=FOREGROUND_COLOR)
text_group.append(text_area)  # Add this text to the text group
g.append(text_group)
display.show(g)

display.refresh()
print("display refreshed")

def updateStatus(status):
    msg = "order " + ordernum + ": " + status
    msgbytes = bytes(msg, "utf-8")
    data = bytearray(msgbytes)
    print("Sending packet...")
    lora.send_data(data, len(data), lora.frame_counter)
    print("Packet sent!")
    lora.frame_counter += 1

i = 0
while True:
    while True:
        print("uwu")
        if not leftbutton.value:
            print("button pressed")
            updateStatus(str(i))
            i += 1
            break
        else:
            print("noooo")
        time.sleep(0.1)

    time.sleep(3)
