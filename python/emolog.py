# -*- coding: utf-8 -*-
# This is an example of popping a packet from the Emotiv class's packet queue


import time

from emokit.emotiv import Emotiv

f = open("log.csv","w")
#f.write('"Counter","F3","F3qual","FC5","FC5qual","AF3","AF3qual","F7","F7qual","T7","T7qual","P7","P7qual","O1","O1qual","O2","O2qual","P8","P8qual","T8","T8qual","F8","F8qual","AF4","AF4qual","FC6","FC6qual","F4","F4qual"\n')

if __name__ == "__main__":
    with Emotiv(display_output=True, verbose=False) as headset:
        while True:
            packet = headset.dequeue()
            if packet is not None:
                f.write('%d, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f, %1.4f\n' % (packet.counter, 
                    packet.sensors['F3']['value'], packet.sensors['F3']['quality'],
                    packet.sensors['FC5']['value'], packet.sensors['FC5']['quality'],
                    packet.sensors['AF3']['value'], packet.sensors['AF3']['quality'],
                    packet.sensors['F7']['value'], packet.sensors['F7']['quality'],
                    packet.sensors['T7']['value'], packet.sensors['T7']['quality'],
                    packet.sensors['P7']['value'], packet.sensors['P7']['quality'],
                    packet.sensors['O1']['value'], packet.sensors['O1']['quality'],
                    packet.sensors['O2']['value'], packet.sensors['O2']['quality'],
                    packet.sensors['P8']['value'], packet.sensors['P8']['quality'],
                    packet.sensors['T8']['value'], packet.sensors['T8']['quality'],
                    packet.sensors['F8']['value'], packet.sensors['F8']['quality'],
                    packet.sensors['AF4']['value'], packet.sensors['AF4']['quality'],
                    packet.sensors['FC6']['value'], packet.sensors['FC6']['quality'],
                    packet.sensors['F4']['value'], packet.sensors['F4']['quality']))
                pass
            time.sleep(0.001)
