import copy
import exceptions
import json
import math
import time

try:
    import RPi.GPIO as gpio
except:
    gpio = None

from twisted.application import service
from twisted.internet import task, reactor, defer
from twisted.python import log
from twisted.python.filepath import FilePath
from twisted.web import server, resource
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

from .components import * 
from . import web, pidata


class DataProtocol(WebSocketServerProtocol):
    def __init__(self, board):
        WebSocketServerProtocol.__init__(self)
        self.log.debug = lambda *a, **kw: None
        self.board = board
        self.gpio_buffers = {}
        self.streaming = False
        self.inputs = []
        self.start_time = time.time()*1000000
        self.t = None

    def onMessage(self, payload, binary):
        if not binary:
            cmd = payload.decode('utf8').split()[0]
            try:
                c = getattr(self, 'cmd_%s' % cmd.lower())
                return defer.maybeDeferred(c, payload)
            except exceptions.AttributeError:
                log.msg("Command '%s' not implemented" % cmd)

    def send(self, t, payload):
        self.sendMessage(json.dumps({'type': t, 'payload': payload}), False)
        
    def _get_inputs(self):
        inputs = []
        for id, g in self.board.gpio.items():
            if g.mode == 1:
                inputs.append(g)
        inputs.sort(key=lambda g: g.bcm_id)
        return inputs

    def _format_timebase(self, buffer, base=100000, duration=5000000):
        if not buffer:
            return []
        base = float(base)
        chunks = int(math.floor(duration/base))

        minT = self.start_time - duration

        wlist = []

        tL = 0
        vL = 0
        for t, v in reversed(buffer):
            if (len(wlist) >= chunks) or (t < minT):
                # Stop reading buffer when our timebase is full
                break

            if tL:
                # uSecs since last datapoint
                tD = tL - t
            else:
                # Fill waveform since earliest of all waveforms
                tD = self.start_time - t

            basebits = int(math.ceil(tD/base))
            wlist.extend([v] * basebits)
            tL = t
            vL = v

        remainder = len(wlist) - chunks
        if remainder < 0:
            wlist.extend([0]*remainder)
        
        return reversed(wlist)

    def sendBuffer(self):
        self.inputs = self._get_inputs()
        
        heads = []
        # Snapshot all the buffers
        for g in self.inputs:
            self.gpio_buffers[g.bcm_id] = copy.deepcopy(g.buffer)
            if self.gpio_buffers[g.bcm_id]:
                heads.append(self.gpio_buffers[g.bcm_id][-1])
        
        if heads:
            self.start_time = max(heads, key=lambda h: h[0])[0]

        # Rebase waves to t-zero
        waveforms = []
        for g in self.inputs:
            waveforms.append({
                'id': g.bcm_id,
                'buffer': list(self._format_timebase(
                                self.gpio_buffers[g.bcm_id]))
            })

        self.send('waveform_start', waveforms)

    def cmd_start_buffer_stream(self, payload):
        log.msg(payload)
        
        self.t = task.LoopingCall(self.sendBuffer)
        self.t.start(0.05)

    def onClose(self, wasClean, code, reason):
        if self.t:
            self.t.stop()
            log.msg("Stopping buffer send")

class WSFactory(WebSocketServerFactory):
    def __init__(self, url, board):
        WebSocketServerFactory.__init__(self, url)
        self.board = board

    def buildProtocol(self, addr):
        p = self.protocol(self.board)
        p.factory = self
        return p


class PiToolService(service.Service):
    def __init__(self, config):
        self.config = config
        self.board = pidata.PiBoard()

    def startService(self):
        root = resource.Resource()

        root.putChild('', web.Index(self))
        root.putChild('api', web.API(self))
        root.putChild('analyzer', web.Analyzer(self))
        root.putChild("static", File(FilePath('pitool/resources/static').path))

        site = server.Site(root)

        reactor.listenTCP(self.config.get('port', 8081), site)

        factory = WSFactory(u"ws://127.0.0.1:8082", self.board)
        factory.protocol = DataProtocol

        reactor.listenTCP(8082, factory)

        for g in self.board.gpio.values():
            g.listen()

    def stopService(self):
        for g in self.board.gpio.values():
            g.stopListening()

        if gpio:
            gpio.cleanup()
