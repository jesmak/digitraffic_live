import { afterEach, describe, expect, it } from "vitest";

import "../src/road-conditions-card";
import type { RoadConditionsCard } from "../src/road-conditions-card";
import { compactStations } from "../src/editor";
import type { HomeAssistant } from "../src/hass";
import { browserLanguage, translate } from "../src/localize/localize";
import type { RoadConditionsCardConfig } from "../src/types";
import { DRY, SNOW, SPARSE, hass } from "./fixtures";

async function card(state: HomeAssistant, config: Partial<RoadConditionsCardConfig>, layout?: string): Promise<RoadConditionsCard> {
    const element = document.createElement("road-conditions-card");
    element.setConfig({ type: "custom:road-conditions-card", stations: ["station-a"], ...config } as RoadConditionsCardConfig);
    element.hass = state;
    element.layout = layout;
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

    it("refuses a height that isn't a positive number of pixels, and an unknown height mode, with an error about the height", () => {
        const element = document.createElement("road-conditions-card");
        const config = (extra: Record<string, unknown>) =>
            ({ type: "custom:road-conditions-card", stations: ["station-a"], ...extra }) as never;
        const error = translate(browserLanguage(), "common.invalid_height");
        expect(error).toMatch(/^Invalid height\./);
        for (const value of ["300px", 0, -10]) {
            expect(() => element.setConfig(config({ max_height: value }))).toThrow(error);
            expect(() => element.setConfig(config({ height: value }))).toThrow(error);
        }
        expect(() => element.setConfig(config({ height_mode: "tall" }))).toThrow(error);
        // Left empty in YAML, each is unset.
        expect(() => element.setConfig(config({ height_mode: null, height: null, max_height: null }))).not.toThrow();
    });

    it.each<[string, string | undefined, Partial<RoadConditionsCardConfig>, string]>([
        ["its content", undefined, {}, ""],
        ["a fixed height", undefined, { height_mode: "fixed", height: 240, max_height: 300 }, "height: 240px"],
        ["a maximum height", undefined, { max_height: 300 }, "max-height: 300px"],
        ["grid rows in a sections view, over its mode", "grid", { height: 240, grid_options: { rows: 6 } }, "height: 100%"],
        ["its mode when the grid rows are automatic", "grid", { max_height: 300, grid_options: { rows: "auto" } }, "max-height: 300px"],
        ["a fixed height, with several stations", undefined, { stations: ["station-a", "station-b"], height: 240 }, "height: 240px"],
    ])("sizes itself by %s", async (_name, layout, extra, style) => {
        const element = await card(hass({ "station-a": DRY, "station-b": DRY }), extra, layout);
        const drawn = element.shadowRoot!.querySelector("ha-card")!;
        expect(drawn.getAttribute("style") ?? "").toBe(style);
        // Held to a height, the card is a column in which the station, or the list of them, scrolls under the title.
        expect(drawn.classList.contains("held")).toBe(style !== "");
        expect(drawn.querySelector(":scope > .station, :scope > .rows")).not.toBeNull();
    });

    const PARTS: Array<[string, Partial<RoadConditionsCardConfig>]> = [
        ["a station's view", {}],
        ["the list of stations", { stations: ["station-a", "station-b"] }],
    ];
    const HELD: Array<[string, string | undefined, Partial<RoadConditionsCardConfig>, string[]]> = [
        ["held to a height", undefined, { height: 240 }, ["fade-bottom"]],
        ["held up to a limit", undefined, { max_height: 300 }, ["fade-bottom"]],
        ["held by rows in a sections view", "grid", { grid_options: { rows: 4 } }, ["fade-bottom"]],
        [
            "held to a height with automatic rows in a sections view",
            "grid",
            { height: 240, grid_options: { rows: "auto" } },
            ["fade-bottom"],
        ],
        ["held by the older layout options' rows in a sections view", "grid", { layout_options: { grid_rows: 4 } }, ["fade-bottom"]],
        ["never in auto", undefined, {}, []],
        ["never in auto with automatic rows in a sections view", "grid", { grid_options: { rows: "auto" } }, []],
        ["never by grid rows outside a sections view", undefined, { grid_options: { rows: 4 } }, []],
    ];

    /** The card's scroller, made to run 400 px past its edge, as happy-dom lays nothing out. */
    async function overflowing(element: RoadConditionsCard): Promise<HTMLElement> {
        const scroller = element.shadowRoot!.querySelector<HTMLElement>("ha-card > .station, ha-card > .rows")!;
        Object.defineProperty(scroller, "scrollHeight", { value: 600, configurable: true });
        Object.defineProperty(scroller, "clientHeight", { value: 200, configurable: true });
        element.requestUpdate();
        await element.updateComplete;
        return scroller;
    }

    it.each(
        PARTS.flatMap(([part, stations]) =>
            HELD.map(([name, layout, extra, expected]) => [part, name, layout, { ...stations, ...extra }, expected] as const),
        ),
    )("fades the bottom edge of %s that runs past it when %s", async (_part, _name, layout, extra, expected) => {
        const scroller = await overflowing(await card(hass({ "station-a": DRY, "station-b": DRY }), extra, layout));
        expect(["fade-top", "fade-bottom"].filter((name) => scroller.classList.contains(name))).toEqual(expected);
    });

    it.each(PARTS)(
        "lets go of the fade of %s when the card goes from held to auto, and fades it again when held again",
        async (_part, stations) => {
            const element = await card(hass({ "station-a": DRY, "station-b": DRY }), { ...stations, height: 240 });
            const scroller = await overflowing(element);
            expect([...scroller.classList].filter((name) => name.startsWith("fade"))).toEqual(["fades", "fade-bottom"]);
            const config = { type: "custom:road-conditions-card", stations: ["station-a"], ...stations } as RoadConditionsCardConfig;
            element.setConfig(config);
            await element.updateComplete;
            expect([...scroller.classList].filter((name) => name.startsWith("fade"))).toEqual([]);
            element.setConfig({ ...config, height: 240 });
            await element.updateComplete;
            expect([...scroller.classList].filter((name) => name.startsWith("fade"))).toEqual(["fades", "fade-bottom"]);
        },
    );

    it("is held by its rows once moved into a sections view, even when another entity's change comes with it", async () => {
        const state = hass({ "station-a": DRY });
        const element = await card(state, { grid_options: { rows: 4 } });
        expect(element.shadowRoot!.querySelector("ha-card")!.getAttribute("style") ?? "").toBe("");
        element.layout = "grid";
        element.hass = {
            ...state,
            states: {
                ...state.states,
                "sensor.elsewhere": { entity_id: "sensor.elsewhere", state: "1", last_changed: "", attributes: {} },
            },
        } as HomeAssistant;
        await element.updateComplete;
        expect(element.shadowRoot!.querySelector("ha-card")!.getAttribute("style")).toBe("height: 100%");
    });

    it.each<[string, Partial<RoadConditionsCardConfig>, number]>([
        ["one station's content", {}, 4],
        ["three stations' content", { stations: ["station-a", "station-b", "station-c"] }, 4],
        ["a fixed height", { height: 400 }, 8],
        ["a maximum height below its content", { stations: ["station-a", "station-b", "station-c"], max_height: 150 }, 3],
    ])("sizes itself in a masonry view by %s", (_name, extra, size) => {
        const element = document.createElement("road-conditions-card");
        element.setConfig({ type: "custom:road-conditions-card", stations: ["station-a"], ...extra } as RoadConditionsCardConfig);
        expect(element.getCardSize()).toBe(size);
    });

    it.each<[string, Partial<RoadConditionsCardConfig>, number]>([
        ["one station", {}, 3],
        ["one station and a title", { title: "Tiet" }, 4],
        ["several stations", { stations: ["station-a", "station-b"] }, 2],
        ["several stations and a title", { stations: ["station-a", "station-b"], title: "Tiet" }, 3],
    ])("keeps to its minimum height in a sections view with %s", (_name, extra, rows) => {
        const element = document.createElement("road-conditions-card");
        element.setConfig({ type: "custom:road-conditions-card", stations: ["station-a"], ...extra } as RoadConditionsCardConfig);
        expect(element.getGridOptions().min_rows).toBe(rows);
    });

    it.each<[string, Partial<RoadConditionsCardConfig>, string]>([
        ["one station", { height: 100 }, "height: 173px"],
        ["several stations", { stations: ["station-a", "station-b"], height: 50 }, "height: 96px"],
    ])("raises a fixed height below its minimum to the minimum, with %s", async (_name, extra, style) => {
        const element = await card(hass({ "station-a": DRY, "station-b": DRY }), extra);
        expect(element.shadowRoot!.querySelector("ha-card")!.getAttribute("style")).toBe(style);
    });

    it("puts the title and the station's name ahead of the station's view, the grade, scale and values in it", async () => {
        const root = (await card(hass({ "station-a": SNOW }), { title: "Tiet", height: 200 })).shadowRoot!;
        const haCard = root.querySelector("ha-card")!;
        expect([...haCard.children].map((child) => child.classList[0])).toEqual(["card-title", "name", "station"]);
        const station = [...root.querySelector(".station")!.children].map((child) => child.classList[0]);
        expect(station.slice(0, 3)).toEqual(["grade", "scale", "scale-labels"]);
        expect(station).toContain("values");
    });

    it("puts the title ahead of the rows with several stations, a row per station in them", async () => {
        const root = (
            await card(hass({ "station-a": DRY, "station-b": DRY }), { title: "Tiet", stations: ["station-a", "station-b"], height: 200 })
        ).shadowRoot!;
        const haCard = root.querySelector("ha-card")!;
        expect([...haCard.children].map((child) => child.classList[0])).toEqual(["card-title", "rows"]);
        expect(root.querySelectorAll(".rows > .row")).toHaveLength(2);
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

    function saved(value: Record<string, unknown>): unknown[] {
        const editor = document.createElement("road-conditions-card-editor");
        const configs: unknown[] = [];
        editor.addEventListener("config-changed", (event) => configs.push((event as CustomEvent<{ config: unknown }>).detail.config));
        (editor as unknown as { changed(value: unknown): void }).changed({
            type: "custom:road-conditions-card",
            stations: [{ device: "station-a" }],
            ...value,
        });
        return configs;
    }

    it.each([
        ["the auto height mode it shows", { height_mode: "auto" }, {}],
        ["a height mode its height already gives", { height_mode: "fixed", height: 300 }, { height: 300 }],
    ])("leaves out of the configuration %s", (_name, height, kept) => {
        expect(saved(height)).toEqual([{ type: "custom:road-conditions-card", stations: ["station-a"], ...kept }]);
    });

    it("keeps only the height its mode uses, so one left from another mode can't come back", () => {
        const height = { height_mode: "max", height: 300, max_height: 500 };
        expect(saved(height)).toEqual([{ type: "custom:road-conditions-card", stations: ["station-a"], max_height: 500 }]);
    });

    it("puts the height fields in a form of their own after the stations' help, and saves them into the configuration", async () => {
        const editor = document.createElement("road-conditions-card-editor");
        editor.hass = { states: {}, entities: {}, devices: {}, locale: { language: "en" } } as unknown as HomeAssistant;
        editor.setConfig({ type: "custom:road-conditions-card", title: "Tiet", stations: ["station-a"], max_height: 500 });
        document.body.append(editor);
        await editor.updateComplete;
        const root = editor.shadowRoot!;
        expect([...root.children].map((child) => child.tagName.toLowerCase())).toEqual(["ha-form", "p", "ha-form"]);
        type Form = HTMLElement & { data: Record<string, unknown>; schema: Array<{ name: string }> };
        const [stations, height] = [...root.querySelectorAll<Form>("ha-form")];
        expect(stations.schema.map((entry) => entry.name)).toEqual(["title", "stations"]);
        expect(height.schema.map((entry) => entry.name)).toEqual(["height_mode", "max_height"]);
        expect(height.data).toMatchObject({ height_mode: "max", max_height: 500 });

        const configs: unknown[] = [];
        editor.addEventListener("config-changed", (event) => configs.push((event as CustomEvent<{ config: unknown }>).detail.config));
        height.dispatchEvent(
            new CustomEvent("value-changed", { detail: { value: { ...height.data, height_mode: "fixed", height: 300 } } }),
        );
        expect(configs).toEqual([{ type: "custom:road-conditions-card", title: "Tiet", stations: ["station-a"], height: 300 }]);
        editor.remove();
    });
});
