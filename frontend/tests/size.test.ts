import { afterEach, describe, expect, it, vi } from "vitest";

import "../src/road-conditions-card";
import type { RoadConditionsCard } from "../src/road-conditions-card";
import type { RoadConditionsCardConfig } from "../src/types";
import { DRY, hass } from "./fixtures";

async function card(config: Partial<RoadConditionsCardConfig> = {}, layout?: string): Promise<RoadConditionsCard> {
    const element = document.createElement("road-conditions-card");
    element.setConfig({ type: "custom:road-conditions-card", stations: ["station-a"], ...config } as RoadConditionsCardConfig);
    element.layout = layout;
    element.hass = hass({ "station-a": DRY, "station-b": DRY, "station-c": DRY });
    document.body.append(element);
    await element.updateComplete;
    return element;
}

function one(element: Element, selector: string): HTMLElement {
    return element.shadowRoot!.querySelector<HTMLElement>(selector)!;
}

// happy-dom lays nothing out, so each part is given the box it would have, measured from the card's top.
function box(target: Element, top: number, bottom: number): void {
    target.getBoundingClientRect = () => ({ top, bottom, height: bottom - top, width: 300 }) as DOMRect;
}

/** Gives the card a width and its last part a box ending at `end`. */
function laidOut(element: RoadConditionsCard, end: number): void {
    const haCard = one(element, "ha-card");
    Object.defineProperty(haCard, "clientWidth", { value: 300, configurable: true });
    box(haCard, 0, 56);
    const parts = haCard.querySelectorAll(":scope > .card-title, :scope > .name, :scope > .station > *, :scope > .rows > .row");
    box(parts[parts.length - 1], end - 32, end);
}

function style(element: RoadConditionsCard): string {
    return one(element, "ha-card").getAttribute("style") ?? "";
}

/** Lays the card out with its last part ending at `end`, fills its rows and returns its style. */
async function filled(element: RoadConditionsCard, end: number): Promise<string> {
    laidOut(element, end);
    (element as unknown as { fillRows(): void }).fillRows();
    await element.updateComplete;
    return style(element);
}

afterEach(() => {
    document.body.innerHTML = "";
});

