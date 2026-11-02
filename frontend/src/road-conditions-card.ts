/**
 * A dashboard card for the road weather stations of digitraffic_live. One station gets the whole card: its grip
 * as a grade on a scale, and its other values as icons with numbers. Several stations get a row each, with the
 * grade and a small scale on the right.
 *
 * The card finds a station's sensors through its device, by their translation keys, and leaves out whatever the
 * station doesn't measure. States are shown in the user's language through Home Assistant's own formatting.
 */
import { LitElement, css, html, nothing, svg } from "lit";
import type { CSSResultGroup, PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { CARD_VERSION, HEAVY, ICONS } from "./const";
import type { SensorKey } from "./const";
import "./editor";
import { ScrollFade, fadeStyles } from "./fade";
import type { HassEntity, HomeAssistant } from "./hass";
import { gridMinRows, heightCardSize, heightStyle, validHeight } from "./height";
import { browserLanguage, translate } from "./localize/localize";
import { filledHeight, validRowStep } from "./rows";
import { precipitation, reading, scale, showGusts, stationDevices, stationName, stationSensors, stationsOf } from "./stations";
import type { RoadConditionsCardConfig, StationConfig } from "./types";
import { WEATHER_ICONS } from "./weather-icons";

/** Every part of the card is a whole number of these, half a row of a sections view. */
const STEP_PX = 32;

/** The card's padding and border, top and bottom, so that its parts end on the rows. */
const FRAME_PX = 24;

const px = (value: string) => parseFloat(value) || 0;

interface CardRegistration {
    type: string;
    name: string;
    description: string;
    documentationURL?: string;
    preview?: boolean;
}

type Sensors = Partial<Record<SensorKey, string>>;

/** One value of a station: its icon, what it is, what it reads, and the sensor its history is in. */
interface Value {
    key: string;
    icon: string;
    label: string;
    text: string;
    /** What a screen reader says for the value: what it is and what it reads. */
    spoken: string;
    entity: string;
    /** Freezing or heavy precipitation, in the warning colour and in the station's row too. */
    notable?: boolean;
}

export class RoadConditionsCard extends LitElement {
    @property({ attribute: false }) public hass?: HomeAssistant;
    @property({ attribute: false }) public layout?: string;
    @state() private config?: RoadConditionsCardConfig;
    /** The height that fills the card's rows on automatic rows, and the room in it the content leaves over. */
    @state() private filled = 0;
    @state() private spare = 0;
    private sensorCache?: { entities: HomeAssistant["entities"]; byDevice: Map<string, Sensors> };
    private frame?: number;
    private readonly resizes = typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(() => this.measureSoon());

    constructor() {
        super();
        // Fades the scroller's edges while the card is held to a height, through the card's own lifecycle.
        new ScrollFade(this, () =>
            this.heightStyle() ? this.renderRoot.querySelectorAll<HTMLElement>("ha-card > .station, ha-card > .rows") : [],
        );
    }

    public static getConfigElement(): HTMLElement {
        return document.createElement("road-conditions-card-editor");
    }

    /** Offers the first road weather station there is when the card is added from the picker. */
    public static getStubConfig(hass?: HomeAssistant): Record<string, unknown> {
        return { stations: hass ? stationDevices(hass).slice(0, 1) : [] };
    }

    public setConfig(config: RoadConditionsCardConfig): void {
        if (!config || stationsOf(config.stations).length === 0) {
            throw new Error(translate(browserLanguage(), "common.invalid_configuration"));
        }
        // A station whose device is misspelt would otherwise vanish from the card without a word.
        if (stationsOf(config.stations).length !== config.stations.length) {
            throw new Error(translate(browserLanguage(), "common.station_without_device"));
        }
        if (!validHeight(config)) {
            throw new Error(translate(browserLanguage(), "common.invalid_height"));
        }
        if (!validRowStep(config)) {
            throw new Error(translate(browserLanguage(), "common.invalid_row_step"));
        }
        this.config = { ...config };
    }

    /**
     * In a sections view the card takes a whole section by default, and is never lower than its minimum height. Below 9
     * columns a station's name and values have too little room: at 6, a 320 px phone with a section background leaves the
     * card 140 px.
     */
    public getGridOptions(): Record<string, unknown> {
        return { columns: 12, rows: "auto", min_columns: 9, min_rows: gridMinRows(this.minimumHeight()) };
    }

    public connectedCallback(): void {
        super.connectedCallback();
        // Back on the page, the card is observed and measured again, as it was let go when it left.
        if (this.hasUpdated) {
            this.requestUpdate();
        }
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.resizes?.disconnect();
        cancelAnimationFrame(this.frame ?? 0);
    }

    public getCardSize(): number {
        const count = this.config ? stationsOf(this.config.stations).length : 1;
        return heightCardSize(this.config ?? {}, count === 1 ? 4 : 1 + count, this.minimumHeight());
    }

    protected shouldUpdate(changed: PropertyValues): boolean {
        const previous = changed.get("hass") as HomeAssistant | undefined;
        // The layout decides whether the card is held to a height, even when a change of the house comes with it.
        if (changed.has("config") || changed.has("layout") || !this.config || !this.hass || !changed.has("hass") || !previous) {
            return true;
        }
        if (previous.entities !== this.hass.entities || previous.devices !== this.hass.devices) {
            return true;
        }
        // A new language or number format changes every text on the card.
        if (
            previous.locale !== this.hass.locale ||
            previous.language !== this.hass.language ||
            previous.formatEntityState !== this.hass.formatEntityState
        ) {
            return true;
        }
        // Home Assistant hands the card every state change in the house; only the stations' sensors matter.
        const ids = stationsOf(this.config.stations).flatMap((station) => Object.values(this.sensors(station.device)));
        return ids.some((id) => previous.states[id as string] !== this.hass?.states[id as string]);
    }

    /** A station's sensors, looked up again only when the entity registry changes, not on every state change. */
    private sensors(device: string): Sensors {
        const hass = this.hass as HomeAssistant;
        let cache = this.sensorCache;
        if (!cache || cache.entities !== hass.entities) {
            cache = { entities: hass.entities, byDevice: new Map() };
            this.sensorCache = cache;
        }
        let found = cache.byDevice.get(device);
        if (!found) {
            found = stationSensors(hass, device);
            cache.byDevice.set(device, found);
        }
        return found;
    }

    protected render(): TemplateResult | typeof nothing {
        if (!this.hass || !this.config) {
            return nothing;
        }
        const stations = stationsOf(this.config.stations);
        const title = this.config.title;
        // The room a whole row leaves over goes under one station's name, or under the title of several, or above them
        // without one.
        const several = stations.length > 1;
        return html`
            <ha-card class=${this.heightStyle() ? "held" : ""} style=${this.cardStyle()}>
                ${title ? html`<h1 class="card-title ${several ? "spare" : ""}" title=${title}>${title}</h1>` : nothing}
                ${
                    several
                        ? html`<div class="rows ${title ? "" : "spare-top"}">${stations.map((station) => this.row(station))}</div>`
                        : this.station(stations[0])
                }
            </ha-card>
        `;
    }

    protected updated(): void {
        const card = this.renderRoot.querySelector("ha-card");
        if (card && this.isConnected) {
            this.resizes?.observe(card);
            this.measureSoon();
        }
    }

    private measureSoon(): void {
        cancelAnimationFrame(this.frame ?? 0);
        this.frame = requestAnimationFrame(() => this.fillRows());
    }

    /**
     * In a sections view whose rows are left automatic, the card takes the whole rows its content needs, or the half rows
     * with `row_step: half`, so the cards under it stay on the rows. The room left over goes under one station's name,
     * or under the title of several, or above them without one.
     */
    private fillRows(): void {
        const card = this.renderRoot.querySelector<HTMLElement>("ha-card");
        if (!card || !card.clientWidth) {
            return;
        }
        if (this.layout !== "grid" || this.heightStyle()) {
            this.filled = 0;
            this.spare = 0;
            return;
        }
        // From the card's top to the end of its own last part, never its own height, which is the min-height set here, and
        // never an element a theme adds to it.
        const parts = card.querySelectorAll<HTMLElement>(
            ":scope > .card-title, :scope > .name, :scope > .station > *, :scope > .rows > .row",
        );
        const last = parts[parts.length - 1];
        if (!last) {
            return;
        }
        const style = getComputedStyle(card);
        let content =
            last.getBoundingClientRect().bottom +
            px(getComputedStyle(last).marginBottom) -
            card.getBoundingClientRect().top +
            px(style.paddingBottom) +
            px(style.borderBottomWidth);
        // The spare room as drawn now.
        const below = card.querySelector<HTMLElement>(".spare");
        const above = card.querySelector<HTMLElement>(".spare-top");
        content -= (below ? px(getComputedStyle(below).paddingBottom) : 0) + (above ? px(getComputedStyle(above).paddingTop) : 0);
        const filled = filledHeight(Math.round(content), this.config ?? {});
        this.filled = filled;
        this.spare = Math.max(0, Math.floor(filled - content));
    }

    /** The card's inline style: the height it is held to, or the rows it fills, with their spare room. */
    private cardStyle(): string {
        const held = this.heightStyle();
        if (held || !this.filled) {
            return held;
        }
        return `min-height: ${this.filled}px; --spare: ${this.spare}px`;
    }

    /**
     * The whole card for one station: its name, and under it the grade on its scale, the values in a grid and a warning
     * when there is one, which is the part that scrolls when the card is held to a height.
     */
    private station(station: StationConfig): TemplateResult {
        const hass = this.hass as HomeAssistant;
        const sensors = this.sensors(station.device);
        const name = stationName(hass, station);
        const head = html`<div class="name spare" title=${name}>${name}</div>`;
        if (Object.keys(sensors).length === 0) {
            return html`${head}
                <div class="station"><div class="message">${this.text("common.no_station")}</div></div>`;
        }
        const condition = reading(hass, sensors.grip_condition);
        const grip = reading(hass, sensors.grip);
        const warning = reading(hass, sensors.road_warning);
        const values = this.values(sensors);
        // The integration keeps its sensors when it can't reach the station; they are all unavailable then.
        if (!condition && values.length === 0 && !warning) {
            return html`${head}
                <div class="station"><div class="message">${this.text("common.no_readings")}</div></div>`;
        }
        return html`
            ${head}
            <div class="station">
                ${
                    condition
                        ? html`
                              <button class="grade" @click=${() => this.moreInfo(condition.entity_id)}>
                                  <span class="grade-text" title=${this.format(condition)}>${this.format(condition)}</span>
                                  ${grip ? html`<span class="grip">${this.format(grip)}</span>` : nothing}
                              </button>
                              ${this.scale(condition.state, "large")}
                              <div class="scale-labels" aria-hidden="true">
                                  <span title=${this.text("scale.very_slippery")}>${this.text("scale.very_slippery")}</span
                                  ><span title=${this.text("scale.winter")}>${this.text("scale.winter")}</span
                                  ><span title=${this.text("scale.good")}>${this.text("scale.good")}</span>
                              </div>
                          `
                        : nothing
                }
                ${
                    values.length
                        ? html`<div class="values ${condition ? "divided" : ""}">
                              ${values.map(
                                  (value) => html`
                                      <button
                                          class="value ${value.key} ${value.notable ? "notable" : ""}"
                                          title="${value.label}"
                                          aria-label="${value.spoken}"
                                          @click=${() => this.moreInfo(value.entity)}
                                      >
                                          ${this.icon(value.icon)} ${value.text ? html`<span>${value.text}</span>` : nothing}
                                      </button>
                                  `,
                              )}
                          </div>`
                        : nothing
                }
                ${
                    warning && warning.state !== "ok"
                        ? html`<button class="warning" @click=${() => this.moreInfo(warning.entity_id)}>
                              ${this.icon(ICONS.road_warning)}
                              <span>${this.text("labels.road_warning")}: ${this.format(warning)}</span>
                          </button>`
                        : nothing
                }
            </div>
        `;
    }

    /** One station as a row: its name and main values on the left, the grade and a small scale on the right. */
    private row(station: StationConfig): TemplateResult {
        const hass = this.hass as HomeAssistant;
        const sensors = this.sensors(station.device);
        const name = stationName(hass, station);
        const condition = reading(hass, sensors.grip_condition);
        const grip = reading(hass, sensors.grip);
        const summary = this.values(sensors).filter(
            (value) => value.notable || ["road_temperature", "road_surface", "wind"].includes(value.key),
        );
        let message: string | undefined;
        if (Object.keys(sensors).length === 0) {
            message = this.text("common.no_station");
        } else if (summary.length === 0 && !condition) {
            message = this.text("common.no_readings");
        }
        // Held to a height, the name and the values keep to one line, so the whole of each is a tooltip.
        const values = message ?? summary.map((value) => value.spoken).join(", ");
        const content = html`
            <span class="row-text">
                <span class="row-name" title=${name}>${name}</span>
                <span class="row-values" title=${values}>
                    ${
                        message
                            ? message
                            : summary.map(
                                  (value) =>
                                      html`<span class="row-value ${value.notable ? "notable" : ""}" title="${value.label}"
                                          >${this.icon(value.icon)}${value.text}</span
                                      >`,
                              )
                    }
                </span>
            </span>
            ${
                condition
                    ? html`<span class="row-grade">
                          <span>${this.format(condition)}${grip ? html` <span class="grip">${this.format(grip)}</span>` : nothing}</span>
                          ${this.scale(condition.state, "small")}
                      </span>`
                    : nothing
            }
        `;
        const target = sensors.grip_condition ?? sensors.road_temperature;
        if (!target) {
            return html`<div class="row">${content}</div>`;
        }
        // The values in the row are named only by their tooltips, so the row says them in full for a screen reader.
        const spoken = [name, ...summary.map((value) => value.spoken)];
        if (condition) {
            spoken.push(grip ? `${this.format(condition)} ${this.format(grip)}` : this.format(condition));
        }
        return html`<button class="row" aria-label=${spoken.join(", ")} @click=${() => this.moreInfo(target)}>${content}</button>`;
    }

    private heightStyle(): string {
        return heightStyle(this.config ?? {}, this.layout, this.minimumHeight());
    }

    /**
     * The lowest the card is held to, in pixels: its padding and border, the title when it has one, and for one station its
     * name, the grade, the scale and the first line of values, a half-row step each, for several the first station's row.
     * A row is three steps on a narrow card, where its grade goes under its values, and the minimum is for the narrowest
     * its columns get. Held, the texts above the values keep to one line, so this holds at any width.
     */
    private minimumHeight(): number {
        const one = this.config ? stationsOf(this.config.stations).length === 1 : true;
        return FRAME_PX + ((this.config?.title ? 1 : 0) + (one ? 4 : 3)) * STEP_PX;
    }

    private scale(condition: string, size: "large" | "small"): TemplateResult {
        return html`<div class="scale ${size}" aria-hidden="true">
            ${scale(condition).map((part) => html`<span class="part grip-${part.condition} ${part.lit ? "lit" : ""}"></span>`)}
        </div>`;
    }

    /** A Weather Icons glyph drawn inline ("wi:rain"), or a Material Design Icon through Home Assistant. */
    private icon(name: string): TemplateResult {
        if (name.startsWith("wi:")) {
            return html`<svg class="icon" data-icon=${name} viewBox="0 0 30 30" aria-hidden="true">
                ${svg`<path d=${WEATHER_ICONS[name.slice(3)] ?? ""}></path>`}
            </svg>`;
        }
        return html`<ha-icon class="icon" data-icon=${name} icon=${name}></ha-icon>`;
    }

    /** The station's values in the order they are shown, leaving out what it doesn't measure. */
    private values(sensors: Sensors): Value[] {
        const hass = this.hass as HomeAssistant;
        const values: Value[] = [];
        const add = (key: string, entity: HassEntity | undefined, icon: string, text: string) => {
            if (entity) {
                const label = this.text(`labels.${key}`);
                values.push({ key, icon, label, text, spoken: `${label} ${text}`, entity: entity.entity_id });
            }
        };
        for (const key of ["road_temperature", "air_temperature", "road_surface"] as const) {
            const entity = reading(hass, sensors[key]);
            add(key, entity, ICONS[key], entity ? this.format(entity) : "");
        }
        const speed = reading(hass, sensors.wind_speed);
        if (speed) {
            const gusts = reading(hass, sensors.wind_gusts);
            const extra = gusts && showGusts(speed, gusts) ? ` (${this.format(gusts)})` : "";
            add("wind", speed, ICONS.wind, `${this.format(speed)}${extra}`);
        }
        const code = reading(hass, sensors.precipitation);
        const type = reading(hass, sensors.precipitation_type);
        if (code || type) {
            // A short word fits the grid; the full description and the amount are in the tooltip.
            const shown = precipitation(type?.state, code?.state);
            const entity = (type ?? code) as HassEntity;
            const intensity = reading(hass, sensors.rain_intensity);
            // The type doesn't say how heavy it is, so the tooltip names heavy precipitation by its amount code too.
            const described = [
                entity,
                ...(type && code && HEAVY.includes(code.state) ? [code] : []),
                ...(intensity && Number(intensity.state) > 0 ? [intensity] : []),
            ];
            const label = `${this.text("labels.precipitation")}: ${described.map((part) => this.format(part)).join(", ")}`;
            values.push({
                key: "precipitation",
                notable: shown.notable,
                icon: shown.icon,
                label,
                text: shown.text ? this.text(`precipitation.${shown.text}`) : this.format(entity),
                // The label already says it all; the short word would be heard twice.
                spoken: label,
                entity: entity.entity_id,
            });
        }
        const visibility = reading(hass, sensors.visibility);
        add("visibility", visibility, ICONS.visibility, visibility ? this.format(visibility) : "");
        return values;
    }

    /** A state as Home Assistant shows it, in the user's language and with its unit. */
    private format(entity: HassEntity): string {
        return (this.hass as HomeAssistant).formatEntityState(entity);
    }

    private moreInfo(entityId: string | undefined): void {
        if (entityId) {
            this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
        }
    }

    private text(key: string): string {
        return translate(this.language(), key);
    }

    private language(): string {
        return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
    }

    static get styles(): CSSResultGroup {
        return [
            css`
                /*
                 * Every part is a whole number of half-row steps, 32 px, and the padding and the border make up the 24 px that
                 * leave the card on the rows of a sections view: k rows are 64k − 8 px. A heading or a row's text that wraps
                 * adds a step a line, while a value or the warning that wraps keeps its lines together instead.
                 *
                 * The container queries measure the card's content box, 34 px narrower than the card: the padding and the
                 * border at its sides.
                 */
                ha-card {
                    padding: 11px 16px;
                    container-type: inline-size;
                    font-variant-numeric: tabular-nums;
                    --road-very-slippery: var(--road-conditions-very-slippery-color, var(--error-color, #db4437));
                    --road-slippery: var(--road-conditions-slippery-color, #f4511e);
                    --road-fair-winter: var(--road-conditions-fair-winter-color, #fb8c00);
                    --road-good-winter: var(--road-conditions-good-winter-color, #ffb300);
                    --road-fair: var(--road-conditions-fair-color, #9ccc65);
                    --road-good: var(--road-conditions-good-color, var(--success-color, #43a047));
                }

                button {
                    font: inherit;
                    color: inherit;
                    background: none;
                    border: none;
                    padding: 0;
                    margin: 0;
                    text-align: inherit;
                    cursor: pointer;
                }

                .card-title {
                    margin: 0;
                    font-size: var(--ha-card-header-font-size, 24px);
                    font-weight: var(--ha-font-weight-normal, 400);
                    line-height: 32px;
                    overflow-wrap: anywhere;
                }

                .name {
                    font-size: 16px;
                    font-weight: var(--ha-font-weight-medium, 500);
                    line-height: 32px;
                    overflow-wrap: anywhere;
                }

                /* The room a whole row leaves over, under the name or the title, or above the rows without a title. Padding,
                   not a margin, which would collapse into its neighbour's. */
                .spare {
                    padding-bottom: var(--spare, 0px);
                }

                .spare-top {
                    padding-top: var(--spare, 0px);
                }

                /* Held to a height, the texts above what scrolls keep to one line, so the card's least height holds. */
                ha-card.held .card-title,
                ha-card.held .name,
                ha-card.held .grade-text,
                ha-card.held .row-name,
                ha-card.held .row-values {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .message {
                    line-height: 32px;
                    color: var(--secondary-text-color);
                }

                .grip-very_slippery {
                    color: var(--road-very-slippery);
                }
                .grip-slippery {
                    color: var(--road-slippery);
                }
                .grip-fair_winter {
                    color: var(--road-fair-winter);
                }
                .grip-good_winter {
                    color: var(--road-good-winter);
                }
                .grip-fair {
                    color: var(--road-fair);
                }
                .grip-good {
                    color: var(--road-good);
                }

                /*
                 * One step, or two when a narrow card puts the grip on a line of its own. Centred, not on their baselines, as
                 * aligning the baselines of two font sizes in lines of 32 px makes the line 34.
                 */
                .grade {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    align-items: center;
                    column-gap: 12px;
                    width: 100%;
                    line-height: 32px;
                }

                ha-card.held .grade {
                    flex-wrap: nowrap;
                }

                .grade-text {
                    min-width: 0;
                    font-size: 20px;
                    font-weight: var(--ha-font-weight-medium, 500);
                }

                /* "0,22 µ" stays whole on its line. */
                .grip {
                    color: var(--primary-text-color);
                    white-space: nowrap;
                }

                .grade .grip {
                    font-size: 16px;
                }

                /* The scale is six parts, faint in the colours of their conditions, lit up to the one the road is in. */
                .scale {
                    display: grid;
                    grid-template-columns: repeat(6, minmax(0, 1fr));
                    gap: 3px;
                }

                .scale.large .part {
                    height: 8px;
                }

                .scale.small {
                    width: 72px;
                    gap: 2px;
                }

                .scale.small .part {
                    height: 4px;
                }

                .part {
                    background: currentColor;
                    opacity: 0.25;
                }

                .part.lit {
                    opacity: 1;
                }

                .scale.large .part:first-child {
                    border-radius: 4px 0 0 4px;
                }

                .scale.large .part:last-child {
                    border-radius: 0 4px 4px 0;
                }

                /*
                 * Equal side columns keep the middle label on the meter's middle gap, however long the outer ones are. The scale
                 * and its labels are one step, so the labels keep to one line.
                 */
                .scale-labels {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
                    gap: 8px;
                    margin: 6px 0 4px;
                    font-size: 11px;
                    line-height: 14px;
                    color: var(--secondary-text-color);
                }

                .scale-labels span {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .scale-labels span:last-child {
                    text-align: right;
                }

                /* On a card narrower than about 284 px the middle label goes, so the ends have room for their whole words. */
                @container (max-width: 249px) {
                    .scale-labels {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }

                    .scale-labels span:nth-child(2) {
                        display: none;
                    }
                }

                /* The values flow into three columns of a step a line, so a value the station lacks leaves no gap. */
                .values {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    column-gap: 8px;
                }

                /* Two columns on a card narrower than about 334 px, every value on one row from about 834 px. */
                @container (max-width: 299px) {
                    .values {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }
                }

                @container (min-width: 800px) {
                    .values {
                        grid-template-columns: none;
                        grid-auto-flow: column;
                        grid-auto-columns: minmax(0, 1fr);
                    }
                }

                /* A line drawn over the values, not a border, which would take a pixel off the step. */
                .values.divided {
                    background: linear-gradient(var(--divider-color), var(--divider-color)) top / 100% 1px no-repeat;
                }

                /*
                 * A step tall on one line. A value that wraps keeps its lines together at 20 px, so it reads as one value, and
                 * leaves the step: the card still ends on whole rows, as it measures where its content ends. The 4 px gap keeps a
                 * temperature such as −12,5 °C on one line beside its icon on a held card of 214 px, 9 columns on a 320 px
                 * phone with a section background.
                 */
                .value {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    min-width: 0;
                    min-height: 32px;
                    font-size: 15px;
                    line-height: 20px;
                }

                .icon {
                    flex: 0 0 auto;
                    width: 20px;
                    height: 20px;
                    --mdc-icon-size: 20px;
                    color: var(--state-icon-color, var(--secondary-text-color));
                }

                /* A flex box, as Home Assistant's icon inside it is inline and would sit in the 32 px line of the text beside it,
                   drawn below its box. */
                ha-icon.icon {
                    display: flex;
                }

                /* Weather Icons leave a wide margin inside their canvas, so they are drawn larger to match. */
                svg.icon {
                    width: 26px;
                    height: 26px;
                    margin: -3px;
                    fill: currentColor;
                }

                /* A value too long for its column wraps rather than being cut. */
                .value span {
                    min-width: 0;
                    overflow-wrap: anywhere;
                }

                /* Freezing or heavy precipitation matters at a glance. */
                .notable,
                .notable .icon {
                    color: var(--warning-color, #ffa600);
                }

                /* As a value: a step on one line, its lines kept together when it wraps. */
                .warning {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    min-height: 32px;
                    font-size: 14px;
                    line-height: 20px;
                    color: var(--warning-color, #ffa600);
                }

                .warning .icon {
                    color: inherit;
                }

                .rows {
                    display: flex;
                    flex-direction: column;
                }

                /* Held to a height, by its height mode or a sections view's rows, the card is a column in which only the station's
                   view scrolls, under the title and the station's name, or the list of stations under the title. */
                ha-card.held {
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    overflow: clip;
                }

                ha-card.held > * {
                    flex: none;
                }

                /*
                 * It clips at its padding box, so it reaches 4 px out on every side, where the focus rings are drawn: over the
                 * card's padding at the sides and the bottom, and at the top over the room under the title's or the station's
                 * name's text in its line, or over the card's padding, where nothing takes a tap.
                 */
                ha-card.held > .station,
                ha-card.held > .rows {
                    margin: -4px;
                    padding: 4px;
                    flex: 1 1 auto;
                    min-height: 0;
                    overflow-y: auto;
                    scrollbar-width: thin;
                }

                /*
                 * A row is two steps: its name in 24 px and its values in 20, between 10 px above and below. Each takes a line of
                 * 32 px with negative margins, so a line more adds a step. The row-text is a flex column, as the negative margins
                 * of block siblings collapse into one.
                 */
                .row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                    width: 100%;
                    padding: 10px 0;
                }

                /* A line drawn between the rows, not a border, which would take a pixel off the step. */
                .row + .row {
                    box-shadow: inset 0 1px var(--divider-color);
                }

                .row-text {
                    display: flex;
                    flex-direction: column;
                    min-width: 0;
                }

                .row-name {
                    margin: -4px 0;
                    font-size: 15px;
                    line-height: 32px;
                    overflow-wrap: anywhere;
                }

                .row-values {
                    margin: -6px 0;
                    font-size: 13px;
                    line-height: 32px;
                    color: var(--secondary-text-color);
                }

                .row-value {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    max-width: 100%;
                    margin-inline-end: 12px;
                    vertical-align: top;
                    overflow-wrap: anywhere;
                }

                .row-value:last-child {
                    margin-inline-end: 0;
                }

                .row-value .icon {
                    width: 16px;
                    height: 16px;
                    --mdc-icon-size: 16px;
                }

                .row-value svg.icon {
                    width: 21px;
                    height: 21px;
                    margin: -2.5px;
                }

                .row-grade {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 4px;
                    flex: 0 0 auto;
                    font-size: 14px;
                    line-height: 20px;
                    text-align: right;
                }

                /* Its own line height, as the smaller text on the grade's baseline would make the grade's line of 20 px 21. */
                .row-grade .grip {
                    line-height: 1;
                    font-size: 12px;
                    color: var(--secondary-text-color);
                }

                /*
                 * Beside a long grade a card narrower than about 374 px leaves the name and values no room, so the grade goes
                 * below them, as a step of its own: its 20 px line, the scale and the room between them and above.
                 */
                @container (max-width: 339px) {
                    .row {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 0;
                    }

                    .row-grade {
                        align-items: flex-start;
                        margin-top: 4px;
                        text-align: left;
                    }
                }
            `,
            fadeStyles,
        ];
    }
}

// Anyone who installed the card on its own before it came with the integration may still load that copy too, as a
// dashboard resource of its own. Whichever loads first is the card, and the other stays out of the way.
if (!customElements.get("road-conditions-card")) {
    console.info(
        `%c  ROAD-CONDITIONS-CARD \n%c  ${CARD_VERSION}    `,
        "color: orange; font-weight: bold; background: black",
        "color: white; font-weight: bold; background: dimgray",
    );

    const registry = window as unknown as { customCards?: CardRegistration[] };
    registry.customCards = registry.customCards ?? [];
    registry.customCards.push({
        type: "road-conditions-card",
        name: translate(browserLanguage(), "common.name"),
        description: translate(browserLanguage(), "common.description"),
        documentationURL: "https://github.com/jesmak/digitraffic_live#road-conditions-card",
        preview: true,
    });
    customElements.define("road-conditions-card", RoadConditionsCard);
}

declare global {
    interface HTMLElementTagNameMap {
        "road-conditions-card": RoadConditionsCard;
    }
}
