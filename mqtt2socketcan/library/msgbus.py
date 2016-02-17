__author__ = 'oper'

class msgbus(object):
    callerList = {}

    def __init__(self):
        test =0


    def msgbus_subscribe(self, channel, callback):

        if channel not in msgbus.callerList.keys():
   #         print ('Create Channel new')
            msgbus.callerList[channel] = []
        msgbus.callerList[channel].append(callback)

   #     print('callerList',msgbus.callerList)

        return True

    def unsubscribe(self, channel, callback):

        if channel in msgbus.callerList.keys():
            msgbus.callerList[channel].remove(callback)

        return True

    def unsubscribe_all(self, channel):

        if channel in msgbus.callerList.keys():
            msgbus.callerList[channel] = []

        return True

    def has_subscriber(self,channel):

        result = 0

        if channel in msgbus.callerList.keys():
            result = len(msgbus.callerList[channel])

        return result

    def msgbus_publish(self, channel, *args, **kwargs):

        result = False

    #   print('Hier',channel)
        if channel in msgbus.callerList.keys():
            result = True
     #       print('Channel',channel)
            for item in msgbus.callerList[channel]:
      #          print('Item',item)
                item(*args, **kwargs)
        else:
            print('Channel not found')

        return result

    def debug(self):

        print ('DEBUG',msgbus.callerList)

        return

