# General Info

Written for my [CS2 Honors Project](contract.md).

### Criteria
Bin Tags:
- [ ] send messages over LoRa
- [ ] receive messages over LoRa
- [ ] display order numbers and statuses
- [ ] update displays freely (every time an order updates)
- [ ] button press updates an order’s status
- [ ] relies on OOP (classes and methods)

Gateway:
- [ ] sends messages over LoRa
- [ ] receives messages over LoRa
- [ ] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] relies on OOP (classes and methods)

Central Host:
- [ ] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] stores boards/orders in a database
- [ ] relies on OOP (classes and methods)

## Hardware
Bin Tags:
- 2 [Adafruit Feather M4 Express](https://www.adafruit.com/product/3857) boards 
- 2 [Adafruit LoRa Radio FeatherWing](https://www.adafruit.com/product/3231) boards 
- 2 [Adafruit 2.9" Greyscale eInk Displays](https://www.adafruit.com/product/4777) 

Gateway:
- 1 [Raspberry Pi 3B](https://www.raspberrypi.com/products/raspberry-pi-3-model-b/)
- 1 [Adafruit LoRa Radio Bonnet](https://www.adafruit.com/product/4074)

Central host:
- My own computer

# First Iteration

## Criteria
Bin Tags:
- [x] send messages over LoRa
- [ ] receive messages over LoRa
- [x] display order numbers and statuses
- [ ] update displays freely (every time an order updates)
- [x] button press updates an order’s status
- [ ] relies on OOP (classes and methods)

Gateway:
- [ ] sends messages over LoRa
- [x] receives messages over LoRa
- [x] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] relies on OOP (classes and methods)

Central Host:
- [ ] sends messages over MQTT
- [x] receives messages over MQTT
- [ ] stores boards/orders in a database
- [ ] has command line interface
- [ ] relies on OOP (classes and methods)

## Process and Outcome

The bin tags in the first iteration were successful in sending messages over LoRa and displaying these messages simultaneously. However, the libraries I was using were limited in a couple of ways.

First, the displays couldn’t be updated more often than 3 minutes or the program halted. This was to help prevent the displays from getting permanently damaged (e-ink displays are apparently pretty fickle in this regard), but it did get in the way of debugging while I was programming. It sucked to have to wait 3 minutes before knowing if my code worked or not. I didn’t want to switch to more powerful OLED displays, because those used up a lot more battery. Since I am planning to attach these to bins for prolonged periods of time, I needed displays that could function even if they weren’t powered. So I thought this meant I needed to find another library that could talk to the e-ink display without the 3-minute hassle.

Second (and definitely more important), I could only send messages over LoRa; I couldn’t receive any messages. This wasn't a problem with the LoRa radio itself, just a problem with the library (I think the library was written for sensors, which only need to send data). In this iteration, the gateway I was using operated on a higher-level networking layer for LoRa called LoRaWAN, which had more server-side support. Unfortunately I hadn’t found any other CircuitPython libraries that could talk over LoRaWAN, so I thought I was going to have to switch over to a much more versatile [C++ library](https://github.com/mcci-catena/arduino-lorawan).

# Second Iteration

## Criteria
Bin Tags:
- [x] send messages over LoRa
- [x] receive messages over LoRa
- [x] display order numbers and statuses
- [ ] update displays freely (every time an order updates)
- [x] button press updates an order’s status
- [x] relies on OOP (classes and methods)

Gateway:
- [x] sends messages over LoRa
- [x] receives messages over LoRa
- [ ] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] relies on OOP (classes and methods)

Central Host:
- [ ] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] stores boards/orders in a database
- [ ] has command line interface
- [ ] relies on OOP (classes and methods)

## Process and Outcome

For my second iteration, I planned to try out the MCCI C++ library I mentioned above. My goal was to be able to send and receive messages over LoRaWAN, and to continue updating the display simultaneously. Since the boards wouldn't be running CircuitPython anymore, I planned to use a different library to talk to the displays, such as the [Adafruit EPD](https://github.com/adafruit/Adafruit_EPD) library.

After some grueling attempts to use the Arduino IDE to talk to the M4 boards, and trying to figure out how to use the MCCI library, I realized that I wasn't making as much progress as I would have liked. I also realized that I had a much more straightforward way of getting two boards to talk to each other over LoRa, using [Adafruit's RFM9x library](https://github.com/adafruit/Adafruit_CircuitPython_RFM9x). Instead of relying on LoRaWAN, I was just going to deal with the lower-level LoRa layer directly, and write more of my own server-side code for the gateway and central host.

By the end of the second iteration I had a simple gateway working that could receive and send messages to and from the bin tags over LoRa. I also started incorporating more object-oriented programming ideas into the code for the bin tags, starting with a `Message` and `Order` class. I still had a 3-minute refresh problem.

# Third Iteration

## Criteria
Bin Tags:
- [x] send messages over LoRa
- [x] receive messages over LoRa
- [x] display order numbers and statuses
- [x] update displays freely (every time an order updates)
- [x] button press updates an order’s status
- [x] relies on OOP (classes and methods)

Gateway:
- [x] sends messages over LoRa
- [x] receives messages over LoRa
- [x] sends messages over MQTT
- [ ] receives messages over MQTT
- [ ] relies on OOP (classes and methods)

Central Host:
- [ ] sends messages over MQTT
- [x] receives messages over MQTT
- [ ] stores boards/orders in a database
- [ ] has command line interface
- [ ] relies on OOP (classes and methods)

## Process and Outcome

In my third iteration, I finally figured out how to get around the 180-second display refresh constraint that was built into the `displayio` library on the bin tags. 

I added more code to the gateway so that it could send order updates over MQTT. I also wrote a simple Go program that could subscribe to an MQTT topic and see the messages that the gateway published.

# Final Iteration

## Criteria
Bin Tags:
- [x] send messages over LoRa
- [x] receive messages over LoRa
- [x] display order numbers and statuses
- [x] update displays freely (every time an order updates)
- [x] button press updates an order’s status
- [x] relies on OOP (classes and methods)

Gateway:
- [x] sends messages over LoRa
- [x] receives messages over LoRa
- [x] sends messages over MQTT
- [x] receives messages over MQTT
- [ ] relies on OOP (classes and methods)

Central Host:
- [x] sends messages over MQTT
- [x] receives messages over MQTT
- [x] stores boards/orders in a database
- [x] has command line interface
- [x] relies on OOP (classes and methods)

## Process and Outcome

I refactored the Python code on the bin tags to incorporate a lot more OOP principles. Everything that the bin tag code controlled is now represented by a class (`Button`, `Display`, `Message`, `Radio`, and `Order`). 

(WIP)

# Final Thoughts

(WIP)

## Going Forward

(WIP)
