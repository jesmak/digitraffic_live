import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import "../src/road-conditions-card";
import { valueColumns, type RoadConditionsCard } from "../src/road-conditions-card";
import type { RoadConditionsCardConfig } from "../src/types";
import { DRY, hass, SPARSE, type Readings } from "./fixtures";

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

// happy-dom lays nothing out, so each part is given the box it would have, measured from the card's top, drawn at `scale`.
function box(target: Element, top: number, bottom: number, scale = 1): void {
    target.getBoundingClientRect = () =>
        ({ top: top * scale, bottom: bottom * scale, height: (bottom - top) * scale, width: 300 * scale }) as DOMRect;
}

/** Gives the card a width and its last part a box ending at `end`, drawn at `scale` as a dialog opening draws the card. */
function laidOut(element: RoadConditionsCard, end: number, scale = 1): void {
    const haCard = one(element, "ha-card");
    Object.defineProperty(haCard, "clientWidth", { value: 300, configurable: true });
    box(haCard, 0, 56, scale);
    const parts = haCard.querySelectorAll(":scope > .card-title, :scope > .name, :scope > .station > *, :scope > .rows > .row");
    box(parts[parts.length - 1], end - 32, end, scale);
}

function style(element: RoadConditionsCard): string {
    return one(element, "ha-card").getAttribute("style") ?? "";
}

