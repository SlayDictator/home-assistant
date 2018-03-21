"""
Support for Eurotronic CometBlue thermostats.
They are identical to the Xavax Bluetooth thermostats and others, e.g. sold by discounters.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.cometblue/
"""
import logging
from datetime import timedelta
import threading
import voluptuous as vol

from sys import stderr

from homeassistant.components.climate import (
    ClimateDevice,
    PLATFORM_SCHEMA,
    STATE_ON,
    STATE_OFF,
    STATE_AUTO,
    STATE_HEAT,
    STATE_COOL,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_HIGH,
    SUPPORT_TARGET_TEMPERATURE_LOW,
    SUPPORT_OPERATION_MODE)
from homeassistant.const import (
    CONF_NAME,
    CONF_MAC,
    CONF_PIN,
    CONF_DEVICES,
    TEMP_CELSIUS,
    ATTR_TEMPERATURE,
    PRECISION_HALVES)

import homeassistant.helpers.config_validation as cv

#REQUIREMENTS = ['cometblue']

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(10)

SCAN_INTERVAL = timedelta(seconds=300)

STATE_MANUAL = 'manual'

ATTR_STATE_WINDOW_OPEN = 'window_open'
ATTR_STATE_VALVE = 'valve'
ATTR_STATE_LOCKED = 'is_locked'
ATTR_STATE_LOW_BAT = 'low_battery'

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_PIN, default=0): cv.positive_int,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES):
        vol.Schema({cv.string: DEVICE_SCHEMA}),
})

#SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_TARGET_TEMPERATURE_HIGH | SUPPORT_TARGET_TEMPERATURE_LOW)
#SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_HIGH | SUPPORT_TARGET_TEMPERATURE_LOW)
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE)

from cometblue import device as cometblue_dev

gatt_mgr = None

def setup_platform(hass, config, add_devices, discovery_info=None):
    global gatt_mgr

    gatt_mgr = cometblue_dev.CometBlueManager('hci0')

    class ManagerThread(threading.Thread):
        def run(self):
            gatt_mgr.run()

    ManagerThread().start()

    devices = []

    for name, device_cfg in config[CONF_DEVICES].items():
        dev = CometBlueThermostat(device_cfg[CONF_MAC], name, device_cfg[CONF_PIN])
        devices.append(dev)

    add_devices(devices)

class CometBlueThermostat(ClimateDevice):
    """Representation of a CometBlue thermostat."""

    def __init__(self, _mac, _name, _pin = None):
        """Initialize the thermostat."""

        global gatt_mgr

        self._mac = _mac
        self._name = _name
        #self._pin = _pin
        self._thermostat = cometblue_dev.CometBlue(_mac, gatt_mgr, _pin)
        self._current_temperature = None
        self._target_temperature = None

        #self._thermostat.connect()
        self.update()

    #def __del__(self):
    #    self._thermostat.disconnect()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    #@property
    #def available(self) -> bool:
    #    """Return if thermostat is available."""
    #    return self.current_operation is not None

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Return cometblue's precision 0.5."""
        return PRECISION_HALVES

    @property
    def current_temperature(self):
        """Return current temperature"""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temperature = temperature

    #@property
    #def current_operation(self):
    #    """Return the current operation mode."""
    #    if self._thermostat.mode < 0:
    #        return None
    #    return self.modes[self._thermostat.mode]

    #@property
    #def operation_list(self):
    #    """Return the list of available operation modes."""
    #    return [x for x in self.modes.values()]

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        #return self._thermostat.min_temp
        return 8.0

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        #return self._thermostat.max_temp
        return 28.0

    #@property
    #def device_state_attributes(self):
    #    """Return the device specific state attributes."""
    #    dev_specific = {
    #        ATTR_STATE_LOCKED: self._thermostat.locked,
    #        ATTR_STATE_LOW_BAT: self._thermostat.low_battery,
    #        ATTR_STATE_WINDOW_OPEN: self._thermostat.window_open,
    #    }

    #    return dev_specific

    def update(self):
        """Update the data from the thermostat."""

        _LOGGER.info("Update called {}".format(self._mac))
        temps = {
            'manual_temp': self.target_temperature,
            #'manual_temp': self,
            'target_temp_l': None,
            'target_temp_h': None,
            'offset_temp': None,
            'window_open_detection': None,
            'window_open_minutes': None
        }
        _LOGGER.info("To bet set values {}".format(str(temps)))
        #self._thermostat.connect()
        #self._thermostat.attempt_to_get_ready()
        with self._thermostat as device:
            self._thermostat.set_temperatures(temps)
            temps = self._thermostat.get_temperatures()
        #self._thermostat.disconnect()
        _LOGGER.info("Received values {}".format(str(temps)))
        self._current_temperature = temps['current_temp']
        self._target_temperature = temps['manual_temp']
