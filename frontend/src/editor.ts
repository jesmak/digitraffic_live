/** The card's visual editor: the title, and the stations with the names the card gives them. */
import { LitElement, css, html, nothing } from "lit";
import type { CSSResultGroup, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { PLATFORM } from "./const";
import type { HomeAssistant } from "./hass";
import { browserLanguage, translate } from "./localize/localize";
import { stationsOf } from "./stations";
import type { RoadConditionsCardConfig, StationConfig } from "./types";

interface SchemaEntry {
    name: string;
}

function schema(text: (key: string) => string) {
    return [
        { name: "title", selector: { text: {} } },
        {
            name: "stations",
            required: true,
            selector: {
                object: {
                    multiple: true,
                    label_field: "device",
                    description_field: "name",
                    fields: {
                        device: {
                            label: text("editor.device"),
                            required: true,
                            // Only a road weather station has a temperature sensor of the integration; its feeds have none.
                            selector: { device: { entity: { integration: PLATFORM, domain: "sensor", device_class: "temperature" } } },
                        },
                        // A field inside the object selector takes its helper from here; ha-form's computeHelper doesn't reach it.
                        name: { label: text("editor.name"), description: text("editor.name_helper"), selector: { text: {} } },
                    },
                },
            },
        },
    ];
}

/** A station with nothing but its device is written as the plain device id, so the configuration stays short. */
export function compactStations(stations: StationConfig[]): Array<string | StationConfig> {
    return stationsOf(stations).map((station) => (station.name ? { device: station.device, name: station.name } : station.device));
}

export class RoadConditionsCardEditor extends LitElement {
    @property({ attribute: false }) public hass?: HomeAssistant;
    @state() private config: RoadConditionsCardConfig = { type: "custom:road-conditions-card", stations: [] };

    public setConfig(config: RoadConditionsCardConfig): void {
        this.config = { ...config };
    }

    protected render(): TemplateResult | typeof nothing {
        if (!this.hass) {
            return nothing;
        }
        // The form edits every station as an object; plain device ids are expanded for it.
        return html`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...this.config, stations: stationsOf(this.config.stations) }}
                .schema=${schema((key) => this.text(key))}
                .computeLabel=${(entry: SchemaEntry) => this.text(`editor.${entry.name}`)}
                @value-changed=${this.valueChanged}
            ></ha-form>
            <!-- Home Assistant's list of objects shows no helper text, so the stations' one is drawn here, under the list. -->
            <p class="helper">${this.text("editor.stations_helper")}</p>
        `;
    }

    static get styles(): CSSResultGroup {
        return css`
            .helper {
                margin: 8px 0 0;
                padding: 0 16px;
                font-size: 12px;
                line-height: 1.4;
                color: var(--secondary-text-color);
            }
        `;
    }

    private valueChanged(event: CustomEvent<{ value: RoadConditionsCardConfig }>): void {
        const config: RoadConditionsCardConfig = { ...event.detail.value };
        config.stations = compactStations((config.stations ?? []) as StationConfig[]);
        if (!config.title) {
            delete config.title;
        }
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
    }

    private text(key: string): string {
        return translate(this.language(), key);
    }

    private language(): string {
        return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
    }
}

if (!customElements.get("road-conditions-card-editor")) {
    customElements.define("road-conditions-card-editor", RoadConditionsCardEditor);
}

declare global {
    interface HTMLElementTagNameMap {
        "road-conditions-card-editor": RoadConditionsCardEditor;
    }
}
