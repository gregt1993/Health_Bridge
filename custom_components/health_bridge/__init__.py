"""The Health Bridge integration."""
import logging
import voluptuous as vol

from homeassistant.const import CONF_TOKEN
from homeassistant.components import webhook
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import config_validation as cv
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import async_get_platforms

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TOKEN): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

class HealthBridgeSensor(SensorEntity):
    """Sensor for Health Bridge metrics."""
    
    def __init__(self, hass, config_entry_id, user_id, metric_name):
        """Initialize the sensor."""
        self.hass = hass
        self._config_entry_id = config_entry_id
        self._user_id = user_id
        self.metric_name = metric_name
        self._attr_native_value = None
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        
        # Set name
        self._attr_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
        
        # Get metric-specific attributes
        metric_attrs = self._get_metric_attributes(metric_name)
        self._attr_native_unit_of_measurement = metric_attrs.get("unit_of_measurement")
        self._attr_state_class = metric_attrs.get("state_class")
        self._attr_icon = metric_attrs.get("icon")
        
        # This is needed to avoid the error, but we'll set it properly later
        self.entity_id = f"sensor.{metric_name}_{user_id}"
    
    def _get_metric_attributes(self, metric_name):
        """Get attributes for a specific metric."""
        metric_attributes_map = {
            "steps": {"unit_of_measurement": "steps", "state_class": SensorStateClass.TOTAL_INCREASING, "icon": "mdi:walk"},
            "heart_rate": {"unit_of_measurement": "bpm", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:heart-pulse"},
            "active_calories": {"unit_of_measurement": "kcal", "state_class": SensorStateClass.TOTAL_INCREASING, "icon": "mdi:fire"},
            "resting_heart_rate": {"unit_of_measurement": "bpm", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:heart-pulse"},
            "sleep_duration": {"unit_of_measurement": "of sleep", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:sleep"},
            "distance": {"unit_of_measurement": "m", "state_class": SensorStateClass.TOTAL_INCREASING, "icon": "mdi:map-marker-distance"},
            "oxygen_saturation": {"unit_of_measurement": "%", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:oxygen-mask"},
            "respiratory_rate": {"unit_of_measurement": "breaths/min", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:lungs"},
            "body_mass": {"unit_of_measurement": "kg", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:weight-kilogram"},
            "body_fat_percentage": {"unit_of_measurement": "%", "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:body-percent"},
            "test_connection": {"unit_of_measurement": None, "state_class": None, "icon": "mdi:check-circle"},
        }
        return metric_attributes_map.get(metric_name, {})
    
    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, f"health_bridge_{self._user_id}")
            },
            "manufacturer": "Health Bridge",
            "model": "Health Tracker",
            "name": f"Health Bridge ({self._user_id})",
            "sw_version": "1.0",
        }
    
    def update_state(self, value):
        """Update the sensor state."""
        if self.metric_name == "sleep_duration":
            hours = int(value)
            minutes = int(round((value - hours) * 60))
            self._attr_native_value = f"{hours}h {minutes}m"
        else:
            self._attr_native_value = value
        
        # Make sure _attr_name is always set
        if not hasattr(self, '_attr_name') or not self._attr_name:
            self._attr_name = f"{self.metric_name.replace('_', ' ').title()} ({self._user_id})"
        
        # IMPORTANT: We need to directly update the state instead of using async_schedule_update_ha_state
        # since our entity isn't properly set up with a platform
        if hasattr(self, 'entity_id') and self.entity_id:
            self.hass.states.async_set(
                self.entity_id,
                self._attr_native_value,
                {
                    "friendly_name": self._attr_name,
                    "unit_of_measurement": self._attr_native_unit_of_measurement or "",
                    "state_class": self._attr_state_class or "",
                    "icon": self._attr_icon or "mdi:chart-line",
                }
            )
            _LOGGER.debug(f"Health Bridge: Set state for {self.entity_id} to {self._attr_native_value}")
        else:
            _LOGGER.error(f"Health Bridge: Cannot update state - no entity_id for {self._attr_name}")

async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up the Health Bridge component from YAML."""
    _LOGGER.debug("Health Bridge: async_setup started")
    await async_register_entity_fix_service(hass)
    if DOMAIN not in config:
        _LOGGER.debug("Health Bridge: No configuration found in configuration.yaml. Skipping YAML setup.")
        return True

    token = config[DOMAIN].get(CONF_TOKEN)
    if not token:
        _LOGGER.error("Health Bridge: Token is missing from configuration.yaml")
        return False

    # Store token for webhook use
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = token
    hass.data[DOMAIN].setdefault("entities", {})
    _LOGGER.debug("Health Bridge: Token loaded from YAML and stored in hass.data")
    
    # Set up webhook for both YAML and UI configurations
    setup_webhook(hass)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Health Bridge from a config entry."""
    _LOGGER.debug(f"Health Bridge: Setting up config entry {entry.entry_id}")
    await async_register_entity_fix_service(hass)
    # Store token for webhook use
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = entry.data[CONF_TOKEN]
    hass.data[DOMAIN]["entry_id"] = entry.entry_id
    hass.data[DOMAIN].setdefault("entities", {})
    _LOGGER.debug("Health Bridge: Token loaded from config entry and stored in hass.data")
    
    # Set up webhook
    setup_webhook(hass)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Health Bridge: Unloading config entry {entry.entry_id}")
    
    # We don't need to unregister the webhook as it's shared between all instances
    # Just remove the token associated with this entry if it matches the current one
    if DOMAIN in hass.data and entry.data[CONF_TOKEN] == hass.data[DOMAIN].get("token"):
        hass.data[DOMAIN].pop("token", None)
        
        # Note: We're intentionally not removing the webhook_registered flag
        # as we want to keep track of registration across config entries
    
    return True




async def async_register_entity_fix_service(hass):
    """Register a service to fix entity names."""
    async def fix_entity_names_service(call):
        """Service to fix Health Bridge entity names."""
        _LOGGER.info("Health Bridge: Starting entity name fix service")
        
        # Get all states
        states = hass.states.async_all()
        health_bridge_entities = []
        
        # Find all potential Health Bridge entities by pattern matching on entity_id
        for state in states:
            if state.entity_id.startswith("sensor.") and "_" in state.entity_id:
                parts = state.entity_id.split(".")
                if len(parts) == 2:
                    entity_id_parts = parts[1].split("_")
                    # Look for pattern: metric_name_user_id
                    if len(entity_id_parts) >= 2:
                        health_bridge_entities.append(state)
        
        _LOGGER.info(f"Health Bridge: Found {len(health_bridge_entities)} potential Health Bridge entities")
        
        # Process each entity
        fixed_count = 0
        for state in health_bridge_entities:
            entity_id = state.entity_id
            
            # Extract metric name and user ID from entity_id
            parts = entity_id.split(".")
            if len(parts) != 2:
                continue
                
            entity_id_parts = parts[1].split("_")
            if len(entity_id_parts) < 2:
                continue
                
            # Last part is user_id, everything before is the metric name
            user_id = entity_id_parts[-1]
            metric_name = "_".join(entity_id_parts[:-1])
            
            # Generate the friendly name
            friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
            
            # Check if friendly_name is missing or wrong
            current_friendly_name = state.attributes.get("friendly_name", "")
            if not current_friendly_name or current_friendly_name != friendly_name:
                _LOGGER.info(f"Health Bridge: Fixing entity name for {entity_id} to '{friendly_name}'")
                
                # Copy existing attributes
                attributes = dict(state.attributes)
                
                # Set friendly name
                attributes["friendly_name"] = friendly_name
                
                
                
                # Update the state with the same value but new attributes
                hass.states.async_set(
                    entity_id,
                    state.state,
                    attributes
                )
                fixed_count += 1
        
        # Create notification with results
        message = f"Fixed {fixed_count} Health Bridge entity names."
        hass.components.persistent_notification.async_create(
            message,
            title="Health Bridge Entity Fix",
            notification_id="health_bridge_entity_fix"
        )
        
        _LOGGER.info(f"Health Bridge: Fixed {fixed_count} entity names")

    # Register the service
    hass.services.async_register(
        DOMAIN, 
        "fix_entity_names", 
        fix_entity_names_service
    )
    _LOGGER.info("Health Bridge: Registered fix_entity_names service")



def setup_webhook(hass: HomeAssistant) -> None:
    """Set up webhook for Health Bridge."""
    
    # There's no direct way to check if a webhook is registered
    # We'll use a flag in hass.data to prevent duplicate registrations
    if hass.data.get(DOMAIN, {}).get("webhook_registered"):
        _LOGGER.debug("Health Bridge: Webhook already registered")
        return
    
    _LOGGER.debug("Health Bridge: Registering webhook")
    
    async def handle_webhook(hass: HomeAssistant, webhook_id: str, request):
        """Handle webhook callback."""
        _LOGGER.debug(f"Health Bridge: Webhook received for webhook_id: {webhook_id}")

        try:
            data = await request.json()
            _LOGGER.info(f"Health Bridge: Received data: {data}")

            stored_token = hass.data.get(DOMAIN, {}).get("token")
            received_token = data.get("token")

            health_data = data.get("data", {})
            if "test_connection" in health_data:
                _LOGGER.info("Health Bridge: Received test connection payload. Firing success notification.")
                hass.bus.async_fire(
                    "persistent_notification.create",
                    {
                        "message": "Health Bridge connection successful!",
                        "title": "Health Bridge",
                        "notification_id": "health_bridge_test_success",
                    },
                )
                return None

            user_id = data.get("user_id", "unknown")
            health_data = data.get("data", {})

            if not health_data:
                _LOGGER.debug(f"Health Bridge: Received webhook with no health data for webhook_id: {webhook_id}")
                return None

            # Get the config entry ID
            config_entry_id = hass.data.get(DOMAIN, {}).get("entry_id")
            
            # Get or initialize the user's entities dictionary
            user_entities = hass.data[DOMAIN].setdefault("entities", {}).setdefault(user_id, {})
            
            # Create or get device first (for all entities)
            device_registry = dr.async_get(hass)
            device = device_registry.async_get_or_create(
                config_entry_id=config_entry_id,
                identifiers={(DOMAIN, f"health_bridge_{user_id}")},
                name=f"Health Bridge ({user_id})",
                manufacturer="Health Bridge",
                model="Health Tracker",
                sw_version="1.0",
            )
            
            for metric_name, datapoints in health_data.items():
                if not datapoints:
                    _LOGGER.debug(f"Health Bridge: Metric '{metric_name}' has no datapoints for webhook_id: {webhook_id}. Skipping.")
                    continue

                latest_value = datapoints[-1].get("value")
                if latest_value is None:
                    _LOGGER.debug(f"Health Bridge: Metric '{metric_name}' missing latest value. Skipping update.")
                    continue

                unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
                suggested_object_id = f"{metric_name}_{user_id}"
                entity_id = f"sensor.{suggested_object_id}"
                
                # Check if we already have an entity for this metric
                if metric_name in user_entities:
                    # Update the existing entity
                    _LOGGER.debug(f"Health Bridge: Using existing entity for {metric_name}")
                    entity = user_entities[metric_name]
                else:
                    # Create a new entity
                    _LOGGER.debug(f"Health Bridge: Creating new entity for metric {metric_name}, user {user_id}")
                    entity = HealthBridgeSensor(hass, config_entry_id, user_id, metric_name)
                    
                    # Get the entity registry
                    entity_registry = er.async_get(hass)
                    
                    # Register the entity in the registry
                    entity_entry = entity_registry.async_get_or_create(
                        domain="sensor",
                        platform=DOMAIN,
                        unique_id=unique_id,
                        suggested_object_id=suggested_object_id,
                        device_id=device.id,
                        original_name=f"{metric_name.replace('_', ' ').title()} ({user_id})",
                    )
                    
                    # Set the entity_id correctly on our entity object
                    entity.entity_id = entity_entry.entity_id
                    _LOGGER.debug(f"Health Bridge: Registered entity with id {entity.entity_id}")
                    
                    # Add entity to our tracking
                    user_entities[metric_name] = entity
                
                # Now update the entity state
                entity.update_state(latest_value)
                
                # Ensure the state is properly set with all attributes
                if hasattr(entity, 'entity_id') and entity.entity_id:
                    friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
                    hass.states.async_set(
                        entity.entity_id,
                        entity._attr_native_value if hasattr(entity, '_attr_native_value') else latest_value,
                        {
                            "friendly_name": friendly_name,
                            "unit_of_measurement": entity._attr_native_unit_of_measurement if hasattr(entity, '_attr_native_unit_of_measurement') else None,
                            "state_class": entity._attr_state_class if hasattr(entity, '_attr_state_class') else None,
                            "icon": entity._attr_icon if hasattr(entity, '_attr_icon') else None,
                        }
                    )
                    _LOGGER.debug(f"Health Bridge: Explicitly set friendly_name for {entity.entity_id}")

            _LOGGER.info("Health Bridge: Webhook processed successfully.")
            return None

        except Exception as e:
            _LOGGER.error(f"Health Bridge: Error processing webhook: {e}", exc_info=True)
            return None

    webhook.async_register(
        hass,
        DOMAIN,
        "Health Bridge",
        "health_bridge",
        handle_webhook
    )

    # Mark webhook as registered
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["webhook_registered"] = True

    _LOGGER.info("Health Bridge webhook registered with ID: health_bridge")