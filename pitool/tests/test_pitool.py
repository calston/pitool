
from twisted.trial import unittest
from twisted.internet import defer

from pitool.service import PiToolService
from pitool import pidata

class Test(unittest.TestCase):
    def test_board(self):
        board = pidata.PiBoard()

