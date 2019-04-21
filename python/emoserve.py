import time

from emokit.emotiv import Emotiv

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import copy
import sys
import time
import json
import pandas
import signal
import numpy as np

sharedObject = dict()
sharedObject["sensors"] = dict()

# bootstrap some data for when EPOC not connected, so we can test
sharedObject["sensors"]["counter"] = 0
sharedObject["sensors"]["F3"] = dict(value=4687.3636, quality=0)
sharedObject["sensors"]["FC5"] = dict(value=3966.1515, quality=0)
sharedObject["sensors"]["AF3"] = dict(value=4452.4545, quality=0)
sharedObject["sensors"]["F7"] = dict(value=4459.6667, quality=0)
sharedObject["sensors"]["T7"] = dict(value=4399.3939, quality=0)
sharedObject["sensors"]["P7"] = dict(value=4591.0303, quality=0)
sharedObject["sensors"]["O1"] = dict(value=4376.7273, quality=0)
sharedObject["sensors"]["O2"] = dict(value=4334.4848, quality=0)
sharedObject["sensors"]["P8"] = dict(value=4211.8788, quality=0)
sharedObject["sensors"]["T8"] = dict(value=4450.9091, quality=0)
sharedObject["sensors"]["F8"] = dict(value=4379.303, quality=0)
sharedObject["sensors"]["AF4"] = dict(value=4207.7576, quality=0)
sharedObject["sensors"]["FC6"] = dict(value=4483.3636, quality=0)
sharedObject["sensors"]["F4"] = dict(value=4174.7879, quality=0)
sharedObject["dft"] = dict()
sharedObject["dft"]["F3"] = [0] * 64
sharedObject["dft"]["FC5"] = [0] * 64
sharedObject["dft"]["AF3"] = [0] * 64
sharedObject["dft"]["F7"] = [0] * 64
sharedObject["dft"]["T7"] = [0] * 64
sharedObject["dft"]["P7"] = [0] * 64
sharedObject["dft"]["O1"] = [0] * 64
sharedObject["dft"]["O2"] = [0] * 64
sharedObject["dft"]["P8"] = [0] * 64
sharedObject["dft"]["T8"] = [0] * 64
sharedObject["dft"]["F8"] = [0] * 64
sharedObject["dft"]["AF4"] = [0] * 64
sharedObject["dft"]["FC6"] = [0] * 64
sharedObject["dft"]["F4"] = [0] * 64

rawData = dict()
rawData["F3"] = [0] * 128
rawData["FC5"] = [0] * 128
rawData["AF3"] = [0] * 128
rawData["F7"] = [0] * 128
rawData["T7"] = [0] * 128
rawData["P7"] = [0] * 128
rawData["O1"] = [0] * 128
rawData["O2"] = [0] * 128
rawData["P8"] = [0] * 128
rawData["T8"] = [0] * 128
rawData["F8"] = [0] * 128
rawData["AF4"] = [0] * 128
rawData["FC6"] = [0] * 128
rawData["F4"] = [0] * 128

sendRawArray = False
signalNames = ("F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4")
running = True

def runDFT(signalName, rawData, results):
    y = rawData[signalName]
    N = len(y)
    Y_k = np.fft.fft(y)[0:int(N / 2)] / N  # FFT function from numpy
    Y_k[1:] = 2 * Y_k[1:]  # need to take the single-sided spectrum only
    Pxx = np.abs(Y_k)  # be sure to get rid of imaginary part
    Pxx[0] = 0
    # print(Pxx)
    results[signalName] = Pxx.tolist()


class RequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        global signalNames
        paths = {
            '/': {'status': 200}
        }
        for signalName in signalNames:
            paths['/' + signalName] = {'status': 200}

        if self.path in paths:
            self.respond(paths[self.path])
        else:
            self.respond({'status': 500})

    def handle_http(self, status_code, path):
        global sendRawArray
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if len(path) > 1:
            sensorName = path[1:]
            runDFT(sensorName, rawData, sharedObject["dft"])
            # if sharedObject["dft"][sensorName][5] > 0.18:
            #     print("5Hz detect > threshold: "+str(sharedObject["dft"][sensorName][5]))

            if sendRawArray:
                response = "{}".format(json.JSONEncoder().encode(sharedObject["dft"][sensorName]))
            else:
                dft = {"name": sensorName, "values": sharedObject["dft"][sensorName]}
                response = "{}".format(json.JSONEncoder().encode(dft))
        else:
            response = "{}".format(json.JSONEncoder().encode(sharedObject["sensors"]))
        return bytes(response, 'UTF-8')

    def respond(self, opts):
        response = self.handle_http(opts['status'], self.path)
        self.wfile.write(response)


def emoPollingWorker(sharedObject):
    global running
    with Emotiv(display_output=True, verbose=False) as headset:
        while True:
            packet = headset.dequeue()
            if packet is not None:
                sharedObject["sensors"] = copy.deepCopy(packet.sensors)

            time.sleep(0.001)


def csvPollingWorker(sharedData, csv):
    global signalNames
    global rawData
    df = pandas.read_csv(csv, header=None, names=(
        "Counter", "F3", "F3qual", "FC5", "FC5qual", "AF3", "AF3qual", "F7", "F7qual", "T7", "T7qual", "P7", "P7qual",
        "O1",
        "O1qual", "O2", "O2qual", "P8", "P8qual", "T8", "T8qual", "F8", "F8qual", "AF4", "AF4qual", "FC6", "FC6qual",
        "F4",
        "F4qual"))
    index = 0
    max = len(df.index)
    while running:
        row = df.iloc[index]

        for name in signalNames:
            rawData[name].pop(9)
            rawData[name].append((row[name]-4096)/4096.0)

        index += 1
        if index >= max:
            index = 0
        time.sleep(1/128.0)


def signal_handler(sig, frame):
    global running
    running = False


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "0.0.0.0", 3838
    server = HTTPServer((HOST, PORT), RequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    if len(sys.argv) < 2:
        p = threading.Thread(name="PollingThread", target=emoPollingWorker, args=(sharedObject,))
        p.daemon = True
        p.start()
    else:
        p = threading.Thread(name="PollingThread", target=csvPollingWorker, args=(sharedObject, sys.argv[1]))
        p.daemon = True
        p.start()

    try:
        print('Press Ctrl+C or Ctrol+Break to exit')
        signal.signal(signal.SIGINT, signal_handler)
        while running:
            p.join(0.1)
            if not p.isAlive():
                break
    except KeyboardInterrupt:
        print
        server.shutdown()
        server.server_close()
        sys.exit(0)
