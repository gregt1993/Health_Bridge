"""Health Bridge sensor platform."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the Health Bridge sensor platform."""
    # This will handle YAML configuration
    # No need to do anything here since entities are created dynamically via webhook
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Health Bridge sensor from a config entry."""
    # This will be called when a config entry is loaded
    # We'll register a dispatcher to add entities when webhook data arrives
    
    @callback
    def async_add_sensor(user_id: str, metric_name: str, attributes: Dict[str, Any], latest_value: StateType):
        """Add a sensor entity."""
        entity = HealthBridgeSensor(
            user_id=user_id,
            metric_name=metric_name,
            attributes=attributes,
            value=latest_value,
            config_entry_id=entry.entry_id,
            hass=hass
        )
        async_add_entities([entity], True)
        
        # Ensure the entity has a state with correct friendly name after adding
        entity_id = f"sensor.{metric_name}_{user_id}"
        friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
        
        # Check if state exists but might be missing attributes
        current_state = hass.states.get(entity_id)
        if current_state:
            # Update with friendly name explicitly
            hass.states.async_set(
                entity_id,
                current_state.state,
                {
                    **current_state.attributes,
                    "friendly_name": friendly_name,
                    "unit_of_measurement": attributes.get("unit_of_measurement"),
                    "state_class": attributes.get("state_class"),
                    "icon": attributes.get("icon"),
                }
            )
            _LOGGER.debug(f"Health Bridge: Explicitly set friendly_name for new entity {entity_id}")
    
    # Store the add_sensor callback in hass.data for the webhook to use
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
        hass: Optional[HomeAssistant] = None
    ):
        """Initialize the sensor."""
        self._user_id = user_id
        self._metric_name = metric_name
        self._config_entry_id = config_entry_id
        self._value = value
        self._hass = hass
        
        # Use attributes from the map
        self._attr_unit_of_measurement = attributes.get("unit_of_measurement")
        self._attr_state_class = attributes.get("state_class")
        self._attr_icon = attributes.get("icon")
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        
        # Set name explicitly
        self._attr_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
        _LOGGER.debug(f"Health Bridge: Initialized sensor with name: {self._attr_name}")
        
        # Set device information
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
        """Return the state of the sensor."""
        if self._metric_name == "sleep_duration":
            hours = int(self._value)
            minutes = int(round((self._value - hours) * 60))
            return f"{hours}h {minutes}m"
        return self._value
    
    @property
    def name(self) -> str:
        """Return the name of the entity."""
        # Ensure the name is always the correct format
        return f"{self._metric_name.replace('_', ' ').title()} ({self._user_id})"
    
    @callback
    def update_state(self, value: StateType) -> None:
        """Update the sensor's state."""
        self._value = value
        
        # Check if the state exists but is missing the friendly name
        if self._hass and hasattr(self, 'entity_id') and self.entity_id:
            current_state = self._hass.states.get(self.entity_id)
            if current_state and ('friendly_name' not in current_state.attributes or 
                                 current_state.attributes.get('friendly_name') != self.name):
                # Explicitly update the state with the correct friendly name
                self._hass.states.async_set(
                    self.entity_id,
                    self.native_value,
                    {
                        **current_state.attributes,
                        "friendly_name": self.name,
                        "unit_of_measurement": self._attr_unit_of_measurement,
                        "state_class": self._attr_state_class,
                        "icon": self._attr_icon,
                    }
                )
                _LOGGER.debug(f"Health Bridge: Fixed missing/incorrect friendly_name for {self.entity_id}")
        
        # Call standard update
        self.async_write_ha_state()