

from datetime import timedelta
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
    ConfigEntryNotReady
)
from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=5)


from homeassistant.core import callback

from .tp_net import TpNet
from .cordinator import MyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    # The hub is loaded from the associated hass.data entry that was created in the
    # __init__.async_setup_entry function
    tp_net = hass.data[DOMAIN][config_entry.entry_id]
    # This will call Entity.set_sleep_timer(sleep_time=VALUE)
    # Add all entities to HA
    coordinator = MyCoordinator(hass, tp_net)

    await coordinator.async_refresh()

    async_add_entities([MySelect(coordinator, tp_net)])



class MySelect(CoordinatorEntity, SelectEntity):
    # Implement one of these methods.
    _attr_has_entity_name = True


    async def async_select_option(self, option: str) -> None:
        await self.tp_net.set(["PRESET",option])

    @property
    def unique_id(self):
        """Name of the entity."""
        return "My Switch"

    @property
    def name(self):
        """Name of the entity."""
        return "Preset"
    

    def __init__(self, coordinator, tp_net: TpNet):
        self._attr_options = ["1","2","3","4","5"]
        self.tp_net = tp_net
        self._attr_current_option = None

        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_option = self.coordinator.data["PRESET"][0]
        self.async_write_ha_state()

