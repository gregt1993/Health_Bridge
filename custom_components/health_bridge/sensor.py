"""Health Bridge sensor platform (unit-safe, enum-safe)."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.const import UnitOfTime

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the Health Bridge sensor platform (YAML flow)."""
    # Entities are created dynamically via webhook/services; nothing to do here.
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Health Bridge sensors from a config entry."""

    # index of live entity objects so webhook can update without poking hass.states
    hass.data.setdefault(DOMAIN, {})
    entity_index: Dict[str, Dict[str, "HealthBridgeSensor"]] = hass.data[DOMAIN].setdefault(
        "entity_objs", {}
    )

    @callback
    def async_add_sensor(
        user_id: str, metric_name: str, attributes: Dict[str, Any], latest_value: StateType
    ):
        """Create a sensor entity for a metric/user."""
        entity = HealthBridgeSensor(
            user_id=user_id,
            metric_name=metric_name,
            attributes=attributes,
            value=latest_value,
            config_entry_id=entry.entry_id,
        )
        async_add_entities([entity], True)
        # index it for fast updates
        entity_index.setdefault(user_id, {})[metric_name] = entity

    @callback
    def update_sensor(user_id: str, metric_name: str, value: StateType):
        """Update an existing sensor entity if present."""
        ent = entity_index.get(user_id, {}).get(metric_name)
        if ent:
            ent.update_state(value)
        else:
            _LOGGER.debug(
                "Health Bridge: update_sensor skipped for %s/%s (entity not created yet)",
                user_id,
                metric_name,
            )

    # expose callbacks for webhook/services
    hass.data[DOMAIN]["add_sensor"] = async_add_sensor
    hass.data[DOMAIN]["update_sensor"] = update_sensor
    return True


class HealthBridgeSensor(SensorEntity):
    """Representation of a Health Bridge sensor."""

    _attr_has_entity_name = True  # Let HA manage friendly_name

    def __init__(
        self,
        user_id: str,
        metric_name: str,
        attributes: Dict[str, Any],
        value: StateType,
        config_entry_id: str,
    ):
        self._user_id = user_id
        self._metric_name = metric_name
        self._config_entry_id = config_entry_id
        self._value = value
    
        
        # --- Coerce device_class/state_class (strings from const.py -> Enums), safe on older HA
        dc = attributes.get("device_class")
        sc = attributes.get("state_class")

        if isinstance(dc, str):
            try:
                self._attr_device_class = SensorDeviceClass(dc)
            except Exception:
                self._attr_device_class = None
        else:
            self._attr_device_class = dc  # already enum or None

        if isinstance(sc, str):
            try:
                self._attr_state_class = SensorStateClass(sc)
            except Exception:
                self._attr_state_class = None
        else:
            self._attr_state_class = sc  # already enum or None
        # --- end coercion

        # Use native unit so HA can auto-convert to user settings.
        self._attr_native_unit_of_measurement = (
            attributes.get("native_unit_of_measurement")
            or attributes.get("unit_of_measurement")
        )
        self._attr_icon = attributes.get("icon")

        # Normalize sleep_duration to numeric minutes and set proper device class/units.
        if self._metric_name == "sleep_duration":
            # If HA doesn't recognize "duration", keep None; it's OK. Units still show.
            try:
                self._attr_device_class = self._attr_device_class or SensorDeviceClass.DURATION
            except Exception:
                pass
            self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
            if isinstance(self._value, (int, float)):
                # If upstream sends hours (float), convert once to minutes
                self._value = int(round(float(self._value) * 60))

        # Identity (stable IDs)
        self._attr_unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        self._attr_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"

        # Device grouping
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
        """Return the native (device) value. No human formatting here."""
        return self._value

    @callback
    def update_state(self, value: StateType) -> None:
        if self._metric_name == "sleep_duration" and isinstance(value, (int, float)):
            value = int(round(float(value) * 60))
        elif self._metric_name == "walking_speed":
            try:
                value = float(value)
            except (TypeError, ValueError):
                _LOGGER.debug("Health Bridge: walking_speed update received non-numeric %r", value)
        self._value = value
        self.async_write_ha_state()
