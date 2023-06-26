from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
    ConfigEntryNotReady
)
_LOGGER = logging.getLogger(__name__)

import async_timeout
from .tp_net import TpNet

class TpNetCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, tp_net: TpNet):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Tp Net",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=3),
        )
        self.tp_net = tp_net

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.debug("Refresh data from device")
        if not self.tp_net.available:
            resutl = await self.tp_net.connect()
            if not resutl:
                raise UpdateFailed("Device not aviable")
                
        try:
            async with async_timeout.timeout(10):
                await self.tp_net.get_all()
                _LOGGER.debug(f"cached data {self.tp_net.data}")
                return self.tp_net.data
        except Exception as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise err


