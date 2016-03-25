import time

from twisted.internet import reactor, defer, task

try:
    import RPi.GPIO as gpio
except:
    gpio = None


VERSIONS = {
    None: ('Unknown', None),
    '0002': ('Raspberry Pi Model B V1', 'b'),
    '0003': ('Raspberry Pi Model B V1', 'b'),
    '0004': ('Raspberry Pi Model B V2', 'b2'),
    '0005': ('Raspberry Pi Model B V2', 'b2'),
    '0006': ('Raspberry Pi Model B V2', 'b2'),
    '0007': ('Raspberry Pi Model A', 'a'),
    '0008': ('Raspberry Pi Model A', 'a'),
    '0009': ('Raspberry Pi Model A', 'a'),
    '000d': ('Raspberry Pi Model B V2 512MB', 'b2'),
    '000e': ('Raspberry Pi Model B V2 512MB', 'b2'),
    '000f': ('Raspberry Pi Model B V2 512MB', 'b2'),
    '0010': ('Raspberry Pi Model B+', 'bplus'),
    '0011': ('Raspberry Pi Compute Module', 'cm'),
    '0012': ('Raspberry Pi Model A+', 'aplus'),
    'a01041': ('Raspberry Pi 2 Model B', '2b'),
    'a21041': ('Raspberry Pi 2 Model B', '2b'),
    '900092': ('Raspberry PiZero', 'pz'),
    'a02082': ('Raspberry Pi 3 Model B', '3b'),
    'a22082': ('Raspberry Pi 3 Model B', '3b'),
}

MODES = {
    1: 'Input',
    0: 'Output',
    41: 'SPI',
    42: 'I2C',
    43: 'PWM',
    40: 'Serial',
    -1: 'Unset'
}

class Pin(object):
    pass

class Voltage(Pin):
    def __init__(self, voltage):
        self.voltage = voltage
        self.mode = None

    def __str__(self):
        if self.voltage == 0:
            return "<Voltage Ground>"
        else:
            return "<Voltage +%sV>" % self.voltage

class GPIO(Pin):
    """ Pin object representing a GPIO channel

    :param bcm_id: The BCM identifier for this GPIO channel
    :ivar pin: The physical pin number on the board
    :ivar mode: Pin mode, one of GPIO.IN, GPIO.OUT, GPIO.SPI, GPIO.I2C,
                 GPIO.HARD_PWM, GPIO.SERIAL, GPIO.UNKNOWN
    :ivar state: If in input or output mode, the last known state of the pin
    :ivar listening: `bool` value of whether the listener is active for this pin
    """

    def __init__(self, bcm_id):
        self.bcm_id = bcm_id
        self.buffer = []
        self.max_buffer = 100
        self.pin = None
        self.listening = False

        self.mode = self.getFunction()

        # Check initial state
        if self.mode in (0, 1):
            gpio.setup(bcm_id, self.mode)
            self.state = gpio.input(bcm_id)
        else:
            self.state = -1

    def _buffer_write(self, value, t):
        if len(self.buffer) >= self.max_buffer:
            self.buffer.pop(0)
        
        self.buffer.append((t, value))

    def _edge_fall(self, chan):
        self.state = 0
        self._buffer_write(0, time.time())

    def _edge_rise(self, chan):
        self.state = 1
        self._buffer_write(1, time.time())

    def listen(self, callback):
        """Start listening to events on this pin. Updates `self.buffer`"""
        if self.mode == gpio.IN:
            # Remove any existing detection
            gpio.remove_event_detect(self.bcm_id)

            # Use separate callbacks for rising and falling edges
            gpio.add_event_detect(self.bcm_id, gpio.RISING,
                callback=self._edge_rise)
            gpio.add_event_detect(self.bcm_id, gpio.FALLING,
                callback=self._edge_fall)

            self.listening = True

    def stopListening(self):
        """Stop listeners"""
        gpio.remove_event_detect(self.bcm_id)
        self.listening = False

    def setPin(self, pin):
        # Set the pin location
        self.pin = pin

    def getFunction(self):
        """Check the function mode of the channel"""
        return gpio.gpio_function(self.bcm_id)

    def setInput(self):
        """Set channel to input mode"""
        gpio.setup(self.bcm_id, gpio.IN)
        self.mode = gpio.IN

    def setOutput(self):
        """Set channel to output mode"""
        gpio.setup(self.bcm_id, gpio.OUT)
        self.mode = gpio.OUT

    def set(self, state):
        """If in output mode, set the pin high (1) or low (0)"""
        if self.mode == gpio.OUT:
            gpio.output(self.bcm_id, state)
            self.state = state

    def get(self):
        """If in input mode, get the current value"""
        if self.mode == gpio.IN:
            self.state = gpio.input()

        return self.state

    def asJson(self):
        return {
            'bcm_id': self.bcm_id,
            'mode': MODES[self.mode],
            'pin': self.pin,
            'state': self.state
        }

    def __str__(self):
        return "<GPIO bcm_id=%s mode=%s pin=%s>" % (self.bcm_id, MODES[self.mode], self.pin)

    def __repr__(self):
        return self.__str__()


