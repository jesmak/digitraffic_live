import type { LovelaceCardConfig } from "./hass";

/** One road weather station: its device, and the name the card gives it. */
export interface StationConfig {
    device: string;
    /** Replaces the station's own name, which is long: "VT6 Kärki" for "Road 6 Lappeenranta, Kärki". */
    name?: string;
}

export interface RoadConditionsCardConfig extends LovelaceCardConfig {
    /** Road weather station devices of digitraffic_live: a device id, or one with its name. One draws the full card, more a row each. */
    stations: Array<string | StationConfig>;
    /** Shown at the top of the card. */
    title?: string;
}
