from twisted.web.template import renderer, XMLFile
from twisted.python.filepath import FilePath

from .web_base import BaseResource, ContentElement

class Index(BaseResource):
    isLeaf = True
    addSlash = True

    class Content(ContentElement):
        loader = XMLFile(FilePath('pitool/resources/index.html'))
