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

class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, my_api: TpNet):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=5),
        )
        self.my_api = my_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.debug("Refresh data from device")
        if not self.my_api.available:
            resutl = await self.my_api.connect()
            if not resutl:
                raise UpdateFailed("Device not aviable")
                
        try:
            async with async_timeout.timeout(10):
                await self.my_api.get_all()
                _LOGGER.info(f"cached data {self.my_api.data}")
                return self.my_api.data
        except Exception as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise err


