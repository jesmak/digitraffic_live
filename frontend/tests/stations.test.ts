import { describe, expect, it } from "vitest";

import { precipitation, scale, showGusts, stationDevices, stationName, stationSensors, stationsOf } from "../src/stations";
import type { HassEntity } from "../src/hass";
import { DRY, SPARSE, hass } from "./fixtures";

describe("stations", () => {
    it("finds a station's sensors by translation key, leaving out other integrations and what it lacks", () => {
        const state = hass({ "station-a": DRY, "station-b": SPARSE });
        const sensors = stationSensors(state, "station-a");
        expect(sensors.grip).toBe("sensor.tie_station_a_grip_fi");
        expect(Object.keys(sensors)).toHaveLength(12);
        const sparse = stationSensors(state, "station-b");
        expect(sparse.grip).toBeUndefined();
        expect(sparse.road_surface).toBeUndefined();
        expect(Object.keys(sparse)).toHaveLength(5);
        expect(stationSensors(state, "station-gone")).toEqual({});
    });

    it("offers only devices with a road temperature sensor as stations", () => {
        expect(stationDevices(hass({ "station-a": DRY, "station-b": SPARSE }))).toEqual(["station-a", "station-b"]);
    });

    it("writes plain device ids as stations and drops empty ones", () => {
        expect(stationsOf(["station-a", { device: "station-b", name: "VT1" }, { device: "" }])).toEqual([
            { device: "station-a" },
            { device: "station-b", name: "VT1" },
        ]);
        expect(stationsOf(undefined)).toEqual([]);
    });

    it("names a station by its own name, the user's device name or the device", () => {
        const state = hass({ "station-a": DRY });
        expect(stationName(state, { device: "station-a" })).toBe("Road 1 Example, station-a");
        expect(stationName(state, { device: "station-a", name: "VT1" })).toBe("VT1");
        (state.devices as NonNullable<typeof state.devices>)["station-a"] = { id: "station-a", name: "x", name_by_user: "Renamed" };
        expect(stationName(state, { device: "station-a" })).toBe("Renamed");
        expect(stationName(state, { device: "station-gone" })).toBe("station-gone");
    });

    it("lights the scale up to the condition, in the condition's colour", () => {
        expect(scale("good_winter")).toEqual([
            { condition: "good_winter", lit: true },
            { condition: "good_winter", lit: true },
            { condition: "good_winter", lit: true },
            { condition: "good_winter", lit: true },
            { condition: "fair", lit: false },
            { condition: "good", lit: false },
        ]);
        expect(scale("very_slippery").filter((part) => part.lit)).toHaveLength(1);
        expect(scale("good").every((part) => part.lit && part.condition === "good")).toBe(true);
        expect(scale(undefined).some((part) => part.lit)).toBe(false);
    });

    it("shows gusts only when they exceed the mean wind by 3 m/s, in whatever unit the sensors are", () => {
        const wind = (state: string, unit?: string): HassEntity => ({
            entity_id: "sensor.wind",
            state,
            last_changed: "",
            attributes: unit ? { unit_of_measurement: unit } : {},
        });
        expect(showGusts(wind("3.1", "m/s"), wind("7.3", "m/s"))).toBe(true);
        expect(showGusts(wind("3.0", "m/s"), wind("6.0", "m/s"))).toBe(true);
        expect(showGusts(wind("5.2", "m/s"), wind("6.0", "m/s"))).toBe(false);
        // 5 and 6 m/s in km/h: 3.6 apart in numbers, but only 1 m/s in wind.
        expect(showGusts(wind("18.0", "km/h"), wind("21.6", "km/h"))).toBe(false);
        expect(showGusts(wind("18.0", "km/h"), wind("10.0", "m/s"))).toBe(true);
        expect(showGusts(wind("10", "kn"), wind("17", "kn"))).toBe(true);
        // A unit the card doesn't know: any gust above the mean.
        expect(showGusts(wind("3", "Beaufort"), wind("4", "Beaufort"))).toBe(true);
        expect(showGusts(wind("3"), wind("3"))).toBe(false);
    });

    it("shows precipitation by its type when the station tells it, otherwise by its amount code", () => {
        expect(precipitation("freezing_rain", "moderate")).toEqual({ icon: "wi:rain-mix", text: "freezing_rain", notable: true });
        expect(precipitation("rain", "light")).toEqual({ icon: "wi:showers", text: "rain", notable: false });
        expect(precipitation("sleet", "heavy_snow")).toEqual({ icon: "wi:sleet", text: "heavy_sleet", notable: true });
        expect(precipitation("hail", "heavy")).toEqual({ icon: "wi:hail", text: "hail", notable: true });
        expect(precipitation(undefined, "moderate_snow")).toEqual({ icon: "wi:snow", text: "snow_or_sleet", notable: false });
        expect(precipitation(undefined, "heavy_snow")).toEqual({ icon: "wi:snow", text: "heavy_snow_or_sleet", notable: true });
        expect(precipitation("something_new", "light")).toEqual({ icon: "wi:sprinkle", text: "rain", notable: false });
        expect(precipitation(undefined, "something_new")).toEqual({ icon: "wi:na", text: undefined, notable: false });
    });
});
