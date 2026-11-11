"""Nautical warnings: which of Traficom's warnings a feed takes, and the features built from them."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live.api import NAUTICAL_WARNING_LAYERS, TRAFICOM_WFS
from custom_components.digitraffic_live.const import DOMAIN
from custom_components.digitraffic_live.nautical_warnings import (
    NauticalWarningFeedConfig,
    build_nautical_warning_features,
    fetch_nautical_warnings,
)
from custom_components.digitraffic_live.texts import load_texts

from .conftest import HAMINA_AREA

TEXTS = load_texts("en")


def warning(number: int, geometry: dict[str, Any], **fields: Any) -> dict[str, Any]:
    """A warning as the layers give it, with invented contents."""
    return {
        "type": "Feature",
        "id": f"navigational_warnings.{number}",
        "geometry": geometry,
        "properties": {
            "WARNINGINFORMATIONNAVWARNTYPEDETAILS_FI": None,
            "WARNINGINFORMATIONNAVWARNTYPEDETAILS_EN": None,
            "WARNINGINFORMATION_FI": "VENEILIJÖITÄ KEHOTETAAN VAROVAISUUTEEN.",
            "WARNINGINFORMATION_EN": "BOATERS ARE ADVISED TO NAVIGATE WITH CAUTION.",
            "MESSAGESERIESIDENTIFIERINTEROPERABILITYIDENTIFIER": f"urn:mrn:fin:navwarn:FI05:VV:2026:{number}",
            "MESSAGESERIESIDENTIFIERNAMEOFSERIES_FI": "Varoituksia veneilijöille",
            "MESSAGESERIESIDENTIFIERNAMEOFSERIES_EN": "Warnings for Yachtmen",
            "MESSAGESERIESIDENTIFIERWARNINGNUMBER": number,
            "MESSAGESERIESIDENTIFIERYEAR": 2026,
            "NAVWARNTYPEGENERAL_FI": "Erityistoiminnot",
            "NAVWARNTYPEGENERAL_EN": "Special operations",
            "PUBLICATIONTIME": "2026-09-07T12:59:49Z",
            "GENERALAREALOCATIONNAME_FI": "Suomenlahti",
            "GENERALAREALOCATIONNAME_EN": "Gulf of Finland",
            "LOCALITYLOCATIONNAME_FI": "KUUSILUOTO",
            "LOCALITYLOCATIONNAME_EN": "KUUSILUOTO",
            **fields,
        },
    }


DREDGING = warning(
    11,
    {"type": "MultiPolygon", "coordinates": [[[[27.19, 60.55], [27.21, 60.55], [27.21, 60.56], [27.19, 60.56], [27.19, 60.55]]]]},
)
# The circle lies wholly inside this one.
FIRING_EXERCISE = warning(
    12,
    {"type": "MultiPolygon", "coordinates": [[[[26.0, 60.0], [28.5, 60.0], [28.5, 61.0], [26.0, 61.0], [26.0, 60.0]]]]},
    WARNINGINFORMATIONNAVWARNTYPEDETAILS_FI="Ampumaharjoitus",
    WARNINGINFORMATIONNAVWARNTYPEDETAILS_EN="Firing exercise",
)
FAR_AWAY_AREA = warning(
    13,
    {"type": "MultiPolygon", "coordinates": [[[[21.0, 60.0], [21.1, 60.0], [21.1, 60.1], [21.0, 60.1], [21.0, 60.0]]]]},
)
BRIDGE_WORK = warning(21, {"type": "MultiLineString", "coordinates": [[[27.15, 60.52], [27.16, 60.53]]]})
UNLIT_BUOY = warning(
    31,
    {"type": "MultiPoint", "coordinates": [[27.205303, 60.549405]]},
    WARNINGINFORMATIONNAVWARNTYPEDETAILS_FI="Valaistu poiju - valo ei käytössä",
    WARNINGINFORMATIONNAVWARNTYPEDETAILS_EN="Light buoy - light unlit",
    WARNINGINFORMATION_EN="\nRED BUOY KUU 4 NR 99901\nIN POSITION 60-32.96 N, 027-12.31 E\n\nLIGHT OUT OF ORDER",
    MESSAGESERIESIDENTIFIERINTEROPERABILITYIDENTIFIER="urn:mrn:fin:navwarn:FI05:LC:2026:31",
    MESSAGESERIESIDENTIFIERNAMEOFSERIES_EN="Coastal and Local Warnings",
)
FAR_AWAY_BUOY = warning(32, {"type": "MultiPoint", "coordinates": [[21.3, 61.6]]})

LAYERS = {
    "navigational_warnings_a": [DREDGING, FIRING_EXERCISE, FAR_AWAY_AREA],
    "navigational_warnings_l": [BRIDGE_WORK],
    "navigational_warnings_p": [UNLIT_BUOY, FAR_AWAY_BUOY],
}


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def nautical_warnings(self, layer: str) -> dict[str, Any]:
        self.calls.append(layer)
        return {"type": "FeatureCollection", "features": LAYERS[layer]}


async def fetch() -> list[dict[str, Any]]:
    return await fetch_nautical_warnings(FakeClient(), NauticalWarningFeedConfig.from_data({"area": HAMINA_AREA}))  # type: ignore[arg-type]


async def test_every_layer_is_fetched_and_limited_to_the_area() -> None:
    client = FakeClient()
    warnings = await fetch_nautical_warnings(client, NauticalWarningFeedConfig.from_data({"area": HAMINA_AREA}))  # type: ignore[arg-type]

    assert client.calls == list(NAUTICAL_WARNING_LAYERS)
    assert warnings == [DREDGING, FIRING_EXERCISE, BRIDGE_WORK, UNLIT_BUOY]


async def test_a_point_warning_is_a_point_with_its_text_as_one_paragraph() -> None:
    features = build_nautical_warning_features(await fetch(), TEXTS)
    buoy = next(feature for feature in features if feature["id"] == "nautical_warning:urn:mrn:fin:navwarn:FI05:LC:2026:31")

    assert buoy["geometry"] == {"type": "Point", "coordinates": [27.2053, 60.54941]}
    assert buoy["properties"] == {
        "name": "Light buoy - light unlit",
        "kind": "sea.warning",
        "updated": "2026-09-07T12:59:49Z",
        "subtitle": "KUUSILUOTO",
        "details": [{"label": "Type", "value": "Special operations"}, {"label": "Area", "value": "Gulf of Finland"}],
        "notices": ["RED BUOY KUU 4 NR 99901 IN POSITION 60-32.96 N, 027-12.31 E LIGHT OUT OF ORDER"],
        "footer": "Coastal and Local Warnings 31/2026",
    }
    assert not any(feature["id"] == f"{buoy['id']}/area" for feature in features)


async def test_an_area_or_line_warning_gets_its_shape_tied_to_its_point() -> None:
    features = {feature["id"]: feature for feature in build_nautical_warning_features(await fetch(), TEXTS)}
    dredging_id = "nautical_warning:urn:mrn:fin:navwarn:FI05:VV:2026:11"
    bridge_id = "nautical_warning:urn:mrn:fin:navwarn:FI05:VV:2026:21"

    # Without a detailed type the general one is the name, and isn't repeated as a row.
    dredging = features[dredging_id]["properties"]
    assert dredging["name"] == "Special operations"
    assert dredging["details"] == [{"label": "Area", "value": "Gulf of Finland"}]
    assert features[dredging_id]["geometry"] == {"type": "Point", "coordinates": [27.2, 60.555]}

    area = features[f"{dredging_id}/area"]
    assert area["geometry"]["type"] == "Polygon"
    assert area["properties"] == {"kind": "sea.warning", "point": dredging_id}
    assert features[f"{bridge_id}/area"]["geometry"] == {"type": "LineString", "coordinates": [[27.15, 60.52], [27.16, 60.53]]}


async def test_the_texts_follow_the_language() -> None:
    features = build_nautical_warning_features([FIRING_EXERCISE], load_texts("fi"))

    assert features[0]["properties"]["name"] == "Ampumaharjoitus"
    assert features[0]["properties"]["notices"] == ["VENEILIJÖITÄ KEHOTETAAN VAROVAISUUTEEN."]
    assert features[0]["properties"]["footer"] == "Varoituksia veneilijöille 12/2026"


async def test_empty_fields_fall_back_to_finnish_and_to_the_feeds_own_name() -> None:
    bare = warning(
        41,
        {"type": "MultiPoint", "coordinates": [[27.2, 60.55]]},
        NAVWARNTYPEGENERAL_FI=None,
        NAVWARNTYPEGENERAL_EN=None,
        WARNINGINFORMATION_EN=None,
        MESSAGESERIESIDENTIFIERNAMEOFSERIES_EN="",
        MESSAGESERIESIDENTIFIERWARNINGNUMBER=None,
        MESSAGESERIESIDENTIFIERYEAR=None,
    )
    [feature] = build_nautical_warning_features([bare], TEXTS)

    assert feature["properties"]["name"] == "Nautical warning"
    assert feature["properties"]["notices"] == ["VENEILIJÖITÄ KEHOTETAAN VAROVAISUUTEEN."]
    assert feature["properties"]["footer"] == "Varoituksia veneilijöille"
    assert feature["properties"]["details"] == [{"label": "Area", "value": "Gulf of Finland"}]


async def test_the_feed_credits_traficom(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    for layer, warnings in LAYERS.items():
        aioclient_mock.get(
            TRAFICOM_WFS,
            params={
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": f"avoin:{layer}",
                "outputFormat": "application/json",
                "srsName": "EPSG:4326",
            },
            json={"type": "FeatureCollection", "features": warnings},
        )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="nautical_warnings",
                title="Nautical warnings",
                unique_id=None,
                data={"area": HAMINA_AREA, "refresh_seconds": 600},
            )
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.nautical_warnings")
    assert state is not None
    assert state.state == "4"
    assert state.attributes["attribution"] == "Traficom, CC BY 4.0"
    assert state.attributes["feed_type"] == "sea"
    assert len(state.attributes["geojson"]["features"]) == 7
