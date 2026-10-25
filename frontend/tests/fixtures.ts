import type { HassEntity, HomeAssistant } from "../src/hass";

/** A made-up station's readings, by translation key: a state, and its unit when it has one. */
export type Readings = Record<string, [string, string?]>;

export const DRY: Readings = {
    road_temperature: ["5.3", "°C"],
    air_temperature: ["4.8", "°C"],
    road_surface: ["dry"],
    grip: ["0.82", "µ"],
    grip_condition: ["good"],
    road_warning: ["ok"],
    wind_speed: ["3.1", "m/s"],
    wind_gusts: ["7.3", "m/s"],
    precipitation: ["none"],
    precipitation_type: ["none"],
    rain_intensity: ["0.0", "mm/h"],
    visibility: ["20.0", "km"],
};

export const SNOW: Readings = {
    ...DRY,
    road_temperature: ["-4.2", "°C"],
    road_surface: ["snow"],
    grip: ["0.22", "µ"],
    grip_condition: ["fair_winter"],
    road_warning: ["beware"],
    wind_speed: ["5.2", "m/s"],
    wind_gusts: ["6.0", "m/s"],
    precipitation: ["light_snow"],
    precipitation_type: ["snow"],
    rain_intensity: ["0.4", "mm/h"],
};

/** A station with no grip, surface or present weather sensor, as many have. */
export const SPARSE: Readings = {
    road_temperature: ["4.6", "°C"],
    air_temperature: ["4.6", "°C"],
    wind_speed: ["1.8", "m/s"],
    precipitation: ["light"],
    visibility: ["20.0", "km"],
};

/** Home Assistant with the given stations, each a device of digitraffic_live named after its key. */
export function hass(stations: Record<string, Readings>): HomeAssistant {
    const states: Record<string, HassEntity> = {};
    const entities: NonNullable<HomeAssistant["entities"]> = {
        // Something else on the same device that isn't a station sensor, and a sensor of another integration.
        "sensor.unrelated": { entity_id: "sensor.unrelated", device_id: "station-a", platform: "other", translation_key: "grip" },
    };
    const devices: NonNullable<HomeAssistant["devices"]> = {};
    for (const [device, readings] of Object.entries(stations)) {
        devices[device] = { id: device, name: `Road 1 Example, ${device}`, name_by_user: null };
        for (const [key, [state, unit]] of Object.entries(readings)) {
            // Entity ids are in the user's language, so the card must not rely on them.
            const id = `sensor.tie_${device.replace(/-/g, "_")}_${key}_fi`;
            entities[id] = { entity_id: id, device_id: device, platform: "digitraffic_live", translation_key: key };
            states[id] = { entity_id: id, state, last_changed: "2026-10-13", attributes: unit ? { unit_of_measurement: unit } : {} };
        }
    }
    return { locale: { language: "fi" }, states, entities, devices, formatEntityState };
}

/** Home Assistant's formatting as a Finnish user gets it, for numbers at least: a decimal comma and the unit. */
function formatEntityState(entity: HassEntity): string {
    const unit = entity.attributes.unit_of_measurement;
    const state = /^-?\d/.test(entity.state) ? entity.state.replace(".", ",") : entity.state;
    return unit ? `${state} ${unit}` : state;
}
