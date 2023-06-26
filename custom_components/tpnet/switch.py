
from ast import While
import asyncio
from datetime import timedelta
import logging
from typing import cast
from homeassistant.components.switch import SwitchEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.core import callback


from .const import DOMAIN, SERVICE_SET_PRESET

SCAN_INTERVAL = timedelta(seconds=5)


import voluptuous as vol

from .tp_net import TpNet
from .cordinator import TpNetCoordinator

_LOGGER = logging.getLogger(__name__)



async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    # The hub is loaded from the associated hass.data entry that was created in the
    # __init__.async_setup_entry function
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    coordinator = cast(TpNetCoordinator, coordinator)

    async_add_entities([DevicePower(coordinator, coordinator.tp_net)])
       
class DevicePower(CoordinatorEntity, SwitchEntity):
    # Implement one of these methods.
    _attr_has_entity_name = True
    _attr_assumed_state = False

    @property
    def unique_id(self):
        """Name of the entity."""
        return "My Switch"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data == None:
            return
        self._attr_is_on = self.coordinator.data["POWER"][0] == "ON"
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return "power"

    def __init__(self, coordinator, tp_net: TpNet):

        super().__init__(coordinator)
        self.tp_net = tp_net
        
    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.tp_net.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.tp_net.turn_off()
        await self.coordinator.async_request_refresh()




