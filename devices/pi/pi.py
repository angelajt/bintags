"""
bintags server-side prototype

derived from: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
"""
import sys
import time
import busio
import digitalio import DigitalInOut
import board
import adafruit_ssd1306
import adafruit_rfm9x
import paho.mqtt.client as mqtt

# TODO put this stuff in config file
# https://docs.python.org/3/library/configparser.html
BOARD_ID = "pi"

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

#
# LoRa Setup
#

class Radio:
    counter = 0
    sendQueue = []

    def __init__(self):
        # Configure LoRa Radio
        CS = DigitalInOut(board.CE1)
        RESET = DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
        rfm9x.tx_power = 23

    # receive a packet over LoRa and return it
    def receive(self, t):
        packet = None
        try:
            # acks probably need longer timeouts, so make timeout flexible
            packet = self.rfm9x.receive(timeout=t)
        # weird unexplained RuntimeError that we get sometimes (just ignore it and try again)
        except RuntimeError:
            time.sleep(0.1)
            pass
        return packet
    
    def send(self, msg):
        m = bytes(str(msg), "utf-8")
        try:
            self.rfm9x.send(m, destination=255, node=255)
        # weird unexplained RuntimeError that we get sometimes (just ignore it and try again)
        except RuntimeError: 
            time.sleep(0.1)
            pass

    # receive an order over LoRa
    def receiveOrder(self):
        order = None
        packet = self.receive(1)

        if packet is not None:
            msg = Message.parse(packet)
            if msg is None: # garbage message
                return None
            print() # make a newline for easy reading in the serial console
            
            if msg.isMsg(): # ensure the message is a valid order message to this board
                self.sendAck(msg)
                print("ack sent!")
                order = Order(msg.ordernum)
        
        return order
    
    # send a given message over LoRa, checking for an acknowledgement
    def sendMsg(self, msg):
        self.counter += 1 # add to the counter
        msg.counter = self.counter
        gotAck = False
        # send a message, looping over and over until we get an ack
        while not gotAck:

            self.send(msg)
            print("sending:", msg)
            
            time.sleep(0.1)
            print("message sent!")

            gotAck = self.receiveAck()

            if not gotAck:
                print("no ack received! trying again") # no ack, loop again

    # receive an acknowledgement over LoRa and return it
    def receiveAck(self):
        gotAck = False
        packet = self.receive(5)

        if packet is not None:
            msg = Message.parse(packet)
            if msg is None: # garbage message
                return
            if msg.isAck(self.counter):
                gotAck = True
        
        return gotAck
    
    def sendAck(self, msg):
        time.sleep(1)
        ack = Message(type = "ACK", ordernum = msg.ordernum, status = msg.status, counter = msg.counter)
        self.send(ack)
        return

# convert a packet to a parsed message
def toMsg(data):
    msg = {
            "type": data[0],
            "from": data[1],
            "to": data[2],
            "counter": data[3],
            "ordernum": data[4],
            "content": data[5]
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
def receiveLora():
    # check for packet rx
    packet = rfm9x.receive(timeout=5)
    print("finished receive", packet)

    if packet is not None:
        display.fill(0)

        try:
            packet_text = str(packet, "utf-8")
        except UnicodeDecodeError:
            return
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
        if msg["to"] == "pi":
            time.sleep(2)
            ack = "ACK, " + "pi" + ", " + msg["from"] + ", " + msg["counter"]
            rfm9x.send(bytes(ack, "utf-8"), destination=255, node=255)
            print("ack sent!")
            send(packet_text)
            time.sleep(1)

# given an order number and board ID, send a packet over LoRa with that info
# then wait for an ack
def sendLora():
    global sendQueue
    for msg in sendQueue:
        boardid = msg["boardid"]
        num = msg["num"]
        for i in range(5):
            # counter may be useful in confirming acks
            global counter

            data = bytes("MSG, pi, " + boardid + ", " + str(counter) + ", " + num, "utf-8")
            rfm9x.send(data)

            time.sleep(0.1)

            # XXX not sure if this timeout is excessive
            packet = rfm9x.receive(timeout=7.0)
            if packet is not None:
                try:
                    packet_text = str(packet, "ascii")
                except UnicodeDecodeError:
                    continue
                data = packet_text.split(", ")
                ack = toAck(data)
                if ack["type"] == "ACK" and ack["to"] == "pi" and ack["counter"] == str(counter):
                    print("ack received!")
                    counter += 1
                    sendQueue.remove(msg)
                    return
            else: 
                print("no ack received! trying again") # no ack, loop again


#
# MQTT Setup
#

send_topic = "to-app" # pi -> application
recv_topic = "from-app" # application -> pi

# subscribe to the MQTT topic (application -> pi)
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(recv_topic)

# handle incoming MQTT messages by parsing them and sending them over LoRa
# (application will know which boards can be reset with new order nums)
def on_message(client, userdata, msg):
    global sendQueue

    msgstr = str(msg.payload, "utf-8")
    data = msgstr.split(", ")
    boardid = data[0]
    num = data[1]

    sendQueue.append(dict(boardid=boardid, num=num))

def _exit(rc):
    sys.exit(rc)

# send an MQTT message to the application
def send(line):
    client.publish(send_topic, payload=line)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("lorapi.local", 1883, 60) # XXX config file?
client.loop_start()

#
# Main Code
#

def main():
    global counter
    counter = 0

    while True:
        time.sleep(0.1)
        receiveLora() # wait for incoming LoRa messages
        sendLora()

        # MQTT library handles everything in the background,
        # so don't worry about it here
        

main()
