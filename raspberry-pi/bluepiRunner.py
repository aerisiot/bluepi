#! /usr/bin/python
# Jins George - GPS related source code taken from http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/


from gps import *
import threading
import sys, math, Queue

import time, json, requests
from pygsm import GsmModem
from tendo import singleton

gpsd = None  # seting the global variable


class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd  # bring it in scope
        gpsd = gps(mode=WATCH_ENABLE)  # starting the stream of info
        self.current_value = None
        self.running = True  # setting the thread running to true

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next()  # this will continue to loop and grab EACH set of gpsd info to clear the buffer


me = singleton.SingleInstance()
if __name__ == '__main__':
    snapshot_file = '/tmp/bluepisnapshot'
    gsm = GsmModem(port="/dev/ttyUSB1", logger=GsmModem.debug_logger).boot()

    gpsp = GpsPoller()  # create the thread

    iccid = gsm.query("AT^ICCID?", "^ICCID:").strip('"')
    imei = gsm.query("ATI", "IMEI:")
    url = "<bluemix http post url>"
    headers = {'Content-type': 'application/json'}
    msgQ = Queue.Queue()
    try:
        gpsp.start()  # start it up
        while True:
            # It may take a second or two to get good data
            # print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc
            try:

                readings = {}
                readings["iccid"] = iccid
                readings["imei"] = imei
                #### Following will be changed based on GSP module
                lat = gpsd.fix.latitude
                readings["lat"] = lat
                lng = gpsd.fix.longitude
                readings["lng"] = lng
                alt = gpsd.fix.altitude
                readings["alt"] = alt
                speed = gpsd.fix.speed
                readings["speed"] = speed
                track = gpsd.fix.track
                readings["angle"] = track
                sq = gsm.signal_strength()
                readings["sq"] = sq
                cell_id, lac = gsm.cell_id_lac()
                readings["ci"] = cell_id
                readings["lac"] = lac
                mcc, mnc = gsm.mcc_mnc()
                readings["mcc"] = mcc
                readings["mnc"] = mnc
                readings["ts"] = int(round(time.time()))
                readings_json = json.dumps(readings)
                print readings_json
                if lat is None or lng is None or alt is None or sq is None or math.isnan(lat) or math.isnan(
                        lng) or math.isnan(alt) or math.isnan(speed) or math.isnan(sq):
                    print "Location or Signal readings are not retrieved, ignoring send to Server"
                else:
                    #print 'Adding to Queue'
                    msgQ.put(readings_json)

                while not msgQ.empty():
                    #print 'Reading from Queue'
                    r = requests.post(url, data=msgQ.get(), headers=headers)
                    with open(snapshot_file, 'w+') as f:
                        f.seek(0)
                        f.write(readings_json)
                        f.truncate()
            except:
                print 'Excpetion - waiting 2 sec', sys.exc_info()[0]
                time.sleep(2)
            time.sleep(2)  # set to whatever

    except (KeyboardInterrupt, SystemExit):  # when you press ctrl+c
        print
        "\nKilling Thread..."
        gpsp.running = False
        gpsp.join()  # wait for the thread to finish what it's doing
    print
    "Done.\nExiting."
