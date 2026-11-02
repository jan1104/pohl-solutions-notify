"""Single local instance, configured through the HA integration UI."""
import probatio as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN


class AlarmSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Pohl Solutions Alarm Notify", data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("site_id", default="LW20"): selector.TextSelector(),
        }))