class PiBoard(object):
    def __init__(self):
        if gpio:
            gpio.setmode(gpio.BCM)
        else:
            pass

        self.revision = self._get_revision()
        self.memory = self._get_memory()
        self.board_name, self.board_code = VERSIONS[self.revision]
        self.header = self._get_header_factory(self.board_code)()

        self.gpio = {}

        for i, g in enumerate(self.header):
            if isinstance(g, GPIO):
                g.setPin(i)
                self.gpio[g.bcm_id] = g

    def _header_b(self):
        return [
            Voltage(3.3),   Voltage(5),
            GPIO(0),        Voltage(5),
            GPIO(1),        Voltage(0),
            GPIO(4),        GPIO(14),
            Voltage(0),     GPIO(15),
            GPIO(17),       GPIO(18),
            GPIO(21),       Voltage(0),
            GPIO(22),       GPIO(23),
            Voltage(3.3),   GPIO(24),
            GPIO(10),       Voltage(0),
            GPIO(9),        GPIO(25),
            GPIO(11),       GPIO(8),
            Voltage(0),     GPIO(7),
        ]

    def _header_ab2(self):
        return [
            Voltage(3.3),   Voltage(5),
            GPIO(2),        Voltage(5),
            GPIO(3),        Voltage(0),
            GPIO(4),        GPIO(14),
            Voltage(0),     GPIO(15),
            GPIO(17),       GPIO(18),
            GPIO(27),       Voltage(0),
            GPIO(22),       GPIO(23),
            Voltage(3.3),   GPIO(24),
            GPIO(10),       Voltage(0),
            GPIO(9),        GPIO(25),
            GPIO(11),       GPIO(8),
            Voltage(0),     GPIO(7),
        ]

    def _header_bplus(self):
        return self._header_ab2() + [
            None,       None,
            GPIO(5),    Voltage(0),
            GPIO(6),    GPIO(12),
            GPIO(13),   Voltage(0),
            GPIO(19),   GPIO(16),
            GPIO(26),   GPIO(20),
            Voltage(0), GPIO(21),
        ]

    def _get_header_factory(self, code):
        headers = {
            None: lambda: [],
            'b': self._header_b,
            'b2': self._header_ab2,
            'a': self._header_ab2,
            'bplus': self._header_bplus,
            'aplus': self._header_bplus,
            '2b': self._header_bplus,
            '3b': self._header_bplus,
            'pz': self._header_bplus,
            'cm': None,
        }

        return headers[code]

    def _get_memory(self):
        f = open('/proc/meminfo')
        val = None
        for l in f:
            if l.startswith('MemTotal'):
                val = int(l.split(':')[-1].split()[0].strip())

        return val/1024

    def _get_revision(self):
        f = open('/proc/cpuinfo')
        rev = None
        for l in f:
            if l.startswith('Revision'):
                rev = l.split(':')[-1].strip()

        f.close()
        return rev
