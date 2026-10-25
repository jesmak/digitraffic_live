import { expect, test, vi } from "vitest";

// A file of its own, as the first copy has to be loaded into a page that has none.
test("the first copy registers the card and its editor, lists it in the picker and logs its version", async () => {
    const info = vi.spyOn(console, "info").mockImplementation(() => undefined);

    await import("../src/road-conditions-card");

    expect(customElements.get("road-conditions-card")).toBeDefined();
    expect(customElements.get("road-conditions-card-editor")).toBeDefined();
    const registry = window as unknown as { customCards?: { type: string }[] };
    expect(registry.customCards?.filter((card) => card.type === "road-conditions-card")).toEqual([
        {
            type: "road-conditions-card",
            name: "Road conditions",
            description: expect.any(String),
            documentationURL: "https://github.com/jesmak/digitraffic_live#road-conditions-card",
            preview: true,
        },
    ]);
    expect(info).toHaveBeenCalledTimes(1);
    expect(info.mock.calls[0]?.[0]).toContain("ROAD-CONDITIONS-CARD");
});
