"""Health Bridge sensor platform."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the Health Bridge sensor platform (YAML)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Health Bridge sensors from a config entry."""
    @callback
    def async_add_sensor(user_id: str, metric_name: str, attributes: Dict[str, Any], latest_value: StateType):
        """Add a sensor entity (runtime object) and set initial state attributes."""
        entity = HealthBridgeSensor(
            user_id=user_id,
            metric_name=metric_name,
            attributes=attributes,
            value=latest_value,
            config_entry_id=entry.entry_id,
            hass=hass
        )
        async_add_entities([entity], True)

        # Ensure attributes like friendly_name/units are visible on first render
        entity_id = f"sensor.{metric_name}_{user_id}"
        friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"

        current_state = hass.states.get(entity_id)
        if current_state:
            hass.states.async_set(
                entity_id,
                current_state.state,
                {
                    **current_state.attributes,
                    "friendly_name": friendly_name,
                    # mirror native field or fall back to legacy so UI shows units
                    "unit_of_measurement": attributes.get("native_unit_of_measurement") or attributes.get("unit_of_measurement"),
                    "state_class": attributes.get("state_class"),
                    "icon": attributes.get("icon"),
                }
            )
            _LOGGER.debug("Health Bridge: Explicitly set friendly_name/units for %s", entity_id)

    # Make callbacks available to the webhook handler
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["add_sensor"] = async_add_sensor

    return True


class HealthBridgeSensor(SensorEntity):
    """Representation of a Health Bridge sensor."""

    def __init__(
        self,
        user_id: str,
        metric_name: str,
        attributes: Dict[str, Any],
        value: StateType,
        config_entry_id: str,
        hass: Optional[HomeAssistant] = None,
    ):
        self._user_id = user_id
        self._metric_name = metric_name
        self._config_entry_id = config_entry_id
        self._value = value
        self._hass = hass

        # Use **native** fields (fed from METRIC_ATTRIBUTES_MAP via webhook)
        # Fallback preserves existing custom units when native_unit isn't provided
        self._attr_native_unit_of_measurement = (
            attributes.get("native_unit_of_measurement") or attributes.get("unit_of_measurement")
        )
        self._attr_device_class = attributes.get("device_class")
        self._attr_state_class = attributes.get("state_class")
        self._attr_icon = attributes.get("icon")

        # IDs / Names
        self._attr_unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        self._attr_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
        _LOGGER.debug("Health Bridge: Initialized sensor %s", self._attr_name)

        # Device info
        device_id = f"health_bridge_{user_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Health Bridge ({user_id})",
            manufacturer="Health Bridge",
            model="Health Tracker",
            sw_version="1.0",
        )

    @property
    def native_value(self) -> StateType:
        """Return the numeric state (no string formatting)."""
        return self._value

    @property
    def name(self) -> str:
        return f"{self._metric_name.replace('_', ' ').title()} ({self._user_id})"

    @callback
    def update_state(self, value: StateType) -> None:
        """Update the sensor's state and keep friendly name/units visible."""
        self._value = value
        if self._hass and getattr(self, "entity_id", None):
            current_state = self._hass.states.get(self.entity_id)
            if current_state and (
                "friendly_name" not in current_state.attributes
                or current_state.attributes.get("friendly_name") != self.name
            ):
                self._hass.states.async_set(
                    self.entity_id,
                    self.native_value,
                    {
                        **current_state.attributes,
                        "friendly_name": self.name,
                        # already includes fallback
                        "unit_of_measurement": self._attr_native_unit_of_measurement,
                        "state_class": self._attr_state_class,
                        "icon": self._attr_icon,
                    },
                )
                _LOGGER.debug("Health Bridge: Set friendly_name/units for %s", self.entity_id)

        self.async_write_ha_state()