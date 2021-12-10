import board
import busio
import digitalio
import time
import adafruit_rfm9x
import displayio
import terminalio
import adafruit_il0373
from adafruit_display_text import label
import json

# TODO put this stuff in config file
# https://docs.python.org/3/library/configparser.html
conffn = open("bt.conf")
conf = json.load(conffn)
BOARD_ID = conf["id"]
DEST_ID = conf["gateway"]

# ensure the display is free
displayio.release_displays()

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)



class Button:
    """
    Represents a physical button that's on the display.

        __init__(): Constructor for the Button class. Declares what pin the
        button talks to on the board, and additional info about the type of
        input the button provides. Because I'm using other pins for the display
        and LoRa radio, I had to cut the trace for the SD card on the display
        in order to use this pin.

        isOn(): Returns a boolean that describes whether or not the button is 
        pushed.
    """

    def __init__(self):
        # set up middle button 
        # (physically it's on the display, but it doesn't directly
        # interact with the display)
        self.button = digitalio.DigitalInOut(board.D12)
        self.button.switch_to_input()
        self.button.direction = digitalio.Direction.INPUT
        self.button.pull = digitalio.Pull.UP

    def isOn(self):
        return not self.button.value # reverse of what you'd expect :P



class Display:
    """
        Represents the e-paper display, which shows the order number and
        status.

        __init__(): Constructor for the Display class. Declares what pins the 
        display talks to on the board, and additional info about the display.

        refresh(): Refresh the physical display with the display group.

        update(order): Update the display group with a new order, but don't 
        refresh.
    """

    def __init__(self):

        # define pins
        epd_cs = board.D9
        epd_dc = board.D10

        # create the displayio connection to the display pins
        display_bus = displayio.FourWire(
            spi, command=epd_dc, chip_select=epd_cs, baudrate=1000000
        )
        time.sleep(1)

        # create the display object
        self.epd = adafruit_il0373.IL0373(
            display_bus,
            width=296,
            height=128,
            rotation=270,
            grayscale=True,
            seconds_per_frame=10,
            black_bits_inverted=False,
            color_bits_inverted=False
        )

        # create a display group for our screen objects
        self.displaygroup = displayio.Group()

        # set colors
        BLACK = 0x000000
        WHITE = 0xFFFFFF

        FOREGROUND_COLOR = BLACK
        BACKGROUND_COLOR = WHITE

        # set a background
        background_bitmap = displayio.Bitmap(296, 128, 1)
        # map colors in a palette
        palette = displayio.Palette(1)
        palette[0] = BACKGROUND_COLOR
        # create a Tilegrid with the background and put in the displayio group
        t = displayio.TileGrid(background_bitmap, pixel_shader=palette)
        self.displaygroup.append(t)

        self.txtgroup = displayio.Group(scale=3, x=20, y=40)
        self.displaytxt = label.Label(terminalio.FONT, text="0", color=FOREGROUND_COLOR)
        self.txtgroup.append(self.displaytxt)  # add this text to the text group
        self.displaygroup.append(self.txtgroup)
    
    def refresh(self):
        self.epd.show(self.displaygroup)
        self.epd.refresh()

    def update(self, order):
        self.displaytxt.text = str(order)


#
# LoRa Radio
#

class Radio:
    """
    Represents the LoRa radio, which sends updated order statuses and receives
    updated order numbers to the gateway (Raspberry Pi).

        __init__(): Constructor for the Radio class. Declares what pins the 
        LoRa radio talks to on the board, and additional info about the radio.

        receive(t): With a timeout of t seconds, wait for a LoRa packet and
        return it. Return None if a packet hasn't been received.

        send(msg): With a given Message object msg, send a LoRa packet
        containing the text of that message.

        receiveOrder(): receive a packet, and parse it and and send an 
        acknowledgement. Return a new Order object with the new order number
        that was given in the message. If the message was not intended for this
        board, return None.

        receiveAck(): receive an acknowledgement and return it

        sendAck(): send an acknowledgement for a given Message object
    """

    counter = 0

    def __init__(self):
        # built-in radio frequency
        RADIO_FREQ_MHZ = 915.0

        # physical pins on radio board
        CS = digitalio.DigitalInOut(board.D16)
        RESET = digitalio.DigitalInOut(board.D5)

        self.rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
        self.rfm9x.tx_power = 13 # default

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


class Message:
    """
    Represents a message that is sent/received over LoRa.

    __init__(): Constructor for the Message class. 

    __str__(): Return the message as a string, for sending over LoRa.

    parse(): Create a Message object from a given LoRa packet.

    fromOrder(): Create a Message object from a given Order object.

    isMsg(): Verify if a message has the MSG type, and is intended for
    this board.

    isAck(): Verify if a message has the ACK type, and is intended for this
    board. Also check the counter to make sure it's acknowledging the right
    message.
    """
    def __init__(self, type = "MSG", source = BOARD_ID, dest = DEST_ID, ordernum = None, status = None, counter = None):
        self.type = type # types can be MSG or ACK
        self.source = source
        self.dest = dest
        self.counter = counter
        self.ordernum = ordernum
        self.status = status

    def __str__(self):
        return self.type + ", " + self.source + ", " + self.dest + ", " + str(self.counter) + ", " + str(self.ordernum) + ", " + self.status

    @classmethod
    def parse(cls, packet):
        try:
            packet_text = str(packet, "utf-8")
        except UnicodeError:
            return None # garbage packet
        print("packet text: ", packet_text)
        data = packet_text.split(", ")
        self = cls(
            type = data[0],
            source = data[1],
            dest = data[2],
            counter = data[3],
            ordernum = data[4],
            status = data[5]
        )
        
        return self

    @classmethod
    def fromOrder(cls, order):
        return cls(ordernum = order.num, status = order.status)


    def isMsg(self):
        if self.type == "MSG" and self.dest == BOARD_ID:
            return True
        else:
            return False
    
    def isAck(self, counter):
        if self.type == "ACK" and self.dest == BOARD_ID and self.counter == str(counter):
            return True
        else:
            return False        

class Order:
    def __init__(self, num):
        self.num = num
        self.statusArr = ["created", "cut", "stripped", "soldered", "completed"]
        self.statusCounter = 0
        self.status = self.statusArr[self.statusCounter]
    
    def __str__(self):
        return self.num + " " + self.status

    def updateStatus(self):
        self.statusCounter += 1
        try:
            self.status = self.statusArr[self.statusCounter]
        except IndexError: # order completed already
            pass


def eventloop(lora, display, button):
    order = None
    changed = False
    while True:
        time.sleep(0.1)
        o = lora.receiveOrder()

        # if we received an order number from the server ...
        if o is not None:
            changed = True
            # change the order that we're managing
            order = o
            print() # print a newline, for easy reading on the console
            print("new order: ", order)
            continue
            
        # if the button is pressed and we are currently managing an order ...
        if button.isOn() and order is not None:
            changed = True
            # update the current order's status
            order.updateStatus()
            print() # print a newline, for easy reading on the console
            print("updated order: ", order)
            msg = Message.fromOrder(order)
            lora.sendMsg(msg)
            continue
        
        if changed:
            display.update(order)

            if display.epd.time_to_refresh <= 0:
                display.refresh()
                print()
                print("display refreshed")
                changed = False
                continue

        # print a series of dots on the serial console (just to know the program is running :P)
        print(".", end = '')

def main():
    lora = Radio()
    display = Display()
    button = Button()
    eventloop(lora, display, button)

main()
