"""The Health Bridge integration."""
from __future__ import annotations

import logging
import re
import voluptuous as vol

from .config_flow import (
    CONF_NUTRIENT_MASS_UNIT,
    CONF_WATER_VOLUME_UNIT,
    DEFAULT_NUTRIENT_MASS_UNIT,
    DEFAULT_WATER_VOLUME_UNIT,
)

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
async def async_migrate_entry(hass, entry):
    """Migrate old config entry data to the latest version."""
    from homeassistant.const import CONF_TOKEN

    cur_version = entry.version
    if cur_version is None:
        cur_version = 1  # old entries may have no version

    if cur_version == 1:
        # Start from existing data/options
        data = dict(entry.data or {})
        options = dict(entry.options or {})

        # Mirror token into options so it becomes editable in the Options UI
        token = options.get(CONF_TOKEN) or data.get(CONF_TOKEN)
        if token:
            options[CONF_TOKEN] = token

        # Seed new unit prefs if missing
        options.setdefault("nutrient_mass_unit", "g")
        # Accept legacy stored value "fl_oz" but normalize on next startup elsewhere
        options.setdefault("water_volume_unit", "mL")

        # Write back with bumped version
        hass.config_entries.async_update_entry(entry, data=data, options=options, version=2)
        return True

    # Already at latest
    return True

# -------- Aliases (display names, old keys, typos → Swift rawValue keys) --------
_ALIAS_MAP = {
    # Activity/movement
    "active calories": "active_calories",
    "flights climbed": "flights_climbed",
    "walking speed": "walking_speed",
    "walking step length": "walking_step_length",
    "walking asymmetry": "walking_asymmetry_percentage",
    "walking asymmetry percentage": "walking_asymmetry_percentage",
    "walking double support": "walking_double_support_percentage",
    "walking double support percentage": "walking_double_support_percentage",
    "swimming distance": "swimming_distance",
    "6-min walk test distance": "six_minute_walk_test_distance",
    "six-min walk test distance": "six_minute_walk_test_distance",
    "stair ascent speed": "stair_ascent_speed",
    "stair decent speed": "stair_descent_speed",  # typo
    "stair descent speed": "stair_descent_speed",

    # Body
    "body mass": "body_mass",
    "weight": "body_mass",
    "body fat percentage": "body_fat_percentage",
    "lean body mass": "lean_body_mass",
    "waist circumference": "waist_circumference",

    # Vitals
    "body temperature": "body_temperature",
    "heart rate": "heart_rate",
    "resting heart rate": "resting_heart_rate",
    "walking heart rate avg": "walking_heart_rate_average",
    "walking heart rate average": "walking_heart_rate_average",
    "heart rate variability": "heart_rate_variability",
    "vo2 max": "vo2_max",
    "blood pressure (systolic)": "blood_pressure_systolic",
    "blood pressure systolic": "blood_pressure_systolic",
    "blood pressure (diastolic)": "blood_pressure_diastolic",
    "blood pressure diastolic": "blood_pressure_diastolic",
    "blood oxygen": "oxygen_saturation",  # alias

    # Nutrition & glucose
    "carbohydrates intake": "dietary_carbohydrates",
    "fat intake": "dietary_fat",
    "protein intake": "dietary_protein",
    "protine intake": "dietary_protein",
    "water intake": "dietary_water",
    "resting calories": "basal_energy_burned",

    # Sleep/breathing & audio
    "sleep duration": "sleep_duration",
    "respiratory rate": "respiratory_rate",
    "mindful minutes": "mindful_minutes",
    "headphone audio exposure": "headphone_audio_exposure",
    "environmental audio exposure": "environmental_audio_exposure",
}

def _canon_key(name: str) -> str:
    """Canonicalize a provided metric name to the Swift rawValue key."""
    key = (name or "").strip().lower()
    key = re.sub(r"\s+", " ", key)
    return _ALIAS_MAP.get(key, key.replace(" ", "_"))

