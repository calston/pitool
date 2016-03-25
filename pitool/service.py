import time

try:
    import RPi.GPIO as gpio
except:
    gpio = None

from twisted.application import service
from twisted.internet import task, reactor, defer
from twisted.python import log
from twisted.web import server, resource
from twisted.web.static import File
from twisted.python.filepath import FilePath

from .components import * 
from . import web, pidata


class PiToolService(service.Service):
    def __init__(self, config):
        self.config = config
        self.board = pidata.PiBoard()

    def startService(self):
        root = resource.Resource()

        root.putChild('', web.Index(self))
        root.putChild('api', web.API(self))
        root.putChild("static", File(FilePath('pitool/resources/static').path))

        site = server.Site(root)

        reactor.listenTCP(self.config.get('port', 8081), site)

    def stopService(self):
        if gpio:
            gpio.cleanup()
