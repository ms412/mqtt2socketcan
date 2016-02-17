
from threading import Thread
from queue import Queue
from array import *
from msgbus import msgbus

import time
import socket
import select
import struct



class socketcanif(Thread,msgbus):

    def __init__(self,canif = 'vcan0'):
        Thread.__init__(self)
        print('Start Socketcan Server Interface')
        msg = 'Create Object'
        self.msgbus_publish('LOG','%s SocketCanIF: %s '%('INFO',msg))

        '''
        queues
        '''
        self._sendQ = Queue()
        self._receiveQ = Queue()

        '''
        socketcan server
        '''
        self._canif = canif
        print(self._canif)
        self._socketcan  = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self._socketcan.setblocking(0)

        self._can_frame_format = "=IB3x8s"
        self._can_frame_size = struct.calcsize(self._can_frame_format)

        self._inSocket = []
        self._outSocket = []

        self.START_BYTE = 0x7D
        self.ESC_BYTE = 0x7E
        self.END_BYTE = 0x7D

        self.state = 0
        self.timeout = 10
        self.timeout_start = 0

        self.buffer = []
        self.newlist = []
        self.txframeready = False
       # self.run()
        self.msgbus_subscribe('CAN_TX', self.CANframing)

    def __del__(self):
        print('Stop Socketcan Server Interface')
        msg = 'Delete Object'
        self.msgbus_publish('LOG','%s SocketCanIF: %s '%('INFO',msg))

    def connect(self):
        # create a raw socket and bind it to the given CAN interface

        self._socketcan.bind((self._canif,))

        self._inSocket = [self._socketcan]
        self._outSocket = [self._socketcan]
        msg = 'Connected to'
        self.msgbus_publish('LOG','%s SocketCanIF: %s %s'%('INFO',msg,self._canif))

    def run(self):
        self.connect()

        while(True):

            time.sleep(1)
          #  print('loop')

            readable, writeable, exceptional = select.select(self._inSocket, self._outSocket, self._inSocket)

            for socketId in readable:

                canframe, addr = socketId.recvfrom(16)
                print("Receive",canframe)
                msg = 'Received CAN Frame'
                self.msgbus_publish('LOG','%s SocketCanIF: %s Frame: %s'%('DEBUG',msg,canframe))
                self.CANunframing(canframe)
                #self._receiveQ.put(canframe)

            for socketId in writeable:
             #   print('writeabel')
                while not self._sendQ.empty():
                    canframe = self._sendQ.get()
                    try:
                        msg = 'Send CAN Frame'
                        self.msgbus_publish('LOG','%s SocketCanIF: %s Frame: %s'%('DEBUG',msg,canframe))
                        print('Send', canframe)
                        socketId.send(canframe)
                    except socket.error:
                        print('Error sending CAN frame')
                        msg = 'Failed to send CAN Frame'
                        self.msgbus_publish('LOG','%s SocketCanIF: %s Frame: %s'%('ERROR',msg,canframe))

            if (self.txframeready):
                self.txframeready = False
                print('RUN')
                self.rx(self.newlist)

    def CANunframing(self,canframe):
        START = 0
        RUN = 1
        STUFFING = 2
        ENDE = 3
        TIMEOUT = 4

        canId, canlen, canData = struct.unpack(self._can_frame_format, canframe)


        print('time',time.time()-self.timeout_start)

        if (time.time()-self.timeout_start > self.timeout & self.state == RUN):
            print('timeout')
            msg = 'Receiver Timeout'
            self.msgbus_publish('LOG','%s SocketCanIF: %s '%('ERROR',msg))
            self.state = TIMEOUT

        print('STATE1',self.state)

        for byte in canData[:canlen]:
            print('Byte:',byte)
            print('Buffer',self.buffer)
            if self.state == START:
                if byte == self.START_BYTE:
                    self.state = RUN
                    del self.buffer[:]
                    print('buffer',self.buffer)
                    self.timeout_start = time.time()
                    print('STATE2:',self.state)

            elif self.state == RUN:
                print('STATE3:',self.state)
                if byte == self.ESC_BYTE:
                    self.state = STUFFING
                    print('stuff')

                elif byte == self.END_BYTE:
                    self.state = START
                    msg = 'frame complete received'
                    self.msgbus_publish('LOG','%s SocketCanIF: %s CAN ID: %s Frame: %s '%('DEBUG',msg,canId,self.buffer))
                    self.msgbus_publish('CAN_RX',canId,self.buffer)
                    print('END')

                else:
                    self.buffer.append(byte)

            elif self.state == STUFFING:
                print('Stuffing')
                self.buffer.append(byte ^ 0x20)
                self.state = RUN
               # time.sleep(11)

            elif self.state == TIMEOUT:
                print('Timeout')
                self.state = START
                for item in self.buffer:
                    del item

        return

    def CANframing(self,canID,data):
        newlist = []
        canframe = []
        print('TX',canID,data)
        msg = 'Send Frame'
        self.msgbus_publish('LOG','%s SocketCanIF: %s CAN ID: %s Frame: %s '%('DEBUG',msg,canID,data))

        for element in data:
            if element in (self.END_BYTE,self.ESC_BYTE):
                newlist.append(self.ESC_BYTE)
                newlist.append(element ^ 0x20)
            else:
                newlist.append(element)
        newlist.insert(0,self.START_BYTE)
        newlist.append(self.END_BYTE)

        length = len(newlist)
        print('Test1:',newlist,length)

      #  i = 0
        for element in newlist:
          #  i = i + 1
            length = length -1
          #  print('Type',type(element))
            canframe.append(int(element))
            print('Coutner:',len(canframe),length)
            if (len(canframe) == 8 or length == 0):
                print('Test2:',canframe)
               # canframe = canframe.ljust(8, b'\x00')
                canarray = array('B', canframe).tostring()
                canframe=[]
         #       i = 0
                can_dlc = len(canarray)

                print('CANARRAY:',type(canarray),type(can_dlc),type(int(canID)))
                print('CANFRAME:',canarray, can_dlc, int(canID))
                self._sendQ.put(struct.pack(self._can_frame_format, int(canID), can_dlc, canarray))
        return True


    def interface(self,addr,data,callback):
        self._addr = addr
        print('interface')
        self.tx(addr,data)
        callback(data)

    def get(self):
        print('Result', len(self.buffer),self.buffer)
        return self.buffer