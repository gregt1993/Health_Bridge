"""Config flow for Health Bridge integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# New option keys
CONF_NUTRIENT_MASS_UNIT = "nutrient_mass_unit"   # "g" or "oz"
CONF_WATER_VOLUME_UNIT = "water_volume_unit"     # "mL" or "fl_oz"

DEFAULT_NUTRIENT_MASS_UNIT = "g"
DEFAULT_WATER_VOLUME_UNIT = "mL"


class HealthBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Health Bridge."""
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]

            await self.async_set_unique_id(token)
            self._abort_if_unique_id_configured(updates={CONF_TOKEN: token})

            # Create the config entry; options can be set/changed later
            return self.async_create_entry(
                title="Health Bridge",
                data={CONF_TOKEN: token},
                options={
                    CONF_NUTRIENT_MASS_UNIT: DEFAULT_NUTRIENT_MASS_UNIT,
                    CONF_WATER_VOLUME_UNIT: DEFAULT_WATER_VOLUME_UNIT,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            # Save options
            return self.async_create_entry(title="", data=user_input)

        # Current options (with defaults)
        cur = self.config_entry.options
        mass_unit = cur.get(CONF_NUTRIENT_MASS_UNIT, DEFAULT_NUTRIENT_MASS_UNIT)
        vol_unit = cur.get(CONF_WATER_VOLUME_UNIT, DEFAULT_WATER_VOLUME_UNIT)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NUTRIENT_MASS_UNIT, default=mass_unit
                    ): vol.In(["g", "oz"]),
                    vol.Required(
                        CONF_WATER_VOLUME_UNIT, default=vol_unit
                    ): vol.In(["mL", "fl_oz"]),
                }
            ),
        )
