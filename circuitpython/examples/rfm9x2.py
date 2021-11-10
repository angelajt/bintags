"""
bintags server-side prototype

derived from: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
"""
# Import Python System Libraries
import time
# Import Blinka Libraries
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import the SSD1306 module.
import adafruit_ssd1306
# Import RFM9x
import adafruit_rfm9x

# Button A
btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

# Button B
btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

# Button C
btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 23
prev_packet = None

counter = 0
while True:
    packet = None
    # draw a box to clear the image
    display.fill(0)
    display.text('RasPi LoRa', 35, 0, 1)

    # check for packet rx
    packet = rfm9x.receive(timeout=5)
    if packet is None:
        display.show()
        display.text('- Waiting for PKT -', 15, 20, 1)
    else:
        # Display the packet text and rssi
        display.fill(0)
        prev_packet = packet
        packet_text = str(prev_packet, "utf-8")
        data = packet_text.split(", ")
        print(data)
        if data[0] == "MSG" and data[2] == "pi":
            time.sleep(2)
            ack = "ACK, " + data[2] + ", " + data[1] + ", " + data[3]
            rfm9x.send(bytes(ack, "utf-8"), destination=255, node=255)
            print("ack sent!")
            time.sleep(1)

            display.text('RX: ', 0, 0, 1)
            display.text(packet_text, 25, 0, 1)

    if not btnA.value:
        while True:
            # Send Button A
            display.fill(0)
            button_a_data = bytes("MSG, pi, m4-1, " + str(counter) + ", 12345","utf-8")
            rfm9x.send(button_a_data)
            display.text('Sent Button A!', 25, 15, 1)
            time.sleep(0.1)
            packet = rfm9x.receive(timeout=10.0)
            if packet is not None:
                packet_text = str(packet, "ascii")
                data = packet_text.split(", ")
                if data[0] == "ACK" and data[2] == "pi" and data[3] == str(counter):
                    print("ack received!")
                    counter += 1
                    break
            print("no ack received! trying again")
    elif not btnB.value:
        # Send Button B
        display.fill(0)
        button_b_data = bytes("22222","utf-8")
        rfm9x.send(button_b_data)
        display.text('Sent Button B!', 25, 15, 1)
    elif not btnC.value:
        # Send Button C
        display.fill(0)
        button_c_data = bytes("99999","utf-8")
        rfm9x.send(button_c_data)
        display.text('Sent Button C!', 25, 15, 1)


    display.show()
    time.sleep(0.1)
