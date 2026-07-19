
"""The Health Bridge integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
import voluptuous as vol

from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.components import webhook
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, METRIC_ATTRIBUTES_MAP

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_TOKEN): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

# --- Sleep helpers / config ---------------------------------------------------
# Add near the top (module-level constant)
_LAST_SYNC_MIN_INTERVAL_SECONDS = 10
def _normalize_sleep_to_hours(v):
    """Assume input is seconds; return float hours rounded to 2 decimals."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return v
    return round(v / 3600.0, 2)

# Sleep metrics that should be stored as HOURS
_SLEEP_HOUR_KEYS = {
    "sleep_duration",
    "sleep_rem_hours",
    "sleep_core_hours",   # Apple's “Core” ≈ light
    "sleep_deep_hours",
    "sleep_awake_hours",
}

# Add near the top (module-level constant)
_LAST_SYNC_MIN_INTERVAL_SECONDS = 10

# Pretty display names for specific metrics (enforced each sync)
_DISPLAY_NAME_OVERRIDES = {
    "sleep_duration": "Sleep Duration",
    "sleep_rem_hours": "REM Sleep Duration",
    "sleep_core_hours": "Light Sleep Duration",
    "sleep_deep_hours": "Deep Sleep Duration",
    "sleep_awake_hours": "Sleep Awake Duration",
    "last_sync_time": "Last Sync Time",
    "uv_index": "UV Index",
    "time_in_daylight": "Time in Daylight",
    "uv_exposure_sed": "UV Exposure",
    "asleep_time": "Asleep Time",
    "wake_time": "Wake Time",
    "net_calories": "Net Calories",
    "last_apple_workout": "Last Apple Workout",
}

# --- Setup / teardown ---------------------------------------------------------

