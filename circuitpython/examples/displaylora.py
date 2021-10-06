import board
import busio
import digitalio
import time
import adafruit_rfm9x
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
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)  # Uses SCK and MOSI
epd_cs = board.D9
epd_dc = board.D10

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
    highlight_color=0xFF0000,
)

# Create a display group for our screen objects
g = displayio.Group()

# Set colors
BLACK = 0x000000
WHITE = 0xFFFFFF
RED = 0xFF0000

# Change text colors, choose from the following values:
# BLACK, RED, WHITE

FOREGROUND_COLOR = RED
BACKGROUND_COLOR = WHITE

#
# Radio Setup
#

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.D16)
RESET = digitalio.DigitalInOut(board.D11)
# Or uncomment and instead use these if using a Feather M0 RFM9x board and the appropriate
# CircuitPython build:
# CS = digitalio.DigitalInOut(board.RFM9X_CS)
# RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Define the onboard LED
LED = digitalio.DigitalInOut(board.D13)
LED.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
# spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Note that the radio is configured in LoRa mode so you can't control sync
# word, encryption, frequency deviation, or other settings!

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 5

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
text = "98765"
text_area = label.Label(terminalio.FONT, text=text, color=FOREGROUND_COLOR)
text_group.append(text_area)  # Add this text to the text group
g.append(text_group)


# Place the display group on the screen
display.show(g)

# Refresh the display to have it actually show the image
# NOTE: Do not refresh eInk displays sooner than 180 seconds
display.refresh()
print("refreshed")

while True:
    rfm9x.send(bytes("Hello Steve!\r\n", "utf-8"), destination=255, node=255)
    print("Sent Hello World message!")
    packet = rfm9x.receive(timeout=display.time_to_refresh)
    # Optionally change the receive timeout from its default of 0.5 seconds:
    # packet = rfm9x.receive(timeout=5.0)
    # If no packet was received during the timeout then None is returned.
    if packet is None:
        # Packet has not been received
        LED.value = False
        print("Received nothing! Listening again...")
    else:
        # Received a packet!
        LED.value = True
        # Print out the raw bytes of the packet:
        print("Received (raw bytes): {0}".format(packet))
        # And decode to ASCII text and print it too.  Note that you always
        # receive raw bytes and need to convert to a text format like ASCII
        # if you intend to do string processing on your data.  Make sure the
        # sending side is sending ASCII data before you try to decode!
        packet_text = str(packet, "ascii")
        print("Received (ASCII): {0}".format(packet_text))
        # Also read the RSSI (signal strength) of the last received message and
        # print it.
        rssi = rfm9x.last_rssi
        print("Received signal strength: {0} dB".format(rssi))
    # time.sleep(180)
