import time

from emokit.emotiv import Emotiv

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import copy
import sys
import time
import json

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

class RequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        paths = {
            '/': {'status': 200}
        }

        if self.path in paths:
            self.respond(paths[self.path])
        else:
            self.respond({'status': 500})

    def handle_http(self, status_code, path):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = "{}".format(json.JSONEncoder().encode(sharedObject["sensors"]))
        return bytes(response, 'UTF-8')

    def respond(self, opts):
        response = self.handle_http(opts['status'], self.path)
        self.wfile.write(response)

def emoPollingWorker(sharedObject):
    with Emotiv(display_output=True, verbose=False) as headset:
        while True:
            packet = headset.dequeue()
            if packet is not None:
                sharedObject["sensors"] = copy.deepCopy(packet.sensors)
            time.sleep(0.001)


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

    p = threading.Thread(name="PollingThread", target=emoPollingWorker, args=(sharedObject,))
    p.daemon = True

    server_thread.start()
    p.start()

    try:
        while True:
            p.join(250)
            if not p.isAlive():
                break
    except KeyboardInterrupt:
        print
        server.shutdown()
        server.server_close()
        sys.exit(0)
