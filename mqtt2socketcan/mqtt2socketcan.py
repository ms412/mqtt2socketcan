
#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


__app__ = "mqtt2gpio Adapter"
__VERSION__ = "0.8"
__DATE__ = "01.12.2014"
__author__ = "Markus Schiesser"
__contact__ = "M.Schiesser@gmail.com"
__copyright__ = "Copyright (C) 2014 Markus Schiesser"
__license__ = 'GPL v3'

import sys
import time

from mqttclient import *
from msgbus import *
from configfile import getConfig
from socketcan import socketcanif
from logging import log_adapter


class manager(msgbus):

    def __init__(self,cfg_file='configfile.cfg'):

        self._cfg_file = cfg_file

        self._cfg_broker = None
        self._cfg_socket = None
        self._cfg_logging = None

    def read_config(self):
        print('Read Configuration',self._cfg_file)
        cfg_obj = getConfig()
        cfg_obj.open(self._cfg_file)
        self._cfg_broker = cfg_obj.value('BROKER')
        self._cfg_socket = cfg_obj.value('SOCKET')
        self._cfg_logging = cfg_obj.value('LOGGING')
        print('broker',self._cfg_broker)
        print('socket',self._cfg_socket)

    def start_logging(self):
    #    print('Debug Logging1')
        self._log_thread = log_adapter(self._cfg_logging)
        self._log_thread.start()
     #   self.msgbus_publish('LOG','%s Start Logging Adapter')

    def start_mqttbroker(self):
        self._mqttbroker = mqttbroker(self._cfg_broker)
        self._mqttbroker.start()
        return True

    def start_socketcan(self):
        self._socketcan = socketcanif(self._cfg_socket['IF'])
        self._socketcan.start()

    def run(self):
        """
        Entry point, initiates components and loops forever...
        """

    #    self.start_logging()
     #   self.msgbus_publish('LOG','%s Start mqtt2gpio adapter; Version: %s, %s '%('INFO', __VERSION__ ,__DATE__))
        self.read_config()
        self.start_logging()
        self.start_mqttbroker()
        self.start_socketcan()

      #  self.msgbus_publish('MQTT_TX','123456')
        self.msgbus_subscribe('MQTT_RX',self.mqttif)
        self.msgbus_subscribe('CAN_RX',self.canif)

    def mqttif(self,data):
        print('MQTT_RY',data)
        message = data.get('MESSAGE')
        channel = data.get('CHANNEL')

        channellist = channel.split('/')
        network = channellist[1]
        address = channellist[2]
        rcpcall = channellist[3]
        print('Network',network,address,rcpcall)
        msg = 'Received mqtt call'
        self.msgbus_publish('LOG','%s SocketCanIF: %s CAN ID: %s Message: %s '%('DEBUG',msg,address,message))
        self.msgbus_publish('CAN_TX',address,message)


    def canif(self,addr,data):
        message = {}
        x=''.join(chr(i) for i in data)
        print('CANif',addr,data)
        publish = '/OPENHAB'
        print('MEssage Type',type(x))
        message['MESSAGE']=x
        message['CHANNEL']=publish

        msg = 'Received from Socketcan'
        self.msgbus_publish('LOG','%s SocketCanIF: %s MQTT Channel: %s  '%('DEBUG',msg,message))

        self.msgbus_publish('MQTT_TX',message)



      #  self.start_devices()


if __name__ == "__main__":

    print ('main')
    if len(sys.argv) == 2:
        configfile = sys.argv[1]
    else:
        configfile = 'configfile.cfg'

   # print('Configfile',configfile)
    mgr_handle = manager(configfile)
    mgr_handle.run()