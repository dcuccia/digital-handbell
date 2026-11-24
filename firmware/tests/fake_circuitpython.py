"""Minimal stand-ins for CircuitPython modules, for testing handbell.hw on CPython.

They model only what the adapters use and record an ordered event log so
tests can check hardware sequencing (for example, that I2S clocks stop
before the amplifier loses power). They are not simulations of the chips.
"""

import struct
import sys
import types

LOG = []


def _module(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


class Pin:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class DigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self._value = None
        self.pull = None
        self.input_value = True

    def switch_to_output(self, value=False):
        self._value = value
        LOG.append("%s=%d" % (self.pin.name, int(value)))

    def switch_to_input(self, pull=None):
        self.pull = pull
        self._value = None

    @property
    def value(self):
        return self.input_value if self._value is None else self._value

    @value.setter
    def value(self, v):
        if v != self._value:
            LOG.append("%s=%d" % (self.pin.name, int(v)))
        self._value = v

    def deinit(self):
        pass


class AnalogIn:
    def __init__(self, pin):
        self.pin = pin
        self.reference_voltage = 3.3
        self.value = 0


class I2SOut:
    def __init__(self, bit_clock, word_select, data):
        LOG.append("i2s.init")

    def play(self, sample, loop=False):
        LOG.append("i2s.play")

    def stop(self):
        LOG.append("i2s.stop")

    def deinit(self):
        LOG.append("i2s.deinit")


class MixerVoice:
    def __init__(self, index):
        self.index = index
        self.level = 1.0
        self.playing = False
        self.sample = None

    def play(self, sample, loop=False):
        self.sample = sample
        self.playing = True
        LOG.append("voice%d.play:%s" % (self.index, getattr(sample, "name", type(sample).__name__)))

    def stop(self):
        self.playing = False


class Mixer:
    def __init__(self, voice_count=2, **kw):
        self.kw = kw
        self.voice = [MixerVoice(i) for i in range(voice_count)]


class MP3Decoder:
    constructed = 0

    def __init__(self, path, buffer=None):
        self.name = path
        MP3Decoder.constructed += 1

    def open(self, path):
        self.name = path


class WaveFile:
    def __init__(self, f, buffer=None):
        self.name = getattr(f, "name", "wav")
        self.buffer = buffer


class RawSample:
    def __init__(self, data, sample_rate=8000):
        self.name = "raw"


class Envelope:
    def __init__(self, **kw):
        self.kw = kw


class Note:
    def __init__(self, **kw):
        self.kw = kw


class Synthesizer:
    name = "synth"

    def __init__(self, sample_rate=11025, channel_count=1):
        self.pressed = []

    def press(self, notes):
        self.pressed.extend(notes)
        LOG.append("synth.press:%d" % len(notes))

    def release(self, notes):
        LOG.append("synth.release:%d" % len(notes))

    def release_all(self):
        self.pressed = []


class Event:
    def __init__(self, key_number=0, pressed=True):
        self.key_number = key_number
        self.pressed = pressed


class EventQueue:
    def __init__(self):
        self.queue = []

    def get_into(self, event):
        if not self.queue:
            return False
        event.pressed = self.queue.pop(0)
        return True


class Keys:
    last = None

    def __init__(self, pins, value_when_pressed, pull=True, interval=0.02):
        self.value_when_pressed = value_when_pressed
        self.events = EventQueue()
        self.deinited = False
        Keys.last = self

    def deinit(self):
        self.deinited = True
        LOG.append("keys.deinit")


class I2C:
    def __init__(self, scl, sda, frequency=100000):
        pass


class RegisterDevice:
    """Register file with auto-increment burst reads, like an I2CDevice."""

    def __init__(self):
        self.regs = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def write_then_readinto(self, out, buf):
        reg = out[0]
        for i in range(len(buf)):
            buf[i] = self.regs.get(reg + i, 0)

    def write(self, data):
        self.regs[data[0]] = data[1]

    def set_burst(self, status, gyro, accel):
        self.regs[0x1E] = status
        raw = struct.pack("<hhhhhh", *(tuple(gyro) + tuple(accel)))
        for i, b in enumerate(raw):
            self.regs[0x22 + i] = b


class _Consts:
    pass


def _consts(*names):
    c = _Consts()
    for n in names:
        setattr(c, n, n)
    return c


class LSM6DSOX:
    last = None

    def __init__(self, i2c, address=0x6A):
        self.address = address
        self.i2c_device = RegisterDevice()
        self.i2c_device.regs[0x18] = 0xE1  # driver leaves reserved bit 0 set
        self.gyro_range = None
        self.accelerometer_range = None
        self.accelerometer_data_rate = None
        self.gyro_data_rate = None
        LSM6DSOX.last = self

    @property
    def acceleration(self):
        return (0.0, 0.0, 9.80665)

    @property
    def gyro(self):
        return (0.0, 0.0, 0.0)


class PinAlarm:
    def __init__(self, pin, value, edge=False, pull=False):
        self.pin = pin
        self.value = value
        self.edge = edge
        self.pull = pull


class AlarmModule(types.ModuleType):
    """``alarm`` stand-in: records the deep-sleep request instead of sleeping."""

    def __init__(self):
        super().__init__("alarm")
        self.wake_alarm = None
        self.slept_with = None
        self.pin = _module("alarm.pin", PinAlarm=PinAlarm)

    def exit_and_deep_sleep_until_alarms(self, *alarms):
        self.slept_with = alarms
        LOG.append("deep_sleep")


def install(monkeypatch):
    """Install the stand-ins into sys.modules for the duration of a test."""
    del LOG[:]
    pin = types.SimpleNamespace(**{"GPIO%d" % i: Pin("GPIO%d" % i) for i in range(30)})
    nvm = bytearray(256)
    alarm = AlarmModule()
    modules = {
        "alarm": alarm,
        "alarm.pin": alarm.pin,
        "supervisor": _module(
            "supervisor",
            RunReason=types.SimpleNamespace(STARTUP="startup", AUTO_RELOAD="auto_reload"),
            runtime=types.SimpleNamespace(run_reason="startup"),
        ),
        "digitalio": _module("digitalio", DigitalInOut=DigitalInOut, Pull=types.SimpleNamespace(UP="up", DOWN="down")),
        "analogio": _module("analogio", AnalogIn=AnalogIn),
        "audiobusio": _module("audiobusio", I2SOut=I2SOut),
        "audiomixer": _module("audiomixer", Mixer=Mixer),
        "audiomp3": _module("audiomp3", MP3Decoder=MP3Decoder),
        "audiocore": _module("audiocore", WaveFile=WaveFile, RawSample=RawSample),
        "synthio": _module("synthio", Synthesizer=Synthesizer, Note=Note, Envelope=Envelope),
        "keypad": _module("keypad", Keys=Keys, Event=Event),
        "busio": _module("busio", I2C=I2C),
        "microcontroller": _module(
            "microcontroller", pin=pin, nvm=nvm, cpu=types.SimpleNamespace(uid=bytes(range(8)), frequency=125000000)
        ),
        "board": _module("board", board_id="raspberry_pi_pico"),
        "adafruit_lsm6ds": _module(
            "adafruit_lsm6ds",
            Rate=_consts("RATE_104_HZ", "RATE_208_HZ", "RATE_416_HZ", "RATE_833_HZ", "RATE_1_66K_HZ"),
            GyroRange=_consts("RANGE_125_DPS", "RANGE_250_DPS", "RANGE_500_DPS", "RANGE_1000_DPS", "RANGE_2000_DPS"),
            AccelRange=_consts("RANGE_2G", "RANGE_4G", "RANGE_8G", "RANGE_16G"),
        ),
        "adafruit_lsm6ds.lsm6dsox": _module("adafruit_lsm6ds.lsm6dsox", LSM6DSOX=LSM6DSOX),
    }
    for name, mod in modules.items():
        monkeypatch.setitem(sys.modules, name, mod)
    return modules
