"""Config flow for Health Bridge integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HealthBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Health Bridge."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the token (you could add more validation if needed)
            token = user_input[CONF_TOKEN]
            
            # Use the token as the unique ID
            await self.async_set_unique_id(token)
            self._abort_if_unique_id_configured(
                updates={CONF_TOKEN: token}
            )
            
            # Create the config entry
            return self.async_create_entry(
                title="Health Bridge",
                data=user_input,
            )

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            errors=errors,
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TOKEN,
                        default=self.config_entry.data.get(CONF_TOKEN, ""),
                    ): str,
                }
            ),
        )