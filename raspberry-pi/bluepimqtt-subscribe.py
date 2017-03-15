#! /usr/bin/python
# Jins George

import paho.mqtt.client as mqtt
import json
import wiringpi, time, math
from pygsm import GsmModem
from tendo import singleton

PIN_RED = 0
PIN_GREEN = 2
PIN_BLUE = 1
snapshot_file = '/tmp/bluepisnapshot'
me = singleton.SingleInstance()

def init_wiringpi():
    wiringpi.wiringPiSetup()
    wiringpi.pinMode(PIN_RED, wiringpi.GPIO.OUTPUT)
    wiringpi.pinMode(PIN_GREEN, wiringpi.GPIO.OUTPUT)
    wiringpi.pinMode(PIN_BLUE, wiringpi.GPIO.OUTPUT)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    global  gsm
    #Initializing GSM Modem
    gsm = GsmModem(port="/dev/ttyUSB1", logger=GsmModem.debug_logger).boot()

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(("iot-2/cmd/bluepi/fmt/json", 0))

def red():
    rgb_cleanup()
    wiringpi.digitalWrite(PIN_RED, 1)
    time.sleep(10)
    rgb_cleanup()

def blue():
    rgb_cleanup()
    wiringpi.digitalWrite(PIN_BLUE, 1)
    time.sleep(10)
    rgb_cleanup()

def green():
    rgb_cleanup()
    wiringpi.digitalWrite(PIN_GREEN, 1)
    time.sleep(10)
    rgb_cleanup()


def rgb_cleanup():
    wiringpi.digitalWrite(PIN_GREEN, 0)
    wiringpi.digitalWrite(PIN_BLUE, 0)
    wiringpi.digitalWrite(PIN_RED, 0)

def handle_sqlight(command):
    #Invoking Signal Strength
    sq = gsm.signal_strength()
    # Blink the Red LED if the signal strength cannot be retrieved.
    if(sq is None or sq is  math.isnan(sq) ):
        rgb_cleanup()
        for x in range(5):
            wiringpi.digitalWrite(PIN_RED, 1)
            wiringpi.delay(1)
            wiringpi.digitalWrite(PIN_RED, 0)

        rgb_cleanup()
        return
    norm_sq= sq/32.0
    if norm_sq < 0.4 :
        red()
    elif norm_sq >= 0.4 and norm_sq < 0.6:
        blue()
    elif norm_sq >= 0.6:
        green()
    else:
        #show blink
        print 'Unknown Signal'



def handle_snapshot(command):
    with open(snapshot_file, 'r+') as f:
        snapshot = f.read()
        if snapshot is not None:
            print 'Responding Snapshot :' + snapshot
            client.publish('iot-2/evt/bluepi/fmt/json', payload=snapshot, qos=0, retain=False)




# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    command = json.loads(msg.payload)
    print 'Received Command : '+ str(command)
    handlers[command['command']](command)

def publish(client, topic, payload):
    print("Publishing!")
    client.publish(topic, payload)

# Register handlers here. key is the command and value is the handle function
handlers = {
    'sqlight':handle_sqlight,
    'snapshot':handle_snapshot
}

#Client Options
#client_id= 'd:w4ne2y:bluepi:1234567890'
client_id= 'd:<orgid>:<device type>:<device id>'
client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message

#client.username_pw_set('use-token-auth', '3sdf3qfg3r')
client.username_pw_set('use-token-auth', '<auth pass>')

client.connect("<orgid>.messaging.internetofthings.ibmcloud.com", 1883, 60)
#client.connect("234d4.messaging.internetofthings.ibmcloud.com", 1883, 60)
gsm = None
# Initialize the wiring pi module for LED blink
init_wiringpi()

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()
