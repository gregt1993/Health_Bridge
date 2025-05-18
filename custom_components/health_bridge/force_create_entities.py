"""
Health Bridge Force Entity Creation Script

This script directly creates Health Bridge entities in Home Assistant.
"""

import logging
import voluptuous as vol
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

ENTITY_SERVICE_SCHEMA = vol.Schema({
    vol.Optional("user_id", default="default_user"): cv.string,
    vol.Optional("metrics", default=None): vol.Any(None, dict),
})

def get_metric_attributes_map():
    """Get the metric attributes map from const to avoid circular imports."""
    from .const import METRIC_ATTRIBUTES_MAP
    return METRIC_ATTRIBUTES_MAP

def get_domain():
    """Get the domain from const to avoid circular imports."""
    from .const import DOMAIN
    return DOMAIN

async def async_setup_services(hass: HomeAssistant):
    """Set up services for Health Bridge integration."""
    DOMAIN = get_domain()
    METRIC_ATTRIBUTES_MAP = get_metric_attributes_map()
    
    @callback
    async def create_entities(call: ServiceCall):
        """Service to force creation of Health Bridge entities."""
        user_id = call.data.get("user_id", "default_user")
        metrics = call.data.get("metrics")
        
        _LOGGER.info(f"Force creating entities for user {user_id}")
        
        # Create notification
        hass.bus.async_fire(
            "persistent_notification.create",
            {
                "message": f"Starting force entity creation for user {user_id}",
                "title": "Health Bridge - Entity Creation",
                "notification_id": "health_bridge_force_create",
            },
        )
        
        # If no metrics specified, create all standard metrics
        if not metrics:
            metrics = {}
            for metric_name in METRIC_ATTRIBUTES_MAP:
                # Skip test_connection as it's not a real metric
                if metric_name == "test_connection":
                    continue
                metrics[metric_name] = [{"value": 0}]
        
        # Get the entity registry
        registry = er.async_get(hass)
        created_entities = []
        
        # Create or update each entity
        for metric_name, datapoints in metrics.items():
            if not isinstance(datapoints, list) or not datapoints:
                datapoints = [{"value": 0}]
                
            value = datapoints[0].get("value", 0)
            
            # Get attributes for this metric
            attributes = METRIC_ATTRIBUTES_MAP.get(metric_name, {})
            
            # Create unique ID and object ID
            unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
            object_id = f"{metric_name}_{user_id}"
            
            # Format value for sleep duration
            if metric_name == "sleep_duration" and value is not None:
                hours = int(value)
                minutes = int(round((value - hours) * 60))
                formatted_value = f"{hours}h {minutes}m"
            else:
                formatted_value = value
            
            try:
                # Register the entity
                entity_entry = registry.async_get_or_create(
                    domain="sensor",
                    platform=DOMAIN,
                    unique_id=unique_id,
                    suggested_object_id=object_id,
                )
                
                # Set the state with attributes
                friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
                hass.states.async_set(
                    entity_entry.entity_id,
                    formatted_value,
                    {
                        "friendly_name": friendly_name,
                        "unit_of_measurement": attributes.get("unit_of_measurement"),
                        "state_class": attributes.get("state_class"),
                        "icon": attributes.get("icon"),
                    },
                )
                
                created_entities.append(entity_entry.entity_id)
                _LOGGER.info(f"Created/updated entity {entity_entry.entity_id}")
            except Exception as e:
                _LOGGER.error(f"Error creating entity {metric_name}: {str(e)}")
        
        # Create success notification
        entities_str = "\n".join(created_entities)
        hass.bus.async_fire(
            "persistent_notification.create",
            {
                "message": f"Successfully created/updated {len(created_entities)} entities:\n\n{entities_str}",
                "title": "Health Bridge - Entity Creation Complete",
                "notification_id": "health_bridge_force_create_complete",
            },
        )
    
    # Register the service
    hass.services.async_register(
        DOMAIN, "create_entities", create_entities, schema=ENTITY_SERVICE_SCHEMA
    )
    
    return True

async def async_unregister_services(hass):
    """Unregister Health Bridge services."""
    DOMAIN = get_domain()
    hass.services.async_remove(DOMAIN, "create_entities")