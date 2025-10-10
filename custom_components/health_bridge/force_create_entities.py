"""
Health Bridge Force Entity Creation Script

Creates Health Bridge entities via the sensor platform callbacks,
without writing state directly (unit-safe).
"""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

ENTITY_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("user_id", default="default_user"): cv.string,
        vol.Optional("metrics", default=None): vol.Any(None, dict),
    }
)


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

        _LOGGER.info("Health Bridge: Force creating entities for user %s", user_id)

        # Notify start
        hass.components.persistent_notification.async_create(
            f"Starting force entity creation for user {user_id}",
            title="Health Bridge - Entity Creation",
            notification_id="health_bridge_force_create",
        )

        # Fallback to all known metrics (except test_connection)
        if not metrics:
            metrics = {}
            for metric_name in METRIC_ATTRIBUTES_MAP:
                if metric_name == "test_connection":
                    continue
                metrics[metric_name] = [{"value": 0}]

        # Callbacks from sensor platform
        add = hass.data.get(DOMAIN, {}).get("add_sensor")
        update = hass.data.get(DOMAIN, {}).get("update_sensor")

        if not add:
            _LOGGER.warning(
                "Health Bridge: add_sensor callback not available yet; "
                "make sure the sensor platform is set up."
            )

        entity_reg = er.async_get(hass)
        created_entities: list[str] = []

        for metric_name, datapoints in metrics.items():
            try:
                if not isinstance(datapoints, list) or not datapoints:
                    datapoints = [{"value": 0}]
                value = datapoints[0].get("value", 0)

                # Build native attributes for the metric
                attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {}).copy()
                if (
                    "native_unit_of_measurement" not in attrs
                    and "unit_of_measurement" in attrs
                ):
                    # Back-compat: map legacy key to native
                    attrs["native_unit_of_measurement"] = attrs["unit_of_measurement"]

                unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
                suggested_object_id = f"{metric_name}_{user_id}"

                # Reserve a stable entity_id in the registry (idempotent)
                entry = entity_reg.async_get_or_create(
                    domain="sensor",
                    platform=DOMAIN,
                    unique_id=unique_id,
                    suggested_object_id=suggested_object_id,
                    # no state writes here
                )
                created_entities.append(entry.entity_id)

                # Create the runtime entity via the sensor platform factory
                if add:
                    add(user_id, metric_name, attrs, value)

                # Seed the value via update callback (no direct hass.states writes)
                if update:
                    update(user_id, metric_name, value)

                _LOGGER.info("Health Bridge: Created/updated %s", entry.entity_id)

            except Exception as exc:
                _LOGGER.error(
                    "Health Bridge: Error creating entity for metric '%s': %s",
                    metric_name,
                    exc,
                    exc_info=True,
                )

        # Notify completion
        if created_entities:
            entities_str = "\n".join(created_entities)
            msg = (
                f"Successfully created/updated {len(created_entities)} entities:\n\n{entities_str}"
            )
        else:
            msg = "No entities were created or updated."

        hass.components.persistent_notification.async_create(
            msg,
            title="Health Bridge - Entity Creation Complete",
            notification_id="health_bridge_force_create_complete",
        )

    # Register the service
    hass.services.async_register(
        DOMAIN, "create_entities", create_entities, schema=ENTITY_SERVICE_SCHEMA
    )

    return True


async def async_unregister_services(hass: HomeAssistant):
    """Unregister Health Bridge services."""
    DOMAIN = get_domain()
    hass.services.async_remove(DOMAIN, "create_entities")
