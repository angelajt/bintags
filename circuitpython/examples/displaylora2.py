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
spi = board.SPI()  # Uses SCK and MOSI
epd_cs = board.D9
epd_dc = board.D10
epd_reset = board.D5
epd_busy = board.D6

# Create the displayio connection to the display pins
display_bus = displayio.FourWire(
    spi, command=epd_dc, chip_select=epd_cs, reset=epd_reset, baudrate=1000000
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
    busy_pin=epd_busy,
    highlight_color=RED,
)

# Create a display group for our screen objects
g = displayio.Group()


# Change text colors, choose from the following values:
# BLACK, RED, WHITE

FOREGROUND_COLOR = RED
BACKGROUND_COLOR = WHITE

# Board LED
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# RFM9x Breakout Pinouts
cs = digitalio.DigitalInOut(board.D16)
irq = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D11)

# Feather M0 RFM9x Pinouts
# cs = digitalio.DigitalInOut(board.RFM9X_CS)
# irq = digitalio.DigitalInOut(board.RFM9X_D0)
# rst = digitalio.DigitalInOut(board.RFM9X_RST)

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


while True:
    data = bytearray(b"\x68\x69\x20\x68\x65\x6c\x6c\x6f")
    print("Sending packet...")
    lora.send_data(data, len(data), lora.frame_counter)
    print("Packet sent!")
    lora.frame_counter += 1

    led.value = True

    # Set a background
    background_bitmap = displayio.Bitmap(296, 128, 1)
    # Map colors in a palette
    palette = displayio.Palette(1)
    palette[0] = BACKGROUND_COLOR

    # Create a Tilegrid with the background and put in the displayio group
    t = displayio.TileGrid(background_bitmap, pixel_shader=palette)
    g.append(t)

    # Draw simple text using the built-in font into a displayio group
    text_group = displayio.Group(scale=2, x=20, y=40)
    text = "hi"
    text_area = label.Label(terminalio.FONT, text=text, color=FOREGROUND_COLOR)
    text_group.append(text_area)  # Add this text to the text group
    g.append(text_group)
    display.show(g)
    
    display.refresh()
    print("display refreshed")

    time.sleep(5)
    led.value = False
    time.sleep(175)
