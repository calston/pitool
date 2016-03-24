import time

import RPi.GPIO as gpio

from twisted.application import service
from twisted.internet import task, reactor, defer
from twisted.python import log
from twisted.web import server

from .components import * 
from . import web


class PiToolService(service.Service):
    def __init__(self, config):
        self.config = config

    def startService(self):
        gpio.setmode(gpio.BCM)
        
        site = server.Site(web.Index(self))
        reactor.listenTCP(self.config.get('port', 8080), site)

    def stopService(self):
        gpio.cleanup()
