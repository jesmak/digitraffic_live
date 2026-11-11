"""Water restriction areas: speed limits, wake bans, motor boat bans and other standing restrictions on the water.

Data: Väylävirasto's open WFS, the layer rajoitusalue_a_uusi. An area has one or more restriction types, a speed
where one of them is a speed limit, and its exceptions and notes in Finnish. Nearly all are in force until further
notice. The few with an end date stay in the layer after it, and are left out here.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from .const import CONF_AREA, CONF_RESTRICTION_TYPES
from .feed import row, shape_feature
from .geo import Area, simplify_geometry
from .texts import Texts

KIND = "sea.restriction"

# Restriction type setting values by the layer's type code, in display order.
TYPES_BY_CODE = {
    "01": "speed_limit",
    "02": "no_wake",
    "05": "no_motor_vessels",
    "13": "power_limit",
    "04": "no_jet_skis",
    "12": "no_water_skiing",
    "03": "no_windsurfing",
    "06": "no_anchoring",
    "07": "no_berthing",
}
# Areas whose type is unknown (code 0) or one the integration has no name for.
OTHER_TYPE = "other"
RESTRICTION_TYPES = (*TYPES_BY_CODE.values(), OTHER_TYPE)

SPEED_LIMIT_CODE = "01"

# Drops only points that add nothing to a shape: a canal's speed limit area is 20 metres wide.
SIMPLIFY_TOLERANCE_KM = 0.005

# A fairway as the layer names it: "[6005: Saimaan kanava](vaylat:jnro=6005)".
FAIRWAY = re.compile(r"\[\d+: ([^\]]+)\]")


@dataclass(frozen=True)
class WaterRestrictionFeedConfig:
    area: Area
    restriction_types: frozenset[str]

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> WaterRestrictionFeedConfig:
        """From config subentry data. No restriction types chosen means all of them."""
        chosen = frozenset(data.get(CONF_RESTRICTION_TYPES) or ()) & frozenset(RESTRICTION_TYPES)
        return cls(area=Area.from_selector(data[CONF_AREA]), restriction_types=chosen or frozenset(RESTRICTION_TYPES))


def build_water_restriction_features(
    response: Mapping[str, Any] | None, config: WaterRestrictionFeedConfig, texts: Texts, today: date
) -> list[dict[str, Any]]:
    """The outline of each area in force that touches the feed's area and has a chosen restriction type."""
    features: list[dict[str, Any]] = []
    for restriction in (response or {}).get("features") or []:
        props = restriction.get("properties") or {}
        restriction_id = props.get("id")
        codes = split_list(props.get("rajoitustyypit"))
        end = parse_date(props.get("loppupaivamaara"))
        if restriction_id is None or (end is not None and end < today):
            continue
        types = {TYPES_BY_CODE.get(code, OTHER_TYPE) for code in codes} or {OTHER_TYPE}
        if not config.restriction_types & types:
            continue
        if not config.area.touches(restriction.get("geometry")):
            continue
        shape = simplify_geometry(restriction.get("geometry"), SIMPLIFY_TOLERANCE_KM)
        if shape is None:
            continue

        summary = ", ".join(restriction_names(props, codes, texts))
        place = str(props.get("nimisijainti") or "").strip()
        fairways = ", ".join(FAIRWAY.findall(str(props.get("vaylan_nimi") or "")))
        in_force = date_range(parse_date(props.get("alkupaivamaara")), end, texts)
        features.append(
            shape_feature(
                f"water_restriction:{restriction_id}",
                shape,
                {
                    "name": place or summary or texts("water_restriction"),
                    "kind": KIND,
                    # A standing area stays in the background, under the ships and the warnings.
                    "dashed": True,
                    "subtitle": summary if place else None,
                    "details": [
                        *([row(texts("fairway"), fairways)] if fairways else []),
                        *([row(texts("in_force"), in_force)] if in_force else []),
                    ],
                    "notices": [*paragraphs(props.get("lisatieto")), *paragraphs(props.get("poikkeus"))],
                },
            )
        )
    return features


def restriction_names(props: Mapping[str, Any], codes: list[str], texts: Texts) -> list[str]:
    """Each restriction's name in the feed's language, the speed limit with its speed. A type the integration has no
    name for keeps the layer's Finnish one."""
    finnish = split_list(props.get("rajoitustyyppi"))
    speed = str(props.get("suuruus") or "").strip()
    names = []
    for index, code in enumerate(codes):
        key = TYPES_BY_CODE.get(code)
        if code == SPEED_LIMIT_CODE and speed:
            names.append(texts("water_restriction_speed_limit_of", n=speed))
        elif key:
            names.append(texts(f"water_restriction_{key}"))
        elif index < len(finnish):
            names.append(finnish[index])
    return names


def split_list(value: Any) -> list[str]:
    """ "01, 02" → ["01", "02"]"""
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def parse_date(value: Any) -> date | None:
    """ "2014-07-01Z" as a date, or None when the layer has none."""
    try:
        return date.fromisoformat(str(value or "").removesuffix("Z"))
    except ValueError:
        return None


def date_range(start: date | None, end: date | None, texts: Texts) -> str:
    """ "1.7.2014 – 31.5.2027", "from 1.7.2014", "until 31.5.2027", or ""."""
    first = f"{start.day}.{start.month}.{start.year}" if start else ""
    last = f"{end.day}.{end.month}.{end.year}" if end else ""
    if first and last:
        return f"{first} – {last}"
    if first:
        return texts("from_time", time=first)
    if last:
        return texts("until_time", time=last)
    return ""


def paragraphs(value: Any) -> list[str]:
    """A note or an exception as paragraphs. The layer separates an area's texts with "---", and ends some with one."""
    return [text for part in str(value or "").split("---") if (text := " ".join(part.split()))]
