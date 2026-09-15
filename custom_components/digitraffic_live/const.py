"""Constants for the Digitraffic Live integration."""

from typing import Final

DOMAIN: Final = "digitraffic_live"

# Shown on the map and required by the CC BY 4.0 licence.
ATTRIBUTION: Final = "Fintraffic / digitraffic.fi, CC BY 4.0"

# Version of the Map Feed format the sensors write (docs/map-feed-format.md in ha-map-card-plugin-map-feed).
MAP_FEED_VERSION: Final = 1

# Languages for the texts the integration writes into feeds. Each needs a texts/<code>.json file.
LANGUAGES: Final = ["fi", "sv", "en"]

# Config entry
CONF_LANGUAGE: Final = "language"

# Feed types (config subentry types)
SUBENTRY_SHIPS: Final = "ships"
SUBENTRY_TRAINS: Final = "trains"
SUBENTRY_TRAFFIC_MESSAGES: Final = "traffic_messages"
SUBENTRY_ROAD_MAINTENANCE: Final = "road_maintenance"
SUBENTRY_ROAD_CONDITIONS: Final = "road_conditions"
SUBENTRY_WEATHER_STATIONS: Final = "weather_stations"
SUBENTRY_WEATHER_CAMERAS: Final = "weather_cameras"
# A single road weather station or camera, which becomes a device with its own entities
SUBENTRY_ROAD_WEATHER_STATION: Final = "road_weather_station"
SUBENTRY_WEATHER_CAMERA: Final = "weather_camera"

# Feed settings (config subentry data)
CONF_AREA: Final = "area"
CONF_USE_AREA: Final = "use_area"
CONF_MAX_AGE_MINUTES: Final = "max_age_minutes"
CONF_REFRESH_SECONDS: Final = "refresh_seconds"
CONF_SHIP_TYPES: Final = "ship_types"
CONF_INCLUDE_MOORED: Final = "include_moored"
CONF_ICEBREAKERS: Final = "icebreakers"
CONF_ROUTE: Final = "route"
CONF_CATEGORIES: Final = "categories"
CONF_MESSAGE_TYPES: Final = "message_types"
CONF_UPCOMING_DAYS: Final = "upcoming_days"
CONF_TASKS: Final = "tasks"
CONF_SHOW_ROUTES: Final = "show_routes"
CONF_ROUTE_HOURS: Final = "route_hours"
CONF_FORECAST: Final = "forecast"
CONF_ONLY_POOR: Final = "only_poor"
CONF_MARKER_VALUE: Final = "marker_value"

# Road weather station and camera settings (config subentry data)
CONF_STATION: Final = "station"
CONF_CAMERA: Final = "camera"

# Digitraffic caches most responses for about a minute, so polling faster only repeats the same data.
MIN_REFRESH_SECONDS: Final = 30
DEFAULT_REFRESH_SECONDS: Final = 60
DEFAULT_SHIP_MAX_AGE_MINUTES: Final = 30
DEFAULT_TRAIN_MAX_AGE_MINUTES: Final = 15
DEFAULT_MAINTENANCE_MAX_AGE_MINUTES: Final = 60
DEFAULT_ROUTE_HOURS: Final = 2
DEFAULT_UPCOMING_DAYS: Final = 7

# Road data changes more slowly than ship and train positions.
DEFAULT_TRAFFIC_MESSAGE_REFRESH_SECONDS: Final = 300
DEFAULT_ROAD_CONDITION_REFRESH_SECONDS: Final = 600
DEFAULT_WEATHER_STATION_REFRESH_SECONDS: Final = 300
DEFAULT_WEATHER_CAMERA_REFRESH_SECONDS: Final = 600

# Actions
SERVICE_GET_TRAIN_COMPOSITION: Final = "get_train_composition"
ATTR_DEPARTURE_DATE: Final = "departure_date"
ATTR_TRAIN_NUMBER: Final = "train_number"
