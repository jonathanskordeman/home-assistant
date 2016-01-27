""" Support for DS18B20 One Wire Sensors"""
from glob import glob
import logging
import os
import time
from homeassistant.const import TEMP_CELCIUS, STATE_UNKNOWN
from homeassistant.helpers.entity import Entity


BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_FOLDERS = glob(os.path.join(BASE_DIR, '28*'))
SENSOR_IDS = []
DEVICE_FILES = []
for device_folder in DEVICE_FOLDERS:
    SENSOR_IDS.append(os.path.split(device_folder)[1])
    DEVICE_FILES.append(os.path.join(device_folder, 'w1_slave'))

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the one wire Sensors"""

    if DEVICE_FILES == []:
        _LOGGER.error('No onewire sensor found.')
        _LOGGER.error('Check if dtoverlay=w1-gpio,gpiopin=4.')
        _LOGGER.error('is in your /boot/config.txt and')
        _LOGGER.error('the correct gpiopin number is set.')
        return

    devs = []
    names = SENSOR_IDS

    for key in config.keys():
        if key == "names":
            # only one name given
            if isinstance(config['names'], str):
                names = [config['names']]
            # map names and sensors in given order
            elif isinstance(config['names'], list):
                names = config['names']
            # map names to ids.
            elif isinstance(config['names'], dict):
                names = []
                for sensor_id in SENSOR_IDS:
                    names.append(config['names'].get(sensor_id, sensor_id))
    for device_file, name in zip(DEVICE_FILES, names):
        devs.append(OneWire(name, device_file))
    add_devices(devs)


class OneWire(Entity):
    """ A Dallas 1 Wire Sensor"""

    def __init__(self, name, device_file):
        self._name = name
        self._device_file = device_file
        self._state = STATE_UNKNOWN
        self.update()

    def _read_temp_raw(self):
        """ read the temperature as it is returned by the sensor"""
        ds_device_file = open(self._device_file, 'r')
        lines = ds_device_file.readlines()
        ds_device_file.close()
        return lines

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """ return temperature in unit_of_measurement"""
        return self._state

    @property
    def unit_of_measurement(self):
        return TEMP_CELCIUS

    def update(self):
        lines = self._read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp = float(temp_string) / 1000.0
            self._state = temp