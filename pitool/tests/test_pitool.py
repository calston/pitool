
from twisted.trial import unittest
from twisted.internet import defer

from pitool.service import PitoolService

class Test(unittest.TestCase):
    def test_lame(self):
        cls = PitoolService({})
