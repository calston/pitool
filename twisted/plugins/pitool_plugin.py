from zope.interface import implements
 
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
 
import pitool
 
class Options(usage.Options):
    optParameters = [
        ["config", "c", "pitool.yml", "Config file"],
    ]
 
class PiToolServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "pitool"
    description = "pitool"
    options = Options
 
    def makeService(self, options):
        try:
            config = yaml.load(open(options['config']))
        except:
            config = {}
        return pitool.makeService(config)
 
serviceMaker = PiToolServiceMaker()
