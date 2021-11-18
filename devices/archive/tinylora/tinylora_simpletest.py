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
    led.value = True
    lora.frame_counter += 1
    time.sleep(5)
    led.value = False
