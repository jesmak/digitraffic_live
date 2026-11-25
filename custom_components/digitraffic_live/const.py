"""Constants for the Digitraffic Live integration."""

from typing import Final

DOMAIN: Final = "digitraffic_live"

# Shown on the map and required by the CC BY 4.0 licence.
ATTRIBUTION: Final = "Fintraffic / digitraffic.fi, CC BY 4.0"
# The nautical warnings are Traficom's, under the same licence.
TRAFICOM_ATTRIBUTION: Final = "Traficom, CC BY 4.0"
# The water restriction areas are the Finnish Transport Infrastructure Agency's, under the same licence.
VAYLAVIRASTO_ATTRIBUTION: Final = "Väylävirasto, CC BY 4.0"

# Version of the Map Feed format the sensors write (docs/map-feed-format.md in map-feed-card).
MAP_FEED_VERSION: Final = 1

# Version of the departures format the station departure sensors write (docs/departures-format.md in departures-card).
DEPARTURES_VERSION: Final = 1

# Languages for the texts the integration writes into feeds. Each needs a texts/<code>.json file.
LANGUAGES: Final = ["fi", "en"]

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
SUBENTRY_NAUTICAL_WARNINGS: Final = "nautical_warnings"
SUBENTRY_WATER_RESTRICTIONS: Final = "water_restrictions"
# The next departures from one railway station, as a departures sensor rather than a map feed
SUBENTRY_STATION_DEPARTURES: Final = "station_departures"
# A single road weather station or camera, which becomes a device with its own entities
SUBENTRY_ROAD_WEATHER_STATION: Final = "road_weather_station"
SUBENTRY_WEATHER_CAMERA: Final = "weather_camera"
# One port's winter navigation restrictions and suspensions, and the ships calling at it, as a device
SUBENTRY_PORT: Final = "port"

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
CONF_RESTRICTION_TYPES: Final = "restriction_types"

# Road weather station and camera settings (config subentry data)
CONF_STATION: Final = "station"
# Station departure settings; the station uses CONF_STATION
CONF_STOPS_AT: Final = "stops_at"
CONF_DEPARTURES: Final = "departures"
CONF_DIRECTION: Final = "direction"
DIRECTION_DEPARTURES: Final = "departures"
DIRECTION_ARRIVALS: Final = "arrivals"
DIRECTION_BOTH: Final = "both"
DIRECTIONS: Final = [DIRECTION_DEPARTURES, DIRECTION_ARRIVALS, DIRECTION_BOTH]
# The sensors each direction makes.
DIRECTION_SENSORS: Final[dict[str, list[str]]] = {
    DIRECTION_DEPARTURES: [DIRECTION_DEPARTURES],
    DIRECTION_ARRIVALS: [DIRECTION_ARRIVALS],
    DIRECTION_BOTH: [DIRECTION_DEPARTURES, DIRECTION_ARRIVALS],
}
CONF_CAMERA: Final = "camera"
# Port settings: the port chosen, a UN/LOCODE, and whether its winter navigation and its ships are followed.
CONF_PORT: Final = "port"
CONF_WINTER_LOCATION: Final = "winter_location"
CONF_PORT_CALLS: Final = "port_calls"
# The ports whose calls the port call service files under another port's UN/LOCODE. Hamina's are under Kotka's, the two
# being one port company, and each call's port area tells whose it is. No other two Finnish ports shared port areas in
# the service's port list.
CALLS_FILED_UNDER: Final = {"FIHMN": "FIKTK"}

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
DEFAULT_NAUTICAL_WARNING_REFRESH_SECONDS: Final = 600
# Restrictions change by the day, and ships' calls are announced days ahead.
DEFAULT_PORT_REFRESH_SECONDS: Final = 600
# The restriction areas are standing decisions that rarely change.
DEFAULT_WATER_RESTRICTION_REFRESH_SECONDS: Final = 3600

DEFAULT_DEPARTURES: Final = 5
MAX_DEPARTURES: Final = 20

# Actions
SERVICE_GET_TRAIN_COMPOSITION: Final = "get_train_composition"
ATTR_DEPARTURE_DATE: Final = "departure_date"
ATTR_TRAIN_NUMBER: Final = "train_number"