def _normalize_metric_and_value(metric_name: str, value):
    """
    Map aliases and normalize units to the native units specified in const.py.
    Handles:
      - seconds → minutes (sleep/mindful)
      - grams → kg (body_mass)
      - m/cm → mm (height/waist)
      - cm → m (walking_step_length)
      - mg/dL → mmol/L (blood_glucose)
      - fractions → percent (oxygen_saturation, body_fat_percentage, walking_*_percentage)
      - typing coercion for numerics
    """
    m = _canon_key(metric_name)

    # ---- Simple numeric coercion ----
    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    # ---- Body mass: grams → kg ----
    if m == "body_mass":
        v = _f(value)
        if isinstance(v, (int, float)):
            # If value looks like grams (e.g., 72000), convert to kg
            if v > 250:
                return m, v / 1000.0
            return m, v
        return m, value

    # ---- Height: m/cm → mm (native) ----
    if m == "height":
        v = _f(value)
        if isinstance(v, (int, float)):
            if v < 3.0:            # meters
                return m, int(round(v * 1000.0))
            if 30 <= v <= 300:     # centimeters
                return m, int(round(v * 10.0))
            return m, int(round(v))  # assume already mm
        return m, value

    # ---- Waist circumference: cm → mm ----
    if m == "waist_circumference":
        v = _f(value)
        if isinstance(v, (int, float)):
            if v <= 300:  # cm
                return m, int(round(v * 10.0))
            return m, int(round(v))  # mm
        return m, value

    # ---- Walking step length: cm → m ----
    if m == "walking_step_length":
        v = _f(value)
        if isinstance(v, (int, float)):
            if 3 <= v <= 300:  # centimeters
                return m, v / 100.0
            return m, v  # meters
        return m, value

    # ---- Percentages: fractions (0..1) → % (0..100), clamp ----
    if m in ("walking_asymmetry_percentage", "walking_double_support_percentage",
             "oxygen_saturation", "body_fat_percentage"):
        v = _f(value)
        if isinstance(v, (int, float)):
            if 0.0 <= v <= 1.0:
                v = v * 100.0
            return m, max(0.0, min(100.0, v))
        return m, value

    # ---- Blood glucose: mg/dL → mmol/L if necessary ----
    if m == "blood_glucose":
        v = _f(value)
        if isinstance(v, (int, float)):
            # If clearly mg/dL (>20 typical mmol/L upper bound), convert:
            if v > 20.0:
                return m, round(v * 0.0555, 2)
            return m, v
        return m, value

    # ---- Durations (seconds from HK) → minutes (native for our sensors) ----
    if m in ("sleep_duration", "mindful_minutes"):
        v = _f(value)
        if isinstance(v, (int, float)):
            return m, int(round(v / 60.0))  # minutes
        return m, value

    # ---- Speeds, distances, energy, rates: parse numeric ----
    if m in (
        "walking_speed", "stair_ascent_speed", "stair_descent_speed",
        "distance", "swimming_distance", "six_minute_walk_test_distance",
        "active_calories", "basal_energy_burned",
        "heart_rate", "resting_heart_rate", "walking_heart_rate_average",
        "heart_rate_variability", "vo2_max",
        "respiratory_rate",
        "dietary_carbohydrates", "dietary_fat", "dietary_protein", "dietary_water",
        "blood_pressure_systolic", "blood_pressure_diastolic",
        "steps", "flights_climbed",
        "body_temperature",
        "headphone_audio_exposure", "environmental_audio_exposure",
    ):
        v = _f(value)
        return m, v

    # Default: return canonical key and original value
    return m, value


# --------------------------
# Unit preference converters (for dietary metrics)
# --------------------------

def _convert_mass_for_pref(value_float: float, pref: str) -> tuple[float, str]:
    """grams <-> ounces; default native is grams."""
    if pref == "oz":
        return (value_float / 28.349523125, "oz")
    return (value_float, "g")

def _convert_volume_for_pref(value_float: float, pref: str) -> tuple[float, str]:
    """mL <-> US fl oz; default native is mL."""
    # accept either "fl oz" or legacy "fl_oz" from options
    if pref.replace("_", " ") == "fl oz":
        return (value_float / 29.5735295625, "fl oz")
    return (value_float, "mL")


# --------------------------
# Component setup / teardown
# --------------------------