async def async_setup(hass: HomeAssistant, config) -> bool:
    if DOMAIN not in config:
        return True
    token = config[DOMAIN].get(CONF_TOKEN)
    if not token:
        _LOGGER.error("Health Bridge: Token missing in YAML config")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = token
    hass.data[DOMAIN].setdefault("entities", {})
    _setup_webhook(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Health Bridge: Setting up config entry %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = entry.data[CONF_TOKEN]
    hass.data[DOMAIN]["entry_id"] = entry.entry_id
    hass.data[DOMAIN].setdefault("entities", {})

    # Ensure the sensor platform is loaded so add_sensor/update_sensor are available
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])

    _setup_webhook(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if DOMAIN in hass.data and entry.data.get(CONF_TOKEN) == hass.data[DOMAIN].get("token"):
        hass.data[DOMAIN].pop("token", None)
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Allow a Health Bridge device to be removed from the device page."""
    return await async_delete_device_for_entry(hass, config_entry, device_entry.id)


# --- Webhook ------------------------------------------------------------------

def _setup_webhook(hass: HomeAssistant) -> None:
    if hass.data.get(DOMAIN, {}).get("webhook_registered"):
        return

    async def handle_webhook(hass: HomeAssistant, webhook_id: str, request):
        try:
            data = await request.json()
        except Exception as exc:
            _LOGGER.error("Health Bridge: Webhook JSON parse error: %s", exc, exc_info=True)
            return None

        stored_token = hass.data.get(DOMAIN, {}).get("token")
        received_token = data.get("token")
        user_id = data.get("user_id", "unknown")

        # Always stamp last sync time attempt
        _update_last_sync_time_entity(hass, user_id=user_id)

        if stored_token and received_token and stored_token != received_token:
            _LOGGER.warning("Health Bridge: Token mismatch; ignoring payload")
            return None

        health_data = data.get("data", {}) or {}

        if "test_connection" in health_data:
            hass.components.persistent_notification.async_create(
                "Health Bridge connection successful!",
                title="Health Bridge",
                notification_id="health_bridge_test_success",
            )
            return None

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

        # Callbacks from the sensor platform (sensor.py)
        add_sensor = hass.data.get(DOMAIN, {}).get("add_sensor")
        update_sensor = hass.data.get(DOMAIN, {}).get("update_sensor")
        if not add_sensor:
            _LOGGER.warning("Health Bridge: sensor platform not ready (no add_sensor); dropping payload")
            return None

        entity_registry = er.async_get(hass)
        user_entities = hass.data[DOMAIN]["entities"].setdefault(user_id, {})

        for metric_name, datapoints in health_data.items():
            if not datapoints:
                continue

            # Workouts arrive as a single dict. The state is a human-readable
            # composite (type + breakdown); every field is also kept as an
            # attribute so automations/cards read clean values, not the string.
            workout_attrs = None
            if metric_name == "last_apple_workout":
                payload = datapoints[-1] or {}
                latest_value = _compose_workout_state(payload)
                latest_timestamp = payload.get("last_synced") or payload.get("end_time")
                workout_attrs = dict(payload)
            else:
                latest_value = datapoints[-1].get("value")
                latest_timestamp = datapoints[-1].get("timestamp")

            if latest_value is None:
                continue

            # Percentages: 0..1 -> 0..100, clamp
            if metric_name in (
                "body_fat_percentage",
                "walking_asymmetry_percentage",
                "walking_double_support_percentage",
                "oxygen_saturation",
                "walking_steadiness",
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

            # Sleep: seconds -> hours
            if metric_name in _SLEEP_HOUR_KEYS:
                latest_value = _normalize_sleep_to_hours(latest_value)

            # Attributes from const map; ensure native unit key present if legacy key used
            attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {}).copy()
            if "native_unit_of_measurement" not in attrs and "unit_of_measurement" in attrs:
                attrs["native_unit_of_measurement"] = attrs["unit_of_measurement"]

            unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
            suggested_object_id = f"{metric_name}_{user_id}"
            entity_id = f"sensor.{suggested_object_id}"

            # --- Ensure the registry entry exists
            entry = entity_registry.async_get(entity_id)
            if entry is None:
                entry = entity_registry.async_get_or_create(
                    domain="sensor",
                    platform=DOMAIN,
                    unique_id=unique_id,
                    suggested_object_id=suggested_object_id,
                    device_id=device.id,
                    config_entry_id=hass.data.get(DOMAIN, {}).get("entry_id"),
                    original_name=f"{_DISPLAY_NAME_OVERRIDES.get(metric_name, metric_name.replace('_', ' ').title())} ({user_id})",
                )

            # --- Ensure runtime entity exists and update
            if metric_name not in user_entities:
                # Create runtime entity via sensor platform
                add_sensor(
                    user_id,
                    metric_name,
                    attrs,
                    latest_value,
                    latest_timestamp,
                    workout_attrs,
                )
                user_entities[metric_name] = entry.entity_id
            else:
                if update_sensor:
                    update_sensor(
                        user_id,
                        metric_name,
                        latest_value,
                        latest_timestamp,
                        workout_attrs,
                    )

        return None

    webhook.async_register(hass, DOMAIN, "Health Bridge", "health_bridge", handle_webhook)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["webhook_registered"] = True
    _LOGGER.info("Health Bridge webhook registered")


# --- Helpers ------------------------------------------------------------------

def _compose_workout_state(payload: dict) -> str | None:
    """Build the workout sensor's state: '<Type> · <duration> · <distance?> ·
    <energy?> · <avg HR?>'. Optional fields are included only when present, so
    it degrades gracefully across every workout type (a strength session simply
    has no distance). Returns None if there's no workout type to key on."""
    workout_type = payload.get("workout_type")
    if not workout_type:
        return None

    parts: list[str] = [str(workout_type)]

    duration = payload.get("duration_min")
    if duration is not None:
        parts.append(f"{int(round(float(duration)))} min")

    distance_km = payload.get("distance_km")
    if distance_km:
        parts.append(f"{distance_km} km")

    energy = payload.get("active_energy_kcal")
    if energy:
        parts.append(f"{int(round(float(energy)))} kcal")

    avg_hr = payload.get("average_heart_rate_bpm")
    if avg_hr:
        parts.append(f"{int(round(float(avg_hr)))} bpm")

    return " · ".join(parts)


async def async_delete_device_for_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, device_id: str
) -> bool:
    """Delete a Health Bridge device and clean up its entities/runtime state."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    device = device_registry.async_get(device_id)
    if device is None:
        return False

    user_id = _get_user_id_from_device(device)

    for entity_entry in list(er.async_entries_for_device(entity_registry, device_id)):
        hass.states.async_remove(entity_entry.entity_id)
        entity_registry.async_remove(entity_entry.entity_id)

    device_registry.async_remove_device(device_id)

    domain_data = hass.data.get(DOMAIN, {})
    if user_id is not None:
        domain_data.get("entities", {}).pop(user_id, None)
        domain_data.get("entity_objs", {}).pop(user_id, None)

    return True


def _get_user_id_from_device(device: dr.DeviceEntry) -> str | None:
    """Extract the Health Bridge user id from a device registry entry."""
    for domain, identifier in device.identifiers:
        if domain == DOMAIN and identifier.startswith("health_bridge_"):
            return identifier.removeprefix("health_bridge_")
    return None

def _update_last_sync_time_entity(hass: HomeAssistant, user_id: str) -> None:
    """Create/update per-user last_sync_time entity, but only if ≥10s since last update."""
    try:
        metric_name = "last_sync_time"
        unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
        suggested_object_id = f"{metric_name}_{user_id}"
        entity_id = f"sensor.{suggested_object_id}"

        # --- Smoothing: skip if last update was < threshold ago
        prev_state = hass.states.get(entity_id)
        now = datetime.now(timezone.utc)
        if prev_state is not None:
            last_updated = prev_state.last_updated
            # Ensure tz-aware for subtraction
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            elapsed = (now - last_updated).total_seconds()
            if elapsed < _LAST_SYNC_MIN_INTERVAL_SECONDS:
                _LOGGER.debug(
                    "Health Bridge: Skipping last_sync_time update for %s (%.2fs < %ds)",
                    user_id, elapsed, _LAST_SYNC_MIN_INTERVAL_SECONDS
                )
                return

        # We’re past the smoothing window (or no previous state) — proceed.
        ent_reg = er.async_get(hass)
        dev_reg = dr.async_get(hass)

        # Ensure device exists
        device = dev_reg.async_get_or_create(
            config_entry_id=hass.data.get(DOMAIN, {}).get("entry_id"),
            identifiers={(DOMAIN, f"health_bridge_{user_id}")},
            name=f"Health Bridge ({user_id})",
            manufacturer="Health Bridge",
            model="Health Tracker",
            sw_version="1.0",
        )

        # Ensure registry entry exists
        if ent_reg.async_get(entity_id) is None:
            ent_reg.async_get_or_create(
                domain="sensor",
                platform=DOMAIN,
                unique_id=unique_id,
                suggested_object_id=suggested_object_id,
                device_id=device.id,
                config_entry_id=hass.data.get(DOMAIN, {}).get("entry_id"),
                original_name=f"{_DISPLAY_NAME_OVERRIDES.get(metric_name, 'Last Sync Time')} ({user_id})",
            )

        # Route through the sensor platform so last_sync_time is a real,
        # restorable entity (survives Core restarts) — not a bare state write,
        # which would leave no live entity object after startup.
        domain_data = hass.data.get(DOMAIN, {})
        add_sensor = domain_data.get("add_sensor")
        update_sensor = domain_data.get("update_sensor")
        user_entities = domain_data.setdefault("entities", {}).setdefault(user_id, {})
        attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {}).copy()

        if metric_name in user_entities:
            if update_sensor:
                update_sensor(user_id, metric_name, now)
        elif add_sensor:
            add_sensor(user_id, metric_name, attrs, now)
            user_entities[metric_name] = entity_id
    except Exception as exc:
        _LOGGER.error(
            "Health Bridge: Failed to update last_sync_time for %s: %s",
            user_id, exc, exc_info=True
        )
