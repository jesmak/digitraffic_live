/** The card's visual editor: the title, the stations with the names the card gives them, and the card's height. */
import { LitElement, css, html, nothing } from "lit";
import type { CSSResultGroup, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { PLATFORM } from "./const";
import type { HomeAssistant } from "./hass";
import { heightData, heightSchema, tidyHeight } from "./height";
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
                            // The device classes of a station's sensors, as a station has only those it reports. The integration's
                            // other devices have none of them: feeds no class, departures timestamps.
                            selector: {
                                device: {
                                    entity: {
                                        integration: PLATFORM,
                                        domain: "sensor",
                                        device_class: ["temperature", "enum", "wind_speed", "precipitation_intensity", "distance"],
                                    },
                                },
                            },
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
        // The first form edits every station as an object; plain device ids are expanded for it.
        return html`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...this.config, stations: stationsOf(this.config.stations) }}
                .schema=${schema((key) => this.text(key))}
                .computeLabel=${(entry: SchemaEntry) => this.text(`editor.${entry.name}`)}
                @value-changed=${(event: CustomEvent<{ value: RoadConditionsCardConfig }>) => this.changed(event.detail.value)}
            ></ha-form>
            <!-- Home Assistant's list of objects shows no helper text, so the stations' one is drawn here, between the list and
                 the height fields, which are a form of their own so it can sit there. -->
            <p class="helper">${this.text("editor.stations_helper")}</p>
            <ha-form
                class="height"
                .hass=${this.hass}
                .data=${heightData(this.config)}
                .schema=${heightSchema(this.config, (key) => this.text(key))}
                .computeLabel=${(entry: SchemaEntry) => this.text(`editor.${entry.name}`)}
                .computeHelper=${(entry: SchemaEntry) => this.helper(entry.name)}
                @value-changed=${(event: CustomEvent<{ value: RoadConditionsCardConfig }>) =>
                    this.changed({ ...this.config, ...event.detail.value })}
            ></ha-form>
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

            /* As far from the paragraph as ha-form keeps its own fields apart. */
            ha-form.height {
                display: block;
                margin-top: 24px;
            }
        `;
    }

    private changed(value: RoadConditionsCardConfig): void {
        const config: RoadConditionsCardConfig = tidyHeight(value);
        config.stations = compactStations((config.stations ?? []) as StationConfig[]);
        if (!config.title) {
            delete config.title;
        }
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
    }

    private text(key: string): string {
        return translate(this.language(), key);
    }

    /** The height fields' helpers, for the fields that have one. */
    private helper(name: string): string | undefined {
        const key = `editor.${name}_helper`;
        const helper = translate(this.language(), key);
        return helper === key ? undefined : helper;
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