/** Lays the card out with its last part ending at `end`, drawn at `scale`, fills its rows and returns its style. */
async function filled(element: RoadConditionsCard, end: number, scale = 1): Promise<string> {
    laidOut(element, end, scale);
    // The width it is laid out at, which a scale doesn't change.
    const haCard = one(element, "ha-card");
    const computed = window.getComputedStyle;
    vi.spyOn(window, "getComputedStyle").mockImplementation((target, pseudo) =>
        target === haCard ? ({ ...computed(target, pseudo), width: "300px" } as CSSStyleDeclaration) : computed(target, pseudo),
    );
    (element as unknown as { fillRows(): void }).fillRows();
    vi.restoreAllMocks();
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

    // The content is 120.4 px, a fraction over two rows, and then 216 px drawn at 0.8.
    it.each([
        ["takes the next row for a content a fraction of a pixel over one", 109.4, 1, "min-height: 184px; --spare: 63px"],
        [
            "measures a card drawn scaled, as a dialog opening draws it, in the layout's pixels",
            205,
            0.8,
            "min-height: 248px; --spare: 32px",
        ],
    ])("%s", async (_name, end, scale, style) => {
        expect(await filled(await card({}, "grid"), end, scale)).toBe(style);
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
        ["on rows set in the layout tab", { grid_options: { rows: 5 } }, "grid", "height: 100%"],
    ])("leaves its rows alone %s", async (_name, config, layout, style) => {
        expect(await filled(await card(config as Partial<RoadConditionsCardConfig>, layout), 139)).toBe(style);
    });

    // 500 px rounded down to the rows is 440.
    it.each([
        ["under it, on the rows its content needs", 139, "max-height: 440px; min-height: 184px; --spare: 34px"],
        ["over it, on the limit rounded down to the rows", 600, "max-height: 440px; min-height: 440px; --spare: 0px"],
    ])("grows up to a limit on automatic rows %s", async (_name, end, style) => {
        expect(await filled(await card({ max_height: 500 }, "grid"), end)).toBe(style);
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

describe("a part on a line of its own only when it doesn't fit", () => {
    // happy-dom lays nothing out, so a row is drawn from 0 to WIDTH, and its parts, while the card measures, end where
    // its width on one line says. The meter's labels are LABELS wide together, each at the width given, and the middle one takes nothing while hidden.
    const WIDTH = 300;
    const LABELS = 260;
    const natural = new Map<Element, number>();
    let measuredSplit = false;
    const own = (name: string) => Object.getOwnPropertyDescriptor(HTMLElement.prototype, name);
    const saved = { clientWidth: own("clientWidth"), getBoundingClientRect: own("getBoundingClientRect") };
    const measuring = (element: Element) => !!element.closest("ha-card")?.hasAttribute("data-measuring");
    const isRow = (element: Element | null) => !!element?.matches(".rows > .row");
    const rect = (width: number, left = 0) => ({ left, right: width, width: width - left, top: 0, bottom: 0, height: 0 }) as DOMRect;

    beforeEach(() => {
        natural.clear();
        measuredSplit = false;
        Object.defineProperty(HTMLElement.prototype, "clientWidth", {
            configurable: true,
            get: () => WIDTH,
        });
        Object.defineProperty(HTMLElement.prototype, "getBoundingClientRect", {
            configurable: true,
            writable: true,
            value(this: HTMLElement) {
                const parent = this.parentElement;
                if (isRow(this)) {
                    return rect(WIDTH);
                }
                if (isRow(parent) && measuring(this)) {
                    measuredSplit ||= parent!.classList.contains("split");
                    return rect(natural.get(parent!) ?? WIDTH);
                }
                if (this.classList.contains("values")) {
                    return rect(WIDTH);
                }
                if (this.classList.contains("scale-labels")) {
                    return rect(LABELS);
                }
                if (parent?.classList.contains("scale-labels")) {
                    const hidden = parent.classList.contains("tight") && this === parent.children[1];
                    return rect(hidden ? 0 : (natural.get(this) ?? 60));
                }
                return rect(0);
            },
        });
    });

    afterEach(() => {
        for (const [name, descriptor] of Object.entries(saved)) {
            if (descriptor) {
                Object.defineProperty(HTMLElement.prototype, name, descriptor);
            } else {
                delete (HTMLElement.prototype as unknown as Record<string, unknown>)[name];
            }
        }
    });

    function split(element: RoadConditionsCard): void {
        (element as unknown as { splitLines(): void }).splitLines();
    }

    it.each<[string, boolean[], string[]]>([
        ["every row fits", [false, false, false], ["one line", "one line", "one line"]],
        ["a row doesn't fit", [false, true, false], ["one line", "split", "one line"]],
        ["no row fits", [true, true, true], ["split", "split", "split"]],
    ])("keeps a row's grade beside its name and values while they fit, when %s", async (_name, over, expected) => {
        const element = await card({ stations: ["station-a", "station-b", "station-c"] });
        const rows = [...element.shadowRoot!.querySelectorAll<HTMLElement>(".rows > .row")];
        const shown = () => rows.map((row) => (row.classList.contains("split") ? "split" : "one line"));
        rows.forEach((row, index) => natural.set(row, WIDTH + (over[index] ? 0.4 : 0)));
        split(element);
        expect(shown()).toEqual(expected);
        // A row already split is measured on one line again, so it goes back when it fits once more.
        rows.forEach((row) => natural.set(row, WIDTH));
        split(element);
        expect(shown()).toEqual(["one line", "one line", "one line"]);
        expect(measuredSplit).toBe(false);
    });

    // The values have 300 px and an 8 px gap between columns: n columns fit while n × widest + (n − 1) × 8 is at most 300,
    // and of those, the fewest that keep the fewest lines win.
    it.each([
        [30, 6],
        [40, 6],
        [60, 3],
        [92, 3],
        [146, 2],
        [147, 1],
        [400, 1],
    ])("gives one station's values, all %i px wide, %i columns", async (widest, columns) => {
        const element = await card();
        const values = one(element, ".values");
        expect(values.children.length).toBe(6);
        for (const value of values.children) {
            (value as HTMLElement).getBoundingClientRect = () => ({ width: measuring(value) ? widest : 10 }) as DOMRect;
        }
        split(element);
        expect(values.style.getPropertyValue("--value-columns")).toBe(String(columns));
    });

    // The values of a station on a card 250 px wide, 216 px for the values, Freezing rain far the widest.
    const MIXED = [80, 70, 50, 75, 170, 75];
    it.each<[string, number[], number, number, number[]]>([
        ["all as wide, on the fewest lines, three and three rather than four and two", [60, 60, 60, 60, 60, 60], 300, 3, []],
        ["one on two columns that starts the next line, which makes three columns no shorter than two", [60, 60, 150, 60, 60], 300, 2, [2]],
        ["one far wider, on two columns rather than all in one", MIXED, 216, 2, [4]],
        ["one far wider, with room for four columns", MIXED, 366, 4, [4]],
        ["one wider than two columns can be, in one column", [80, 70, 50, 75, 250, 75], 216, 1, []],
        ["every one narrow, all on one line", [40, 40, 40, 40, 40, 40], 300, 6, []],
        ["a single value", [90], 300, 1, []],
        // Three columns of 81.1 and their gaps: worked back out of the room, a column comes to a hair under 81.1, and only
        // the hundredth of a pixel's slack keeps the values in one column each.
        ["each exactly as wide as a column worked out in fractions", [81.1, 81.1, 81.1], 3 * 81.1 + 16, 3, []],
        [
            "one exactly as wide as two columns and their gap, worked out in fractions",
            [2 * 81.1 + 8, 81.1, 81.1, 81.1, 81.1],
            3 * 81.1 + 16,
            3,
            [0],
        ],
    ])("lays out values %s", (_name, widths, room, columns, wide) => {
        const result = valueColumns(widths, room, 8);
        expect(result.columns).toBe(columns);
        expect(result.wide.flatMap((two, index) => (two ? [index] : []))).toEqual(wide);
    });

    it("works the columns out from the values' drawn width, not the whole pixels clientWidth rounds it to", async () => {
        const element = await card();
        const values = one(element, ".values");
        // 205.6 px drawn leaves two columns of 98.8 px, too narrow for a value of 98.9, which 206 px would take for 99.
        values.getBoundingClientRect = () => rect(205.6);
        Object.defineProperty(values, "clientWidth", { configurable: true, value: 206 });
        const cells = [...values.children] as HTMLElement[];
        cells.forEach((value, index) => {
            value.getBoundingClientRect = () => ({ width: measuring(value) ? (index === 1 ? 98.9 : 80) : 10 }) as DOMRect;
        });
        split(element);
        expect(cells.map((value) => value.style.gridColumn)).toEqual(["", "span 2", "", "", "", ""]);
    });

    it("works the columns out in the layout's pixels when drawn scaled, as a dialog opening draws the card", async () => {
        const element = await card();
        const haCard = one(element, "ha-card");
        const values = one(element, ".values");
        // At 0.8: values of 146 px in 300 px fit two columns with the 8 px gap, which their drawn 116.8 px in 240 would not.
        haCard.getBoundingClientRect = () => rect(300 * 0.8);
        values.getBoundingClientRect = () => rect(300 * 0.8);
        for (const value of values.children) {
            (value as HTMLElement).getBoundingClientRect = () => ({ width: measuring(value) ? 146 * 0.8 : 10 }) as DOMRect;
        }
        const real = window.getComputedStyle.bind(window);
        vi.spyOn(window, "getComputedStyle").mockImplementation((target, pseudo) =>
            target === haCard
                ? ({ ...real(target, pseudo), width: "300px" } as CSSStyleDeclaration)
                : target === values
                  ? ({ ...real(target, pseudo), columnGap: "8px" } as CSSStyleDeclaration)
                  : real(target, pseudo),
        );
        split(element);
        vi.restoreAllMocks();
        expect(values.style.getPropertyValue("--value-columns")).toBe("2");
    });

    it("puts a value on two columns when it is too wide for one", async () => {
        const element = await card();
        const values = [...one(element, ".values").children] as HTMLElement[];
        values.forEach((value, index) => {
            value.getBoundingClientRect = () => ({ width: measuring(value) ? (index === 2 ? 200 : 80) : 10 }) as DOMRect;
        });
        split(element);
        expect(one(element, ".values").style.getPropertyValue("--value-columns")).toBe("2");
        expect(values.map((value) => value.style.gridColumn)).toEqual(["", "", "span 2", "", "", ""]);
        values.forEach((value) => (value.getBoundingClientRect = () => ({ width: measuring(value) ? 80 : 10 }) as DOMRect));
        split(element);
        expect(values.map((value) => value.style.gridColumn)).toEqual(["", "", "", "", "", ""]);
    });

    // Each end label has half of what the middle one and the gaps beside it leave of the 260 px.
    it.each([
        ["shows the middle label while every label fits", [80, 60, 80], false],
        ["drops the middle label when an end label doesn't fit", [101, 60, 80], true],
        ["drops the middle label when it leaves the ends too little", [80, 110, 80], true],
        ["drops the middle label when an end label fits only without the gaps beside it", [93, 60, 80], true],
    ])("%s", async (_name, widths, tight) => {
        // The meter's gap, which happy-dom doesn't read from the card's styles.
        const real = window.getComputedStyle.bind(window);
        vi.spyOn(window, "getComputedStyle").mockImplementation((element, pseudo) =>
            element.classList.contains("scale-labels") ? ({ columnGap: "8px" } as CSSStyleDeclaration) : real(element, pseudo),
        );
        const element = await card();
        const labels = one(element, ".scale-labels");
        [...labels.children].forEach((label, index) => natural.set(label, widths[index]));
        labels.classList.add("tight");
        split(element);
        expect(labels.classList.contains("tight")).toBe(tight);
        vi.restoreAllMocks();
    });

    it.each<[string, Partial<RoadConditionsCardConfig>, string, Readings | undefined, string[]]>([
        ["the rows of several stations", { stations: ["station-a", "station-b"] }, ".rows > .row", undefined, ["96px", "64px"]],
        ["one station's meter labels and values", {}, ".scale-labels, .values", undefined, ["96px", "64px"]],
        ["the values of a station without a meter", {}, ".scale-labels, .values", SPARSE, ["96px"]],
    ])(
        "holds %s to their layout height while it measures, so nothing around the card moves",
        async (_name, config, selector, readings, expected) => {
            const element = await card(config);
            if (readings) {
                element.hass = hass({ "station-a": readings });
                await element.updateComplete;
            }
            const parts = [...element.shadowRoot!.querySelectorAll<HTMLElement>(selector)];
            expect(parts.length).toBe(expected.length);
            const drawn = new Map(parts.map((part, index) => [part, ["96px", "64px"][index]]));
            const real = window.getComputedStyle.bind(window);
            vi.spyOn(window, "getComputedStyle").mockImplementation((target, pseudo) =>
                drawn.has(target as HTMLElement)
                    ? ({ height: drawn.get(target as HTMLElement), columnGap: "8px" } as CSSStyleDeclaration)
                    : real(target, pseudo),
            );
            // What each part is held to when the card starts measuring.
            const held: string[] = [];
            const ha = one(element, "ha-card");
            const toggle = ha.toggleAttribute.bind(ha);
            ha.toggleAttribute = (name: string, force?: boolean) => {
                if (name === "data-measuring" && force) {
                    // Its least height too, as a row held by its height alone still shrinks in a held card's flex column.
                    held.push(...parts.map((part) => (part.style.minHeight === part.style.height ? part.style.height : "not held")));
                }
                return toggle(name, force);
            };
            split(element);
            vi.restoreAllMocks();
            expect(held).toEqual(expected);
            expect(parts.map((part) => part.style.height + part.style.minHeight)).toEqual(expected.map(() => ""));
        },
    );

    it("measures nothing while the card has no width", async () => {
        const element = await card({ stations: ["station-a", "station-b"] });
        Object.defineProperty(one(element, "ha-card"), "clientWidth", { value: 0, configurable: true });
        const rows = [...element.shadowRoot!.querySelectorAll<HTMLElement>(".rows > .row")];
        rows.forEach((row) => natural.set(row, WIDTH + 40));
        split(element);
        expect(rows.map((row) => row.classList.contains("split"))).toEqual([false, false]);
    });
});
