"""Pitool - pitool

.. moduleauthor:: Colin Alston <colin@imcol.in>

"""

from pitool import service


def makeService(config):
    # Create PiToolService
    return service.PiToolService(config)