describe("filling the rows of a sections view", () => {
    // The content ends 11 px of padding under its last part: at 150 px with it ending at 139.
    it.each([
        ["whole rows", {}, "min-height: 184px; --spare: 34px"],
        ["half rows", { row_step: "half" as const }, "min-height: 152px; --spare: 2px"],
    ])("on automatic rows, ends on %s", async (_name, config, style) => {
        expect(await filled(await card(config, "grid"), 139)).toBe(style);
    });

    it.each<[string, Partial<RoadConditionsCardConfig>, string, string]>([
        ["under one station's name", { title: "Tiet" }, ".name", "padding-bottom"],
        ["under one station's name without a title", {}, ".name", "padding-bottom"],
        ["under the title of several stations", { title: "Tiet", stations: ["station-a", "station-b"] }, ".card-title", "padding-bottom"],
        ["above several stations without a title", { stations: ["station-a", "station-b"] }, ".rows", "padding-top"],
    ])("puts the spare room %s, and doesn't count it again once drawn", async (_name, config, holder, side) => {
        const element = await card(config, "grid");
        const holders = element.shadowRoot!.querySelectorAll(".spare, .spare-top");
        expect([...holders]).toEqual([one(element, holder)]);
        expect(await filled(element, 139)).toBe("min-height: 184px; --spare: 34px");
        one(element, holder).style.setProperty(side, "34px");
        expect(await filled(element, 173)).toBe("min-height: 184px; --spare: 34px");
    });

    it("measures to its last part's end, never an element a theme adds after it", async () => {
        const element = await card({}, "grid");
        const added = document.createElement("div");
        box(added, 0, 900);
        one(element, "ha-card").append(added);
        expect(await filled(element, 139)).toBe("min-height: 184px; --spare: 34px");
    });

    it.each([
        ["outside a sections view", {}, undefined, ""],
        ["held up to a limit", { max_height: 500 }, "grid", "max-height: 500px"],
        ["on rows set in the layout tab", { grid_options: { rows: 5 } }, "grid", "height: 100%"],
    ])("leaves its rows alone %s", async (_name, config, layout, style) => {
        expect(await filled(await card(config as Partial<RoadConditionsCardConfig>, layout), 139)).toBe(style);
    });

    // Each change takes the card off automatic rows, and changing back must not bring the old fill with it before the card
    // is measured again.
    const AUTO = { type: "custom:road-conditions-card", stations: ["station-a"] } as RoadConditionsCardConfig;
    it.each<[string, (element: RoadConditionsCard) => void, string, (element: RoadConditionsCard) => void]>([
        ["moved out of a sections view", (element) => (element.layout = undefined), "", (element) => (element.layout = "grid")],
        [
            "held to a fixed height",
            (element) => element.setConfig({ ...AUTO, height: 300 }),
            "height: 300px",
            (element) => element.setConfig(AUTO),
        ],
        [
            "held up to a limit",
            (element) => element.setConfig({ ...AUTO, max_height: 500 }),
            "max-height: 500px",
            (element) => element.setConfig(AUTO),
        ],
        [
            "held by rows set in the layout tab",
            (element) => element.setConfig({ ...AUTO, grid_options: { rows: 5 } }),
            "height: 100%",
            (element) => element.setConfig({ ...AUTO, grid_options: { rows: "auto" } }),
        ],
        [
            "held by rows set in the older layout options",
            (element) => element.setConfig({ ...AUTO, layout_options: { grid_rows: 5 } }),
            "height: 100%",
            (element) => element.setConfig({ ...AUTO, layout_options: { grid_rows: "auto" } }),
        ],
    ])("lets go of the rows it filled once %s", async (_name, change, held, back) => {
        const element = await card({}, "grid");
        expect(await filled(element, 139)).toBe("min-height: 184px; --spare: 34px");
        change(element);
        await element.updateComplete;
        expect(await filled(element, 139)).toBe(held);
        back(element);
        await element.updateComplete;
        expect(style(element)).toBe("");
    });

    it("is observed again when it comes back on the page, and fills its rows on a resize", async () => {
        // The scroll fades have observers of their own, so the card's is the one given the card.
        const observed: Element[] = [];
        let resized: (entries: unknown[]) => void = () => {};
        vi.stubGlobal(
            "ResizeObserver",
            class {
                constructor(private readonly callback: (entries: unknown[]) => void) {}
                observe(target: Element) {
                    observed.push(target);
                    if (target.tagName === "HA-CARD") {
                        resized = this.callback;
                    }
                }
                unobserve() {}
                disconnect() {}
            },
        );
        try {
            const element = await card({}, "grid");
            const haCard = one(element, "ha-card");
            expect(observed).toContain(haCard);
            element.remove();
            observed.length = 0;
            document.body.append(element);
            await element.updateComplete;
            expect(observed).toEqual([haCard]);
            // The frame its own update asked for passes before it has a size, so only the resize can fill its rows.
            const frame = () => new Promise((done) => requestAnimationFrame(() => done(undefined)));
            await frame();
            expect(style(element)).toBe("");
            laidOut(element, 139);
            resized([]);
            await frame();
            await element.updateComplete;
            expect(style(element)).toBe("min-height: 184px; --spare: 34px");
        } finally {
            vi.unstubAllGlobals();
        }
    });
});

describe("texts cut short when held", () => {
    it("carry their whole text as a tooltip", async () => {
        const single = await card({ title: "Ajokeli kotimatkalla" });
        const root = single.shadowRoot!;
        expect(root.querySelector(".card-title")!.getAttribute("title")).toBe("Ajokeli kotimatkalla");
        const name = root.querySelector(".name")!;
        expect(name.getAttribute("title")).toBe(name.textContent!.trim());
        const grade = root.querySelector(".grade-text")!;
        expect(grade.getAttribute("title")).toBe(grade.textContent!.trim());

        const several = await card({ stations: ["station-a", "station-b"] });
        const row = several.shadowRoot!.querySelector(".row")!;
        const rowName = row.querySelector(".row-name")!;
        expect(rowName.getAttribute("title")).toBe(rowName.textContent!.trim());
        // The values' tooltip names each value with what it reads, as the row says them for a screen reader.
        const values = row.querySelector(".row-values")!.getAttribute("title")!;
        expect(row.getAttribute("aria-label")).toContain(values);
        expect(values.split(", ").length).toBe(row.querySelectorAll(".row-value").length);
    });
});
