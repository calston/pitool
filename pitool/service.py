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
        self.active = []
        self.start_time = time.time()*1000000
        self.t = None

        self.base = 100000
        self.window = 5000000

    def onMessage(self, payload, binary):
        if not binary:
            log.msg(payload)
            msg = json.loads(payload.decode('utf8'))
            cmd = msg['type']
            try:
                c = getattr(self, 'cmd_%s' % cmd.lower())
                return defer.maybeDeferred(c, msg['args'])
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

    def _format_timebase(self, buffer):
        if not buffer:
            return []
        base = float(self.base)
        duration = self.window
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

        if buffer and (not wlist):
            v = buffer[-1][1]
            wlist = [v,v]

        remainder = len(wlist) - chunks
        if remainder < 0:
            wlist.extend([0]*remainder)
        
        return reversed(wlist)

    def getBuffer(self):
        self.inputs = self._get_inputs()
        
        heads = []
        # Snapshot all the buffers
        for g in self.inputs:

            if self.active and (g.bcm_id not in self.active):
                # Skip any inputs the user disables
                continue 

            self.gpio_buffers[g.bcm_id] = copy.deepcopy(g.buffer)
            if self.gpio_buffers[g.bcm_id]:
                heads.append(self.gpio_buffers[g.bcm_id][-1])
        
        if heads:
            self.start_time = max(heads, key=lambda h: h[0])[0]

    def sendBuffer(self):
        # Rebase waves to t-zero
        waveforms = []
        for g in self.inputs:
            waveforms.append({
                'id': g.bcm_id,
                'buffer': list(self._format_timebase(
                                self.gpio_buffers[g.bcm_id]))
            })

        self.send('waveform_start', waveforms)

    def streamBuffer(self):
        self.getBuffer()
        self.sendBuffer()

    def sendOneshotBuffers(self):
        self.getBuffer()

        for g in self.inputs:
            g.stopListening()

        self.sendBuffer()

    def cmd_set_timebase(self, args):
        self.base = args['val']

    def cmd_set_window(self, args):
        self.window = args['val']

    def cmd_set_channels(self, args):
        self.active = args['active']

    def cmd_one_shot(self, args):
        trigger_chan = args.get('chan')
        trigger = args['trigger']

        for g in self.inputs:
            g.stopListening()

        for g in self.inputs:
            g.flushBuffer()

        for g in self.inputs:
            g.listen()

        if trigger is None:
            reactor.callLater(self.window/1000000.0, self.sendOneshotBuffers)

    def cmd_stop_buffer_stream(self, args):
        if self.t:
            self.t.stop()
            log.msg("Stopping buffer send")

            self.t = None

    def cmd_start_buffer_stream(self, args):
        if not self.t:
            log.msg("Starting buffer send")
            
            for g in self.inputs:
                g.listen()

            self.t = task.LoopingCall(self.streamBuffer)
            self.t.start(0.1)

    def onClose(self, wasClean, code, reason):
        self.cmd_stop_buffer_stream(None)

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
        factory.setProtocolOptions(allowHixie76 = True)

        reactor.listenTCP(8082, factory)

        for g in self.board.gpio.values():
            g.listen()

    def stopService(self):
        for g in self.board.gpio.values():
            g.stopListening()

        if gpio:
            gpio.cleanup()
