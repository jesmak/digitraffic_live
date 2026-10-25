import { expect, test, vi } from "vitest";

// A copy of the card installed on its own, before it came with the integration, may be loaded first.
test("a copy of the card loaded earlier stays the card, and the picker lists it once", async () => {
    class Earlier extends HTMLElement {}
    customElements.define("road-conditions-card", Earlier);
    const registry = window as unknown as { customCards?: unknown[] };
    registry.customCards = [{ type: "road-conditions-card" }];
    const info = vi.spyOn(console, "info").mockImplementation(() => undefined);

    await import("../src/road-conditions-card");

    expect(customElements.get("road-conditions-card")).toBe(Earlier);
    expect(registry.customCards).toHaveLength(1);
    expect(info).not.toHaveBeenCalled();
});
