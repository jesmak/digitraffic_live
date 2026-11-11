"""Water restriction areas: which of Väylävirasto's areas a feed takes, and the outlines built from them."""

from __future__ import annotations

from datetime import date
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.digitraffic_live.api import VAYLAVIRASTO_WFS
from custom_components.digitraffic_live.const import DOMAIN
from custom_components.digitraffic_live.texts import load_texts
from custom_components.digitraffic_live.water_restrictions import WaterRestrictionFeedConfig, build_water_restriction_features

from .conftest import HAMINA_AREA

TEXTS = load_texts("en")
TODAY = date(2026, 11, 11)


def square(west: float, south: float, size: float = 0.01) -> dict[str, Any]:
    east, north = round(west + size, 5), round(south + size, 5)
    return {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}


def restriction(number: int, geometry: dict[str, Any], names: str, codes: str, **fields: Any) -> dict[str, Any]:
    """An area as the layer gives it, with invented contents."""
    return {
        "type": "Feature",
        "id": f"rajoitusalue_a_uusi.{number}",
        "geometry": geometry,
        "properties": {
            "id": number,
            "rajoitustyyppi": names,
            "rajoitustyypit": codes,
            "suuruus": None,
            "poikkeus": None,
            "lisatieto": None,
            "paatostila": "Toistaiseksi",
            "alkupaivamaara": None,
            "loppupaivamaara": None,
            "nimisijainti": None,
            "vaylan_nimi": None,
            **fields,
        },
    }


HARBOUR_SPEED_LIMIT = restriction(
    1,
    square(27.19, 60.55),
    "Nopeusrajoitus, Aallokon aiheuttamisen kielto",
    "01, 02",
    suuruus="9",
    nimisijainti="Kuusiluodon satama",
    alkupaivamaara="2014-07-01Z",
    vaylan_nimi="[9901: Kuusiluodon väylä](vaylat:jnro=9901)\\n[9902: Satamaväylä](vaylat:jnro=9902)",
    lisatieto="Voimassaolojakso: koko vuoden",
    poikkeus="aallokonmuodostaminen kielletty --- kielto ei koske\r\npelastustehtäviä",
)
CABLE = restriction(2, square(27.21, 60.56), "Ankkurin käyttökielto", "06")
FAR_AWAY = restriction(3, square(21.0, 60.0), "Nopeusrajoitus", "01", suuruus="10")
ENDED = restriction(4, square(27.2, 60.57), "Nopeusrajoitus", "01", suuruus="5", paatostila="Määräaikainen", loppupaivamaara="2026-05-31Z")
ENDS_TODAY = restriction(5, square(27.2, 60.58), "Vesihiihtokielto", "12", alkupaivamaara="2026-05-01Z", loppupaivamaara="2026-11-11Z")
UNKNOWN_TYPE = restriction(6, square(27.18, 60.56), "Tuntematon", "0")
NEW_TYPE = restriction(7, square(27.17, 60.56), "Nopeusrajoitus, Sukelluskielto", "01, 99")

LAYER = {"type": "FeatureCollection", "features": [HARBOUR_SPEED_LIMIT, CABLE, FAR_AWAY, ENDED, ENDS_TODAY, UNKNOWN_TYPE, NEW_TYPE]}


def build(restriction_types: list[str] | None = None, language: str = "en") -> dict[str, dict[str, Any]]:
    config = WaterRestrictionFeedConfig.from_data({"area": HAMINA_AREA, "restriction_types": restriction_types})
    features = build_water_restriction_features(LAYER, config, load_texts(language), TODAY)
    return {feature["id"]: feature for feature in features}


def test_the_areas_in_force_that_touch_the_area_are_taken() -> None:
    # The far one is outside the circle, and one ended in May. An area is in force on its last day.
    assert list(build()) == [f"water_restriction:{number}" for number in (1, 2, 5, 6, 7)]


def test_an_area_is_a_dashed_outline_with_its_restrictions_and_texts() -> None:
    area = build()["water_restriction:1"]

    assert area["geometry"]["type"] == "Polygon"
    assert area["properties"] == {
        "name": "Kuusiluodon satama",
        "kind": "sea.restriction",
        "dashed": True,
        "subtitle": "Speed limit 9 km/h, No wake",
        "details": [
            {"label": "Fairway", "value": "Kuusiluodon väylä, Satamaväylä"},
            {"label": "In force", "value": "from 1.7.2014"},
        ],
        "notices": ["Voimassaolojakso: koko vuoden", "aallokonmuodostaminen kielletty", "kielto ei koske pelastustehtäviä"],
    }


def test_an_area_without_a_place_is_named_after_its_restrictions() -> None:
    assert build()["water_restriction:2"]["properties"] == {"name": "No anchoring", "kind": "sea.restriction", "dashed": True}
    assert build(language="fi")["water_restriction:2"]["properties"]["name"] == "Ankkurin käyttökielto"


def test_a_fixed_term_area_shows_both_its_dates() -> None:
    assert build()["water_restriction:5"]["properties"]["details"] == [{"label": "In force", "value": "1.5.2026 – 11.11.2026"}]


def test_a_type_without_a_name_keeps_the_layers_finnish_one() -> None:
    features = build()

    assert features["water_restriction:6"]["properties"]["name"] == "Tuntematon"
    assert features["water_restriction:7"]["properties"]["name"] == "Speed limit, Sukelluskielto"


def test_only_the_chosen_types_are_taken() -> None:
    # An area with several restrictions is in when one of them is chosen.
    assert list(build(["no_wake", "no_anchoring"])) == ["water_restriction:1", "water_restriction:2"]
    # Unknown types and those without a name are the other restrictions. The speed limit brings the last one in too.
    assert list(build(["other"])) == ["water_restriction:6", "water_restriction:7"]
    assert list(build(["speed_limit"])) == ["water_restriction:1", "water_restriction:7"]


async def test_the_feed_asks_by_area_counts_its_areas_and_credits_vaylavirasto(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to("2026-11-11T12:00:00+00:00")
    aioclient_mock.get(
        VAYLAVIRASTO_WFS,
        params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": "vesivaylatiedot:rajoitusalue_a_uusi",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "bbox": "26.9235,60.4341,27.4725,60.7039,EPSG:4326",
        },
        json=LAYER,
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Digitraffic",
        data={"language": "en"},
        subentries_data=[
            ConfigSubentryData(
                subentry_type="water_restrictions",
                title="Water restrictions",
                unique_id=None,
                data={"area": HAMINA_AREA, "refresh_seconds": 3600},
            )
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.water_restrictions")
    assert state is not None
    assert state.state == "5"
    assert state.attributes["attribution"] == "Väylävirasto, CC BY 4.0"
    assert state.attributes["feed_type"] == "sea"
    assert len(state.attributes["geojson"]["features"]) == 5
