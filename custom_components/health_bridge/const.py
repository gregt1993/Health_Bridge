"""Constants for the Health Bridge integration (enum-safe, HA-compatible)."""
from __future__ import annotations

# Import only stable unit constants
from homeassistant.const import (
    UnitOfLength,
    UnitOfMass,
    UnitOfTime,
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfVolume,
    PERCENTAGE,
)

DOMAIN = "health_bridge"
DEFAULT_ICON = "mdi:heart-pulse"

# device_class/state_class are strings; sensor.py coerces them to Enums safely
METRIC_ATTRIBUTES_MAP = {
    # -------- Activity / Movement --------
    "steps": {
        "native_unit_of_measurement": "steps",
        "state_class": "total_increasing",
        "icon": "mdi:walk",
    },
    "distance": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.METERS,
        "state_class": "total_increasing",
        "icon": "mdi:map-marker-distance",
    },
    "active_calories": {
        "native_unit_of_measurement": "kcal",
        "state_class": "total_increasing",
        "icon": "mdi:fire",
    },
    "flights_climbed": {
        "native_unit_of_measurement": "floors",
        "state_class": "total_increasing",
        "icon": "mdi:stairs-up",
    },
    "walking_speed": {
        "device_class": "speed",
        "native_unit_of_measurement": UnitOfSpeed.METERS_PER_SECOND,  # m/s native
        "state_class": "measurement",
        "icon": "mdi:run",
    },
    "walking_step_length": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.METERS,  # per step
        "state_class": "measurement",
        "icon": "mdi:ruler",
    },
    "walking_asymmetry_percentage": {
        "native_unit_of_measurement": PERCENTAGE,  # 0..100
        "state_class": "measurement",
        "icon": "mdi:axis-z-rotate-clockwise",
    },
    "walking_double_support_percentage": {
        "native_unit_of_measurement": PERCENTAGE,  # 0..100
        "state_class": "measurement",
        "icon": "mdi:human-handsup",
    },
    "swimming_distance": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.METERS,
        "state_class": "total_increasing",
        "icon": "mdi:swim",
    },
    "six_minute_walk_test_distance": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.METERS,
        "state_class": "measurement",
        "icon": "mdi:walk",
    },
    "stair_ascent_speed": {
        "device_class": "speed",
        "native_unit_of_measurement": UnitOfSpeed.METERS_PER_SECOND,
        "state_class": "measurement",
        "icon": "mdi:stairs-up",
    },
    "stair_descent_speed": {
        "device_class": "speed",
        "native_unit_of_measurement": UnitOfSpeed.METERS_PER_SECOND,
        "state_class": "measurement",
        "icon": "mdi:stairs-down",
    },

    # -------- Body Measures --------
    "body_mass": {
        "device_class": "weight",
        "native_unit_of_measurement": UnitOfMass.KILOGRAMS,
        "state_class": "measurement",
        "icon": "mdi:weight-kilogram",
    },
    "height": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.MILLIMETERS,  # native mm
        "state_class": "measurement",
        "icon": "mdi:ruler",
    },
    "body_fat_percentage": {
        "native_unit_of_measurement": PERCENTAGE,  # 0..100
        "state_class": "measurement",
        "icon": "mdi:human-handsup",
    },
    "lean_body_mass": {
        "device_class": "weight",
        "native_unit_of_measurement": UnitOfMass.KILOGRAMS,
        "state_class": "measurement",
        "icon": "mdi:dumbbell",
    },
    "waist_circumference": {
        "device_class": "distance",
        "native_unit_of_measurement": UnitOfLength.MILLIMETERS,  # native mm
        "state_class": "measurement",
        "icon": "mdi:tape-measure",
    },

    # -------- Vitals --------
    "body_temperature": {
        "device_class": "temperature",
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "state_class": "measurement",
        "icon": "mdi:thermometer",
    },
    "heart_rate": {
        "device_class": "heart_rate",
        "native_unit_of_measurement": "bpm",
        "state_class": "measurement",
        "icon": "mdi:heart-pulse",
    },
    "resting_heart_rate": {
        "device_class": "heart_rate",
        "native_unit_of_measurement": "bpm",
        "state_class": "measurement",
        "icon": "mdi:heart",
    },
    "walking_heart_rate_average": {
        "device_class": "heart_rate",
        "native_unit_of_measurement": "bpm",
        "state_class": "measurement",
        "icon": "mdi:walk",
    },
    "heart_rate_variability": {
        "native_unit_of_measurement": "ms",
        "state_class": "measurement",
        "icon": "mdi:waves",
    },
    "vo2_max": {
        "native_unit_of_measurement": "mL/kg/min",
        "state_class": "measurement",
        "icon": "mdi:lungs",
    },
    "blood_pressure_systolic": {
        "device_class": "pressure",
        "native_unit_of_measurement": UnitOfPressure.MMHG,
        "state_class": "measurement",
        "icon": "mdi:heart-pulse",
    },
    "blood_pressure_diastolic": {
        "device_class": "pressure",
        "native_unit_of_measurement": UnitOfPressure.MMHG,
        "state_class": "measurement",
        "icon": "mdi:heart-pulse",
    },
    "oxygen_saturation": {
        "native_unit_of_measurement": PERCENTAGE,  # 0..100
        "state_class": "measurement",
        "icon": "mdi:lungs",
    },

    # -------- Nutrition & Glucose --------
    "dietary_carbohydrates": {
    "device_class": "weight",  # NEW
    "native_unit_of_measurement": UnitOfMass.GRAMS,
    "state_class": "total_increasing",
    "icon": "mdi:food-apple",
    },
    "dietary_fat": {
        "device_class": "weight",  # NEW
        "native_unit_of_measurement": UnitOfMass.GRAMS,
        "state_class": "total_increasing",
        "icon": "mdi:food-drumstick",
    },
    "dietary_protein": {
        "device_class": "weight" , # NEW
        "native_unit_of_measurement": UnitOfMass.GRAMS,
        "state_class": "total_increasing",
        "icon": "mdi:food-steak",
    },
    "dietary_water": {
        "device_class": "volume",  # NEW
        "native_unit_of_measurement": UnitOfVolume.MILLILITERS,
        "state_class": "total_increasing",
        "icon": "mdi:cup-water",
    },
    "blood_glucose": {
        # Native mmol/L (we'll convert mg/dL -> mmol/L in normalizer)
        "native_unit_of_measurement": "mmol/L",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
    },
    "basal_energy_burned": {
        "native_unit_of_measurement": "kcal",
        "state_class": "total_increasing",
        "icon": "mdi:fire-alert",
    },

    # -------- Sleep & Breathing --------
    "sleep_duration": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.HOURS,  # entity state must be minutes
        "state_class": "measurement",
        "icon": "mdi:sleep",
    },
    "sleep_rem_hours": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.HOURS,  # entity state must be minutes
        "state_class": "measurement",
        "icon": "mdi:sleep",
    },
    "sleep_core_hours": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.HOURS,  # entity state must be minutes
        "state_class": "measurement",
        "icon": "mdi:sleep",
    },
    "sleep_deep_hours": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.HOURS,  # entity state must be minutes
        "state_class": "measurement",
        "icon": "mdi:sleep",
    },
    "sleep_awake_hours": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.HOURS,  # entity state must be minutes
        "state_class": "measurement",
        "icon": "mdi:sleep",
    },
    "respiratory_rate": {
        "native_unit_of_measurement": "breaths/min",
        "state_class": "measurement",
        "icon": "mdi:lungs",
    },
    "mindful_minutes": {
        "device_class": "duration",
        "native_unit_of_measurement": UnitOfTime.SECONDS,
        "state_class": "total_increasing",
        "icon": "mdi:meditation",
    },

    # -------- Audio Exposure --------
    "headphone_audio_exposure": {
        "device_class": "sound_pressure",  # may fallback to None on older HA
        "native_unit_of_measurement": "dB",
        "state_class": "measurement",
        "icon": "mdi:headphones",
    },
    "environmental_audio_exposure": {
        "device_class": "sound_pressure",
        "native_unit_of_measurement": "dB",
        "state_class": "measurement",
        "icon": "mdi:volume-high",
    },

    # Connectivity / internal
    "test_connection": {
        "native_unit_of_measurement": None,
        "state_class": None,
        "icon": "mdi:check-circle",
    },
}

SUPPORTED_METRICS = tuple(METRIC_ATTRIBUTES_MAP.keys())
