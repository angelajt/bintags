#!/usr/bin/python

import atexit
import configparser
from optparse import OptionParser
import os
import re
import readline
import serial
import shlex
from io import StringIO
import sys

import paho.mqtt.client as mqtt

def main():

    parser = OptionParser()
    parser.add_option("-b", "--broker", dest="mqtt_broker", help="mqtt broker")
    (opts, args) = parser.parse_args()
    send_topic, recv_topic = args

    dir = os.path.join(os.environ['PWD'], ".mqtt_shell")
    histfn = os.path.join(dir, ".history")

    # set up history
    if not os.path.exists(dir):
        os.mkdir(dir)
    try:
        readline.read_history_file(histfn)
    except IOError:
            pass
    atexit.register(readline.write_history_file, histfn)

    # mqtt
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#")
        client.subscribe(recv_topic)

    def on_message(client, userdata, msg):
        # print(msg.topic+" "+str(msg.payload))
        print(str(msg.payload))

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(opts.mqtt_broker, 1883, 60)
    client.loop_start()

    def _exit(rc):
        sys.exit(rc)

    def send(line):
        client.publish(send_topic, payload=line)

    while True:
        try:
            line = input("")
            send(line)
        except KeyboardInterrupt:
            _exit(0)
        except EOFError:
            _exit(0)
            
main()
