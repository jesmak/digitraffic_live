import { afterEach, describe, expect, it } from "vitest";

import "../src/road-conditions-card";
import type { RoadConditionsCard } from "../src/road-conditions-card";
import { compactStations } from "../src/editor";
import type { HomeAssistant } from "../src/hass";
import type { RoadConditionsCardConfig } from "../src/types";
import { DRY, SNOW, SPARSE, hass } from "./fixtures";

async function card(state: HomeAssistant, config: Partial<RoadConditionsCardConfig>): Promise<RoadConditionsCard> {
    const element = document.createElement("road-conditions-card");
    element.setConfig({ type: "custom:road-conditions-card", stations: ["station-a"], ...config } as RoadConditionsCardConfig);
    element.hass = state;
    document.body.append(element);
    await element.updateComplete;
    return element;
}

function text(element: Element | null | undefined): string {
    return (element?.textContent ?? "").replace(/\s+/g, " ").trim();
}

function icons(root: ShadowRoot, selector: string): string[] {
    return [...root.querySelectorAll(`${selector} .icon`)].map((icon) => icon.getAttribute("data-icon") ?? "");
}

describe("road-conditions-card", () => {
    afterEach(() => {
        document.body.innerHTML = "";
    });

    it("refuses a configuration without stations", () => {
        const element = document.createElement("road-conditions-card");
        expect(() => element.setConfig({ type: "custom:road-conditions-card", stations: [] })).toThrow();
        // One station written without the list is refused with the card's own message, not a TypeError.
        const single = { type: "custom:road-conditions-card", stations: "station-a" } as unknown as RoadConditionsCardConfig;
        expect(() => element.setConfig(single)).toThrow("Invalid configuration");
        // A station with a misspelt key is pointed out, not dropped while the others are shown.
        const misspelt = {
            type: "custom:road-conditions-card",
            stations: ["station-a", { devcie: "station-b" }],
        } as unknown as RoadConditionsCardConfig;
        expect(() => element.setConfig(misspelt)).toThrow("Every station needs its device");
    });

    it("shows one station with its grade on the scale and its values as icons", async () => {
        const root = (await card(hass({ "station-a": DRY }), {})).shadowRoot as ShadowRoot;
        expect(text(root.querySelector(".name"))).toBe("Road 1 Example, station-a");
        expect(text(root.querySelector(".grade-text"))).toBe("good");
        expect(text(root.querySelector(".grade .grip"))).toBe("0,82 µ");
        expect([...root.querySelectorAll(".scale.large .part.lit")]).toHaveLength(6);
        expect(icons(root, ".value")).toEqual([
            "mdi:road-variant",
            "wi:thermometer",
            "mdi:layers-outline",
            "wi:strong-wind",
            "wi:cloud",
            "wi:fog",
        ]);
        // Weather Icons are drawn inline, the road's icons by Home Assistant.
        expect(root.querySelector(".value.wind svg path")?.getAttribute("d")).toMatch(/^M/);
        expect(root.querySelector(".value.road_surface ha-icon")).not.toBeNull();
        // Gusts of 7.3 stand out from a mean of 3.1, so they are shown.
        expect(text(root.querySelector(".value.wind"))).toBe("3,1 m/s (7,3 m/s)");
        expect(root.querySelector(".value.wind")?.getAttribute("aria-label")).toBe("Tuuli 3,1 m/s (7,3 m/s)");
        // A short word beside the icon, the full state in the tooltip.
        expect(text(root.querySelector(".value.precipitation"))).toBe("Pouta");
        expect(root.querySelector(".value.precipitation")?.getAttribute("title")).toBe("Sade: none");
        expect(root.querySelector(".warning")).toBeNull();
    });

    it("shows a winter road amber, with the amount of snow and the warning", async () => {
        const root = (await card(hass({ "station-a": SNOW }), {})).shadowRoot as ShadowRoot;
        // The first three parts are lit in fair winter's colour, the rest faint in their own.
        expect([...root.querySelectorAll(".scale.large .part")].map((part) => part.className)).toEqual([
            "part grip-fair_winter lit",
            "part grip-fair_winter lit",
            "part grip-fair_winter lit",
            "part grip-good_winter ",
            "part grip-fair ",
            "part grip-good ",
        ]);
        expect(icons(root, ".value.precipitation")).toEqual(["wi:snow"]);
        expect(text(root.querySelector(".value.precipitation"))).toBe("Lumi");
        expect(root.querySelector(".value.precipitation")?.getAttribute("title")).toBe("Sade: snow, 0,4 mm/h");
        // Gusts of 6.0 are within 3 m/s of the mean.
        expect(text(root.querySelector(".value.wind"))).toBe("5,2 m/s");
        expect(text(root.querySelector(".warning"))).toBe("Tiesäävaroitus: beware");
    });

    it("leaves out what a station doesn't measure", async () => {
        const root = (await card(hass({ "station-b": SPARSE }), { stations: ["station-b"] })).shadowRoot as ShadowRoot;
        expect(root.querySelector(".grade")).toBeNull();
        expect(root.querySelector(".scale")).toBeNull();
        expect(root.querySelectorAll(".value")).toHaveLength(5);
        expect(root.querySelector(".value.road_surface")).toBeNull();
    });

    it("falls back to the amount code without a present weather sensor", async () => {
        const root = (await card(hass({ "station-b": SPARSE }), { stations: ["station-b"] })).shadowRoot as ShadowRoot;
        expect(icons(root, ".value.precipitation")).toEqual(["wi:sprinkle"]);
        expect(text(root.querySelector(".value.precipitation"))).toBe("Sade");
    });

    it("shows freezing or heavy precipitation in the warning colour, in the rows too", async () => {
        const state = hass({
            "station-a": { ...DRY, precipitation_type: ["freezing_rain"] },
            "station-c": { ...SNOW, precipitation: ["heavy_snow"] },
        });
        const root = (await card(state, {})).shadowRoot as ShadowRoot;
        expect(root.querySelector(".value.precipitation")?.classList.contains("notable")).toBe(true);
        expect(text(root.querySelector(".value.precipitation"))).toBe("Jäätävä sade");
        const rows = (await card(state, { stations: ["station-a", "station-c", "station-b"] })).shadowRoot as ShadowRoot;
        expect([...rows.querySelectorAll(".row-value.notable")].map(text)).toEqual(["Jäätävä sade", "Runsas lumisade"]);
    });

    it("leaves out a value that is unavailable for now", async () => {
        const state = hass({ "station-a": DRY });
        const id = "sensor.tie_station_a_visibility_fi";
        state.states[id] = { ...(state.states[id] as NonNullable<(typeof state.states)[string]>), state: "unavailable" };
        const root = (await card(state, {})).shadowRoot as ShadowRoot;
        expect(root.querySelector(".value.visibility")).toBeNull();
    });

    it("names heavy precipitation by its amount in the tooltip too", async () => {
        const root = (await card(hass({ "station-a": { ...SNOW, precipitation: ["heavy_snow"] } }), {})).shadowRoot as ShadowRoot;
        expect(text(root.querySelector(".value.precipitation"))).toBe("Runsas lumisade");
        expect(root.querySelector(".value.precipitation")?.getAttribute("title")).toBe("Sade: snow, heavy_snow, 0,4 mm/h");
    });

    it("says so when none of a station's sensors has a reading", async () => {
        const state = hass({ "station-a": DRY, "station-c": SNOW });
        for (const [id, entity] of Object.entries(state.states)) {
            if (entity && id.includes("station_a")) {
                state.states[id] = { ...entity, state: "unavailable" };
            }
        }
        const root = (await card(state, {})).shadowRoot as ShadowRoot;
        expect(text(root.querySelector(".name"))).toBe("Road 1 Example, station-a");
        expect(text(root.querySelector(".message"))).toBe("Asemalta ei juuri nyt saada lukemia");
        const rows = (await card(state, { stations: ["station-a", "station-c"] })).shadowRoot as ShadowRoot;
        expect(text(rows.querySelector(".row .row-values"))).toBe("Asemalta ei juuri nyt saada lukemia");
    });

    it("says so when a station has no sensors", async () => {
        const root = (await card(hass({}), { stations: [{ device: "station-gone", name: "VT1" }] })).shadowRoot as ShadowRoot;
        expect(text(root.querySelector(".name"))).toBe("VT1");
        expect(text(root.querySelector(".message"))).toBe("Asemalta ei löytynyt sensoreita");
    });

    it("lists several stations as rows, those without grip without a grade", async () => {
        const root = (
            await card(hass({ "station-a": DRY, "station-c": SNOW, "station-b": SPARSE }), {
                title: "Kelit",
                stations: [{ device: "station-a", name: "VT1" }, "station-c", "station-b"],
            })
        ).shadowRoot as ShadowRoot;
        expect(text(root.querySelector(".card-title"))).toBe("Kelit");
        const rows = [...root.querySelectorAll(".row")];
        expect(rows.map((row) => text(row.querySelector(".row-name")))).toEqual([
            "VT1",
            "Road 1 Example, station-c",
            "Road 1 Example, station-b",
        ]);
        expect(text(rows[0].querySelector(".row-grade"))).toBe("good 0,82 µ");
        expect(rows[0].getAttribute("aria-label")).toBe("VT1, Tien lämpötila 5,3 °C, Tienpinta dry, Tuuli 3,1 m/s (7,3 m/s), good 0,82 µ");
        expect(rows[1].querySelectorAll(".row-grade .part.lit")).toHaveLength(3);
        expect(rows[2].querySelector(".row-grade")).toBeNull();
        expect(icons(root, ".row:first-child .row-values")).toEqual(["mdi:road-variant", "mdi:layers-outline", "wi:strong-wind"]);
    });

    it("lists a station without sensors as a row that can't be clicked", async () => {
        const root = (await card(hass({ "station-a": DRY }), { stations: ["station-a", "station-gone"] })).shadowRoot as ShadowRoot;
        const rows = [...root.querySelectorAll(".row")];
        expect(rows.map((row) => row.tagName)).toEqual(["BUTTON", "DIV"]);
        expect(text(rows[1].querySelector(".row-values"))).toBe("Asemalta ei löytynyt sensoreita");
    });

    it("opens a value's history when it is clicked", async () => {
        const element = await card(hass({ "station-a": DRY }), {});
        const opened: string[] = [];
        element.addEventListener("hass-more-info", (event) => opened.push((event as CustomEvent).detail.entityId));
        (element.shadowRoot?.querySelector(".value.visibility") as HTMLElement).click();
        (element.shadowRoot?.querySelector(".grade") as HTMLElement).click();
        expect(opened).toEqual(["sensor.tie_station_a_visibility_fi", "sensor.tie_station_a_grip_condition_fi"]);
    });

    it("redraws only when one of its stations' sensors changes", async () => {
        const state = hass({ "station-a": DRY, "station-b": SPARSE });
        const element = await card(state, {});
        let renders = 0;
        const original = element["render"].bind(element);
        element["render"] = () => {
            renders += 1;
            return original();
        };
        element.hass = {
            ...state,
            states: {
                ...state.states,
                "sensor.elsewhere": { entity_id: "sensor.elsewhere", state: "1", last_changed: "", attributes: {} },
            },
        };
        await element.updateComplete;
        expect(renders).toBe(0);
        const id = "sensor.tie_station_a_grip_fi";
        element.hass = {
            ...state,
            states: { ...state.states, [id]: { ...(state.states[id] as NonNullable<(typeof state.states)[string]>), state: "0.4" } },
        };
        await element.updateComplete;
        expect(renders).toBe(1);
        // A new language redraws the card even when no sensor has changed.
        element.hass = { ...element.hass, locale: { language: "en" } };
        await element.updateComplete;
        expect(renders).toBe(2);
        // A sensor removed from the registry is gone from the card, though its sensors were looked up before.
        const entities = { ...element.hass.entities };
        delete entities["sensor.tie_station_a_visibility_fi"];
        element.hass = { ...element.hass, entities };
        await element.updateComplete;
        expect(renders).toBe(3);
        expect(element.shadowRoot?.querySelector(".value.visibility")).toBeNull();
    });
});

describe("editor", () => {
    it("writes a station without a name as its device id", () => {
        expect(compactStations([{ device: "station-a" }, { device: "station-b", name: "VT1" }, { device: "" }])).toEqual([
            "station-a",
            { device: "station-b", name: "VT1" },
        ]);
    });
});