async def async_setup(hass: HomeAssistant, config) -> bool:
    _LOGGER.debug("Health Bridge: async_setup started")
    await _async_register_entity_fix_service(hass)

    if DOMAIN not in config:
        _LOGGER.debug("Health Bridge: No configuration in configuration.yaml; skipping YAML setup.")
        return True

    token = config[DOMAIN].get(CONF_TOKEN)
    if not token:
        _LOGGER.error("Health Bridge: Token is missing from configuration.yaml")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["token"] = token
    hass.data[DOMAIN].setdefault("entities", {})
    _LOGGER.debug("Health Bridge: Token loaded from YAML and stored in hass.data")

    _setup_webhook(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Health Bridge: Setting up config entry %s", entry.entry_id)
    await _async_register_entity_fix_service(hass)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entry_id"] = entry.entry_id
    hass.data[DOMAIN].setdefault("entities", {})

    # Cache token and unit prefs from options (fallback to data for token)
    _cache_entry_options(hass, entry)

    # Listen for options updates so token/unit prefs take effect immediately
    unsub = entry.add_update_listener(_async_options_updated)
    hass.data[DOMAIN]["unsub_update_listener"] = unsub

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    _setup_webhook(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Health Bridge: Unloading config entry %s", entry.entry_id)
    unsub = hass.data.get(DOMAIN, {}).pop("unsub_update_listener", None)
    if unsub:
        unsub()
    return True


def _cache_entry_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Cache latest token and unit preferences into hass.data."""
    opts = entry.options or {}
    data = entry.data or {}

    # Prefer token from options (editable in UI); fallback to data
    token = opts.get(CONF_TOKEN) or data.get(CONF_TOKEN)
    if token:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["token"] = token

    # Normalize water unit spelling to HA's "fl oz"
    water_pref = opts.get(CONF_WATER_VOLUME_UNIT, DEFAULT_WATER_VOLUME_UNIT)
    water_pref = water_pref.replace("_", " ")

    hass.data[DOMAIN]["options"] = {
        CONF_NUTRIENT_MASS_UNIT: opts.get(CONF_NUTRIENT_MASS_UNIT, DEFAULT_NUTRIENT_MASS_UNIT),
        CONF_WATER_VOLUME_UNIT: water_pref or DEFAULT_WATER_VOLUME_UNIT,
    }

    _LOGGER.debug("Health Bridge: cached options (units: %s, %s)",
                  hass.data[DOMAIN]["options"].get(CONF_NUTRIENT_MASS_UNIT),
                  hass.data[DOMAIN]["options"].get(CONF_WATER_VOLUME_UNIT))


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("Health Bridge: Options updated; refreshing cached token and prefs")
    _cache_entry_options(hass, entry)


# --------------------------
# Webhook
# --------------------------

def _setup_webhook(hass: HomeAssistant) -> None:
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

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_or_create(
            config_entry_id=hass.data.get(DOMAIN, {}).get("entry_id"),
            identifiers={(DOMAIN, f"health_bridge_{user_id}")},
            name=f"Health Bridge ({user_id})",
            manufacturer="Health Bridge",
            model="Health Tracker",
            sw_version="1.0",
        )

        add_sensor = hass.data.get(DOMAIN, {}).get("add_sensor")
        update_sensor = hass.data.get(DOMAIN, {}).get("update_sensor")
        if not add_sensor:
            _LOGGER.warning("Health Bridge: sensor platform not ready (no add_sensor); dropping payload")
            return None

        user_entities = hass.data[DOMAIN]["entities"].setdefault(user_id, {})
        entity_registry = er.async_get(hass)

        # Pull unit preferences (with defaults, already normalized)
        options = hass.data.get(DOMAIN, {}).get("options", {})
        nutrient_pref = options.get(CONF_NUTRIENT_MASS_UNIT, DEFAULT_NUTRIENT_MASS_UNIT)  # "g" or "oz"
        water_pref = options.get(CONF_WATER_VOLUME_UNIT, DEFAULT_WATER_VOLUME_UNIT)       # "mL" or "fl oz"

        for raw_metric_name, datapoints in health_data.items():
            if not datapoints:
                _LOGGER.debug("Health Bridge: Metric '%s' has no datapoints; skipping", raw_metric_name)
                continue

            latest_value = datapoints[-1].get("value")
            if latest_value is None:
                _LOGGER.debug("Health Bridge: Metric '%s' missing latest value; skipping", raw_metric_name)
                continue

            metric_name, latest_value = _normalize_metric_and_value(raw_metric_name, latest_value)

            # Apply per-integration unit prefs for dietary metrics (convert & override native unit)
            unit_pref: str | None = None
            if metric_name in ("dietary_carbohydrates", "dietary_fat", "dietary_protein"):
                try:
                    v = float(latest_value)
                except (TypeError, ValueError):
                    v = latest_value
                else:
                    v_pref, unit_pref = _convert_mass_for_pref(v, nutrient_pref)
                    latest_value = v_pref
            elif metric_name == "dietary_water":
                try:
                    v = float(latest_value)
                except (TypeError, ValueError):
                    v = latest_value
                else:
                    v_pref, unit_pref = _convert_volume_for_pref(v, water_pref)
                    latest_value = v_pref

            unique_id = f"{DOMAIN}_{metric_name}_{user_id}"
            suggested_object_id = f"{metric_name}_{user_id}"
            entity_id = f"sensor.{suggested_object_id}"

            attrs = METRIC_ATTRIBUTES_MAP.get(metric_name, {}).copy()
            if "native_unit_of_measurement" not in attrs and "unit_of_measurement" in attrs:
                attrs["native_unit_of_measurement"] = attrs["unit_of_measurement"]

            # If a preference was applied above, override native unit
            if unit_pref:
                attrs["native_unit_of_measurement"] = unit_pref  # "g"/"oz" or "mL"/"fl oz"

            entry = entity_registry.async_get(entity_id)
            if entry is None:
                entry = entity_registry.async_get_or_create(
                    domain="sensor",
                    platform=DOMAIN,
                    unique_id=unique_id,
                    suggested_object_id=suggested_object_id,
                    device_id=device.id,
                    original_name=f"{metric_name.replace('_', ' ').title()} ({user_id})",
                )
                user_entities[metric_name] = entry.entity_id
                add_sensor(user_id, metric_name, attrs, latest_value)
                _LOGGER.debug("Health Bridge: Created entity %s", entry.entity_id)
            else:
                user_entities.setdefault(metric_name, entry.entity_id)
                if update_sensor:
                    update_sensor(user_id, metric_name, latest_value)
                else:
                    _LOGGER.debug("Health Bridge: update_sensor callback not available yet; skipped update for %s", entry.entity_id)

        _LOGGER.info("Health Bridge: Webhook processed successfully.")
        return None

    webhook.async_register(hass, DOMAIN, "Health Bridge", "health_bridge", handle_webhook)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["webhook_registered"] = True
    _LOGGER.info("Health Bridge webhook registered with ID: health_bridge")


# --------------------------
# Maintenance service
# --------------------------

async def _async_register_entity_fix_service(hass: HomeAssistant) -> None:
    async def fix_entity_names_service(call):
        _LOGGER.info("Health Bridge: Starting entity name fix service")
        ent_reg = er.async_get(hass)
        updated = 0

        for entry in list(ent_reg.entities.values()):
            if entry.domain != "sensor":
                continue
            object_id = entry.entity_id.split(".", 1)[-1]
            parts = object_id.split("_")
            if len(parts) < 2:
                continue
            user_id = parts[-1]
            metric_name = "_".join(parts[:-1])
            desired = f"{metric_name.replace('_', ' ').title()} ({user_id})"
            if not entry.name:
                ent_reg.async_update_entity(entry.entity_id, name=desired)
                updated += 1

        msg = f"Updated {updated} Health Bridge entity names in the registry."
        hass.components.persistent_notification.async_create(
            msg, title="Health Bridge Entity Fix", notification_id="health_bridge_entity_fix"
        )
        _LOGGER.info("Health Bridge: %s", msg)

    hass.services.async_register(DOMAIN, "fix_entity_names", fix_entity_names_service)
    _LOGGER.info("Health Bridge: Registered fix_entity_names service")
