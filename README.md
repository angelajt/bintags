# General Info

Written for my [CS2 Honors Project](contract.md).

# Current Sprint: Second Iteration

For my second iteration, I plan to try out the MCCI C++ library I mention below. My goal is to be able to send and receive messages over LoRa, and to continue updating the display simultaneously. Since the boards won't be running CircuitPython anymore, I'll need to use a different library to talk to the displays (which is good because I wanted a different library anyway!). I think the [Adafruit EPD](https://github.com/adafruit/Adafruit_EPD) library will work (I used it in my proof-of-concept code in the zero-th iteration).

# Previous Sprint: First Iteration

## Hardware
Currently, I am using two [Adafruit Feather M4 Express](https://www.adafruit.com/product/3857) boards. The boards are each attached to an [Adafruit LoRa Radio FeatherWing](https://www.adafruit.com/product/3231), and an [Adafruit 2.9" Tri-Color eInk Display FeatherWing](https://www.adafruit.com/product/4778). The displays have built-in buttons.

I am also using a [LoRa gateway](https://www.adafruit.com/product/4284) attached to a Raspberry Pi 3B.

## Code
The Feather M4 boards are running [CircuitPython code](circuitpython/examples/tinylora/m4-1/displaylora.py) that can simultaneously update the e-ink display and send messages over LoRa, using Adafruit's [TinyLoRa library](https://github.com/adafruit/TinyLoRa) and CircuitPython's [DisplayIO Library](https://circuitpython.readthedocs.io/en/latest/shared-bindings/displayio/index.html). When the code starts running, an order number (hard-coded) shows up on the display, along with a status (initialized to `"created"`). Every time a user presses the middle button on the display, a counter updates the order status, and a message with the order number and counter number gets sent over LoRa. Every 3 minutes, the display updates with the latest message sent.

The LoRa gateway receives the message and converts the information into JSON data, which gets published over the local network via MQTT. Using a [Go program](mqtt/test.go) that parses this JSON data, I can subscribe to the gateway's MQTT topic and see the messages on my computer.

### Architecture
Each order is an object, with attributes `num` (the order number) and `status` (the order status). The `Order` class also has several methods:
- `getMsg()` returns a string message in the format `[num]: [status]`, for displaying or sending over LoRa.
- `sendStatus()` sends the message over LoRa.
- `updateDisplay()` updates text on the display with the message.
- `updateStatus()` calls both `sendStatus()` and `updateDisplay()`, just for ease-of-use in the main code.

# Thoughts

The first iteration was successful in sending messages over LoRa and displaying these messages simultaneously. However, the libraries I'm using are limited in a couple of ways.

First, the display can't be updated more often than 3 minutes or the program halts. This is to help prevent the display from getting permanently damaged (e-ink displays are apparently pretty fickle in this regard), but it does get in the way of debugging while I'm programming. It sucks to have to wait 3 minutes before knowing if my code worked or not. I'd rather not switch to a more powerful OLED display, because those use up a lot more battery. Since I'm planning to attach these to bins for prolonged periods of time, I need a display that can function even if it's not powered. So this means I'll need to find another library that can talk to the e-ink display without the 3-minute hassle.

Second (and definitely more important), I can only send messages over LoRa; I can't receive any messages. This isn't a problem with the LoRa radio itself, just a problem with the library (I think the library was written for sensors, which only need to send data). Unfortunately I haven't found any other CircuitPython libraries that can talk over LoRaWAN (which is how the LoRa gateway works), so I think I'm going to have to switch over to a much more versatile [C++ library](https://github.com/mcci-catena/arduino-lorawan). That library works for the Adafruit Feather M0, which is similar enough to the M4 Express that I think I can get it to work.


# History

## Zero-th Iteration

(WIP)
