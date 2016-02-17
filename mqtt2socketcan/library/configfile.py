__author__ = 'oper'

from configobj import ConfigObj


class getConfig:

    def __init__(self):
        print('Create ConfigObj')
        self.config = None

    def __del__(self):
        print('Delete ConfigObj')

    def open(self, filename):
        try:
            self.config = ConfigObj(filename)
            return True
        except:
            print('ERROR open file:',filename)
        return False

    def keys(self):
        return self.config.keys()

    def value(self,key):
        return self.config[key]

    def tree(self):
        print('dic:',self.config)
        return self.config



if __name__ == '__main__':

    config = configfile()
    config.open('configfile.cfg')
    cfg = config.tree()
    section1 = cfg['BROKER']
    print('Broker',section1)
    print('Keys Layer1',config.keys())
    print('Value key1', config.value('key'))

