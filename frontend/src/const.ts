/** Replaced at build time with the version in package.json. */
declare const __CARD_VERSION__: string;

export const CARD_VERSION = __CARD_VERSION__;

/** The integration whose road weather stations the card shows. */
export const PLATFORM = "digitraffic_live";

/** The station's sensors, by their translation key, which stays the same in every language. */
export const SENSORS = [
    "road_temperature",
    "air_temperature",
    "road_surface",
    "grip",
    "grip_condition",
    "road_warning",
    "wind_speed",
    "wind_gusts",
    "precipitation",
    "precipitation_type",
    "rain_intensity",
    "visibility",
] as const;

export type SensorKey = (typeof SENSORS)[number];

/** The grip conditions from the least grip to the most, one part of the scale each. */
export const GRIP_SCALE = ["very_slippery", "slippery", "fair_winter", "good_winter", "fair", "good"] as const;

/** Gusts are shown beside the mean wind only when they exceed it by this much, in m/s. */
export const GUST_MARGIN = 3;

/** Wind speed units Home Assistant lets a user pick, as m/s per unit, so gusts are compared in m/s whatever is shown. */
export const WIND_UNITS: Record<string, number> = {
    "m/s": 1,
    "km/h": 1 / 3.6,
    mph: 0.44704,
    kn: 0.514444,
    "ft/s": 0.3048,
};

/** Weather is drawn with Weather Icons ("wi:"), the road with Material Design Icons, which has the road ones. */
export const ICONS: Record<string, string> = {
    road_temperature: "mdi:road-variant",
    air_temperature: "wi:thermometer",
    road_surface: "mdi:layers-outline",
    wind: "wi:strong-wind",
    visibility: "wi:fog",
    road_warning: "mdi:alert-outline",
};

/** Icons for the type of precipitation, which the station's present weather sensor tells. */
export const PRECIPITATION_TYPE_ICONS: Record<string, string> = {
    none: "wi:cloud",
    very_light: "wi:sprinkle",
    drizzle: "wi:sprinkle",
    rain: "wi:rain",
    snow: "wi:snow",
    wet_sleet: "wi:sleet",
    sleet: "wi:sleet",
    hail: "wi:hail",
    ice_crystals: "wi:snowflake-cold",
    snow_grains: "wi:snowflake-cold",
    graupel: "wi:hail",
    freezing_drizzle: "wi:rain-mix",
    freezing_rain: "wi:rain-mix",
};

/** Precipitation that freezes on the road. It is shown in the warning colour, and in each station's row. */
export const FREEZING = ["freezing_drizzle", "freezing_rain"];

/** The amount codes for heavy precipitation, the highest there are. They are shown the same way as freezing rain. */
export const HEAVY = ["heavy", "heavy_snow"];

/** The short text for heavy precipitation of each type. Hail and freezing rain keep their own. */
export const HEAVY_TEXTS: Record<string, string> = {
    very_light: "heavy_rain",
    drizzle: "heavy_rain",
    rain: "heavy_rain",
    snow: "heavy_snow",
    snow_grains: "heavy_snow",
    wet_sleet: "heavy_sleet",
    sleet: "heavy_sleet",
};

/**
 * A station without the present weather sensor tells only the amount of precipitation and whether it is rain or
 * snow (or sleet): an icon for each, and the short text it is shown with.
 */
export const PRECIPITATION_ICONS: Record<string, [string, string]> = {
    none: ["wi:cloud", "none"],
    light: ["wi:sprinkle", "rain"],
    moderate: ["wi:showers", "rain"],
    heavy: ["wi:rain", "heavy_rain"],
    light_snow: ["wi:sleet", "snow_or_sleet"],
    moderate_snow: ["wi:snow", "snow_or_sleet"],
    heavy_snow: ["wi:snow", "heavy_snow_or_sleet"],
};
