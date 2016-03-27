import json
import inspect

from twisted.web.template import renderer, XMLFile
from twisted.python.filepath import FilePath
from twisted.web.static import File

from twisted.web.template import tags

from .web_base import BaseResource, ContentElement, JSONResource
from . import pidata

class API(JSONResource):
    isLeaf = True
    
    def call_gpio(self, request):
        gpios = [g.asJson() for g in self.service.board.gpio.values()]

        return {
            'count': len(gpios),
            'pins': gpios
        }

    def call_gpio_mode(self, request):
        io, mode = request.path.split('/')[-2:]
        io = int(io)

        if io in self.service.board.gpio:
            g = self.service.board.gpio[io]

            if mode == 'input':
                g.setInput()
            if mode == 'output':
                g.setOutput()

            return g.asJson()
        
        return {}

    def call_gpio_set(self, request):
        io, state = request.path.split('/')[-2:]
        io = int(io)

        if io in self.service.board.gpio:
            g = self.service.board.gpio[io]
            g.set(int(state))

            return g.asJson()

        return {}

    def get(self, request):
        members = dict([
            ('/api/' + n.lstrip('call_').replace('_', '/'), m) for n,m in
            inspect.getmembers(self, predicate=inspect.ismethod)
            if n.startswith('call_')
        ])

        keys = members.keys()
        keys.sort(key=lambda n: len(n))

        for key in reversed(keys):
            if request.path.startswith(key):
                return members[key](request)

        return {'Err': 'No command'}

class Bitbanger(BaseResource):
    isLeaf = True

    class Content(ContentElement):
        loader = XMLFile(FilePath('pitool/resources/bitbanger.html'))


class Analyzer(BaseResource):
    isLeaf = True

    class Content(ContentElement):
        loader = XMLFile(FilePath('pitool/resources/analyzer.html'))


class Index(BaseResource):
    isLeaf = True

    class Content(ContentElement):
        loader = XMLFile(FilePath('pitool/resources/index.html'))

        @renderer
        def board(self, request, tag):
            board = self.service.board

            url = "/static/images/modules/%s.png" % board.board_code
            return tag.fillSlots(brd_name=board.board_name, image=url, mem=str(board.memory))

