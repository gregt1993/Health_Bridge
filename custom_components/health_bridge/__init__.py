"""The Health Bridge integration."""
import logging
import voluptuous as vol

from homeassistant.const import CONF_TOKEN
from homeassistant.components import webhook
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, METRIC_ATTRIBUTES_MAP

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_TOKEN): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

# --- Helpers ---

def _normalize_sleep_to_hours(v):
    """Accept seconds, minutes, or hours; return float hours."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return v
    # Heuristic:
    #  > 1440  → very likely SECONDS (e.g., 27000)     → /3600
    #  > 36    → very likely MINUTES (e.g., 450)       → /60
    #  else    → already HOURS (e.g., 7.5)
    if v > 1440:
        return round(v / 3600.0, 2)
    if v > 36:
        return round(v / 60.0, 2)
    return round(v, 2)


class HealthBridgeSensor(SensorEntity):
    """Sensor for Health Bridge metrics."""

    def __init__(self, hass: HomeAssistant, config_entry_id: str, user_id: str, metric_name: str):
        self.hass = hass
        self._config_entry_id = config_entry_id
        self._user_id = user_id
        self.metric_name = metric_name
        self._attr_native_value = None

        # IDs and name
        self._attr_unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        self._attr_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
        self.entity_id = f"sensor.{metric_name}_{user_id}"  # will be corrected by registry below

        # Attributes from shared map (native fields)
        metric_attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {})
        # fallback so kcal/%/etc don’t get lost
        self._attr_native_unit_of_measurement = (
            metric_attrs.get("native_unit_of_measurement") or metric_attrs.get("unit_of_measurement")
        )
        self._attr_state_class = metric_attrs.get("state_class")
        self._attr_icon = metric_attrs.get("icon")
        self._attr_device_class = metric_attrs.get("device_class")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"health_bridge_{self._user_id}")},
            "manufacturer": "Health Bridge",
            "model": "Health Tracker",
            "name": f"Health Bridge ({self._user_id})",
            "sw_version": "1.0",
        }

    def update_state(self, value):
        """Update the sensor state (no string formatting)."""
        self._attr_native_value = value

        # Ensure name is set
        if not getattr(self, "_attr_name", None):
            self._attr_name = f"{self.metric_name.replace('_', ' ').title()} ({self._user_id})"

        # Directly set state with legacy attributes mirrored so UI shows units
        if getattr(self, "entity_id", None):
            self.hass.states.async_set(
                self.entity_id,
                self._attr_native_value,
                {
                    "friendly_name": self._attr_name,
                    "unit_of_measurement": self._attr_native_unit_of_measurement,
                    "state_class": self._attr_state_class,
                    "icon": self._attr_icon or "mdi:chart-line",
                },
            )
            _LOGGER.debug("Health Bridge: Set state for %s to %r", self.entity_id, self._attr_native_value)
        else:
            _LOGGER.error("Health Bridge: Cannot update state - no entity_id for %s", self._attr_name)


# --- Component setup ---

async def async_setup(hass: HomeAssistant, config) -> bool:
    _LOGGER.debug("Health Bridge: async_setup started")
    if DOMAIN not in config:
        _LOGGER.debug("Health Bridge: No YAML config found; skipping YAML setup.")
        return True

    token = config[DOMAIN].get(CONF_TOKEN)
    if not token:
        _LOGGER.error("Health Bridge: Token is missing from configuration.yaml")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = token
    hass.data[DOMAIN].setdefault("entities", {})
    _LOGGER.debug("Health Bridge: Token stored in hass.data")

    setup_webhook(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Health Bridge: Setting up config entry %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = entry.data[CONF_TOKEN]
    hass.data[DOMAIN]["entry_id"] = entry.entry_id
    hass.data[DOMAIN].setdefault("entities", {})

    setup_webhook(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Health Bridge: Unloading config entry %s", entry.entry_id)
    if DOMAIN in hass.data and entry.data[CONF_TOKEN] == hass.data[DOMAIN].get("token"):
        hass.data[DOMAIN].pop("token", None)
    return True


def setup_webhook(hass: HomeAssistant) -> None:
    """Set up webhook for Health Bridge."""
    if hass.data.get(DOMAIN, {}).get("webhook_registered"):
        _LOGGER.debug("Health Bridge: Webhook already registered")
        return

    _LOGGER.debug("Health Bridge: Registering webhook")

    async def handle_webhook(hass: HomeAssistant, webhook_id: str, request):
        _LOGGER.debug("Health Bridge: Webhook received (id=%s)", webhook_id)
        try:
            data = await request.json()
        except Exception as exc:
            _LOGGER.error("Health Bridge: Webhook JSON parse error: %s", exc, exc_info=True)
            return None

        _LOGGER.info("Health Bridge: Received data: %s", data)

        stored_token = hass.data.get(DOMAIN, {}).get("token")
        received_token = data.get("token")
        if stored_token and received_token and stored_token != received_token:
            _LOGGER.warning("Health Bridge: Token mismatch; ignoring payload")
            return None

        health_data = data.get("data", {}) or {}
        if "test_connection" in health_data:
            _LOGGER.info("Health Bridge: Received test connection payload")
            hass.components.persistent_notification.async_create(
                "Health Bridge connection successful!",
                title="Health Bridge",
                notification_id="health_bridge_test_success",
            )
            return None

        user_id = data.get("user_id", "unknown")
        if not health_data:
            _LOGGER.debug("Health Bridge: Webhook had no health data")
            return None

        # Ensure device exists
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_or_create(
            config_entry_id=hass.data.get(DOMAIN, {}).get("entry_id"),
            identifiers={(DOMAIN, f"health_bridge_{user_id}")},
            name=f"Health Bridge ({user_id})",
            manufacturer="Health Bridge",
            model="Health Tracker",
            sw_version="1.0",
        )

        # Per-user runtime entity map
        user_entities = hass.data.setdefault(DOMAIN, {}).setdefault("entities", {}).setdefault(user_id, {})
        entity_registry = er.async_get(hass)

        for metric_name, datapoints in health_data.items():
            if not datapoints:
                _LOGGER.debug("Health Bridge: Metric '%s' has no datapoints; skipping", metric_name)
                continue

            latest_value = datapoints[-1].get("value")
            if latest_value is None:
                _LOGGER.debug("Health Bridge: Metric '%s' missing latest value; skipping", metric_name)
                continue

            if metric_name in (
                "body_fat_percentage",
                "walking_asymmetry_percentage",
                "walking_double_support_percentage",
                "oxygen_saturation",
            ):
                try:
                    v = float(latest_value)
                except (TypeError, ValueError):
                    pass
                else:
                    if 0.0 <= v <= 1.0:
                        latest_value = v * 100.0
                    elif v < 0.0:
                        latest_value = 0.0
                    elif v > 100.0:
                        latest_value = 100.0



            # Normalize sleep to HOURS
            if metric_name == "sleep_duration":
                latest_value = _normalize_sleep_to_hours(latest_value)

            unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
            suggested_object_id = f"{metric_name}_{user_id}"
            entity_id = f"sensor.{suggested_object_id}"

            # Create (or get) runtime entity object
            if metric_name in user_entities:
                entity = user_entities[metric_name]
            else:
                entity = HealthBridgeSensor(hass, hass.data.get(DOMAIN, {}).get("entry_id"), user_id, metric_name)

                # Registry entry (stable entity_id)
                entity_entry = entity_registry.async_get_or_create(
                    domain="sensor",
                    platform=DOMAIN,
                    unique_id=unique_id,
                    suggested_object_id=suggested_object_id,
                    device_id=device.id,
                    original_name=f"{metric_name.replace('_', ' ').title()} ({user_id})",
                )
                entity.entity_id = entity_entry.entity_id
                user_entities[metric_name] = entity
                _LOGGER.debug("Health Bridge: Registered entity %s", entity.entity_id)

            # Update runtime entity
            entity.update_state(latest_value)

            # Ensure legacy attributes are present in state (fallback for UI)
            metric_attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {})
            friendly_name = f"{metric_name.replace('_', ' ').title()} ({user_id})"
            uom = metric_attrs.get("native_unit_of_measurement") or metric_attrs.get("unit_of_measurement")

            hass.states.async_set(
                entity.entity_id,
                entity._attr_native_value if hasattr(entity, "_attr_native_value") else latest_value,
                {
                    "friendly_name": friendly_name,
                    "unit_of_measurement": uom,
                    "state_class": metric_attrs.get("state_class"),
                    "icon": metric_attrs.get("icon"),
                },
            )
            _LOGGER.debug("Health Bridge: Explicitly set attributes for %s", entity.entity_id)

        _LOGGER.info("Health Bridge: Webhook processed successfully.")
        return None

    webhook.async_register(
        hass,
        DOMAIN,
        "Health Bridge",
        "health_bridge",
        handle_webhook,
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["webhook_registered"] = True
    _LOGGER.info("Health Bridge webhook registered with ID: health_bridge")
