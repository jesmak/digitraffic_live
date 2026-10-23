# Digitraffic Live for Home Assistant

Home Assistant integration that turns Fintraffic's live ships, trains and road traffic data into map feeds, road
weather station sensors and railway station departures and arrivals.

[![GitHub Release][releases-shield]][releases] [![GitHub Release Date][release-date-shield]][releases] [![HACS][hacs-shield]][hacs] [![License][license-shield]](LICENSE)

<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/dashboard-light.png#gh-light-mode-only" width="1280" alt="A dashboard around Tampere, with a map of trains coloured by their delay, road weather stations with their temperatures and a road works site, the list of them beside it with a late train's details open, the departures from Tampere station, and the road conditions at three road weather stations">
<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/dashboard-dark.png#gh-dark-mode-only" width="1280" alt="A dashboard around Tampere, with a map of trains coloured by their delay, road weather stations with their temperatures and a road works site, the list of them beside it with a late train's details open, the departures from Tampere station, and the road conditions at three road weather stations">

## What is it?

A custom component that turns live ships, trains and road traffic data from
[Fintraffic's Digitraffic](https://www.digitraffic.fi/) open data into **map feeds**: one sensor per feed, holding
everything in it as GeoJSON.

Show the feeds on a map with [map-feed-card](https://github.com/jesmak/map-feed-card), which draws heading arrows,
colours by ship type or train delay, and shows each item's details beside the map or in a list. The feed format is
documented in [map-feed-format.md](https://github.com/jesmak/map-feed-card/blob/main/docs/map-feed-format.md), so other integrations and template entities can produce feeds
for the same card.

- **Ship feeds:** AIS positions inside an area, with names, types, destinations and draughts from the vessel
  register. Icebreakers can be highlighted.
- **Train feeds:** GPS positions of running trains on a route or inside an area, with delays, the last station
  passed, the next stop with track, passenger notices, and the composition when a popup is opened.
- **Traffic message feeds:** road works, traffic announcements and accidents, weight restrictions and exempted
  transports, with the stretch of road they cover, their times, working hours and restrictions.
- **Road maintenance feeds:** snow ploughs, gritters and other maintenance vehicles on state roads, and optionally
  where they have worked in the last hours.
- **Road condition feeds:** Fintraffic's driving conditions for sections of the main roads, now or up to 12 hours
  ahead.
- **Road weather station feeds:** road and air temperature, road surface, grip, wind and precipitation.
- **Weather camera feeds:** the latest picture from each view of Fintraffic's road cameras.
- **Road weather stations and weather cameras** as devices of their own: sensors for road and air temperature, road
  surface, grip and its grade, road weather warnings, wind, precipitation and visibility, and an image entity for
  each camera view. Shown by [road-conditions-card](https://github.com/jesmak/road-conditions-card).
- **Station departures:** the next passenger trains to leave or reach a railway station, the departures optionally only
  those that stop at another station later, with live estimates, delays, tracks, cancellations and their reasons.
  Shown by [departures-card](https://github.com/jesmak/departures-card).

## Installation

### With HACS

1. Add this repository to HACS custom repositories with type **Integration**
2. Search for Digitraffic Live in HACS and download it
3. Restart Home Assistant
4. Add the integration in Settings › Devices & services, then add feeds from its page

### Manual

1. Download the source code from the latest release
2. Copy the `custom_components/digitraffic_live` folder to your Home Assistant installation's
   `config/custom_components` folder
3. Restart Home Assistant
4. Add the integration in Settings › Devices & services, then add feeds from its page

## Settings

### Integration

| Name     | Type | Description                                                  | Default                   |
| -------- | ---- | ------------------------------------------------------------ | ------------------------- |
| language | enum | Language of the texts written into feeds: `fi` or `en` | Home Assistant's language |

### Ship feed

Add with **Add ship feed** on the integration page. Every feed creates one sensor named after the feed.

| Name                  | Type    | Description                                                                      | Default     |
| --------------------- | ------- | -------------------------------------------------------------------------------- | ----------- |
| Name                  | string  | Name of the feed and its sensor                                                  |             |
| Area                  | circle  | Centre and radius, picked on a map                                               | home, 15 km |
| Ship types            | list    | `cargo`, `tanker`, `passenger`, `pilot`, `tug`, `fishing`, `pleasure`, `other`   | all         |
| Include moored        | boolean | Include moored and anchored ships                                                | on          |
| Highlight icebreakers | boolean | Uses winter navigation data. Icebreakers are shown whatever the type filters say | off         |
| Maximum position age  | minutes | Ships whose latest position is older are left out                                | 30          |
| Update interval       | seconds | How often the feed is fetched, at least 30                                       | 60          |

### Train feed

Add with **Add train feed** on the integration page. Choose route stations, an area, or both.

| Name                 | Type    | Description                                                                                    | Default     |
| -------------------- | ------- | ---------------------------------------------------------------------------------------------- | ----------- |
| Name                 | string  | Name of the feed and its sensor                                                                |             |
| Route stations       | list    | Only trains that stop at every chosen station, e.g. Lappeenranta, or Helsinki and Lappeenranta | none        |
| Train categories     | list    | Long-distance, commuter, cargo, locomotive, test drive, on-track machines, shunting            | all         |
| Limit to an area     | boolean | Only trains inside the area                                                                    | off         |
| Area                 | circle  | Centre and radius, picked on a map                                                             | home, 30 km |
| Maximum position age | minutes | Trains whose latest position is older are left out                                             | 15          |
| Update interval      | seconds | How often the feed is fetched, at least 30                                                     | 60          |

### Traffic message feed

Add with **Add traffic message feed**. Road works, announcements and restrictions whose road stretch or area touches
the feed's area are included.

| Name                       | Type    | Description                                                                          | Default     |
| -------------------------- | ------- | ------------------------------------------------------------------------------------ | ----------- |
| Name                       | string  | Name of the feed and its sensor                                                      |             |
| Area                       | circle  | Centre and radius, picked on a map                                                   | home, 30 km |
| Message types              | list    | Road works, traffic announcements, weight restrictions, exempted transports          | all         |
| Road works starting within | days    | Upcoming road works are included this many days ahead. `0` shows only those in force | 7           |
| Update interval            | seconds | How often the feed is fetched, at least 30                                           | 300         |

### Road maintenance feed

Add with **Add road maintenance feed**. Covers state roads maintained under Fintraffic's contracts. Most city
streets are not included.

| Name                            | Type    | Description                                                        | Default     |
| ------------------------------- | ------- | ------------------------------------------------------------------ | ----------- |
| Name                            | string  | Name of the feed and its sensor                                    |             |
| Area                            | circle  | Centre and radius, picked on a map                                 | home, 30 km |
| Tasks                           | list    | Ploughing, salting, sanding, brushing and 43 other tasks           | all         |
| Maximum position age            | minutes | Vehicles whose latest position is older are left out               | 60          |
| Show where vehicles have worked | boolean | Draw the vehicles' routes as lines                                 | on          |
| Routes from the last            | hours   | How far back routes are drawn, at most 24                          | 2           |
| Update interval                 | seconds | How often the feed is fetched, at least 30                         | 60          |

Digitraffic gives a vehicle no id of its own, only that of the stretch it drove last, which changes every few
minutes. The feed follows a vehicle from one update to the next along its route, so its marker keeps its id while the
route goes on. When the route breaks, such as in a gap in Digitraffic's data, the vehicle starts over as a new item,
and its details close if they are open. A route line's id changes when its oldest stretch falls out of **Routes from
the last**.

### Road condition feed

Add with **Add road condition feed**. Road sections are drawn as lines coloured by driving conditions.

| Name                 | Type    | Description                                                | Default     |
| -------------------- | ------- | ---------------------------------------------------------- | ----------- |
| Name                 | string  | Name of the feed and its sensor                            |             |
| Area                 | circle  | Centre and radius, picked on a map                         | home, 50 km |
| Time                 | enum    | Now, or in 2, 4, 6 or 12 hours                             | now         |
| Only poor conditions | boolean | Leave out sections whose conditions are normal or unknown  | off         |
| Update interval      | seconds | How often the feed is fetched, at least 30                 | 600         |

### Road weather station and weather camera feeds

Add with **Add road weather station feed** or **Add weather camera feed**. Both have a name, an area (home, 30 km
by default) and an update interval (300 and 600 seconds). Station markers show the air temperature, or the road
temperature if you choose so with **Value on the map**. The popup has both. Markers turn amber when the station
gives any warning, its road is frosty, snowy or slushy, or its grip is that of a winter road (see
[Grip condition](#grip-condition)). They turn red when the road is icy, the station raises an alarm or its grip is
very slippery.

### Road weather station

Add with **Add road weather station** to get sensors for one station anywhere in Finland, for example to show on a
dashboard. The station becomes a device named after it, with these sensors, which
[road-conditions-card](https://github.com/jesmak/road-conditions-card) shows:

<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/road-weather-station-light.png#gh-light-mode-only" width="510" alt="A road weather station on road-conditions-card, in good winter conditions with snow on the road, wind with gusts, snowfall and a road weather warning">
<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/road-weather-station-dark.png#gh-dark-mode-only" width="510" alt="A road weather station on road-conditions-card, in good winter conditions with snow on the road, wind with gusts, snowfall and a road weather warning">


| Sensor               | Description                                                                          |
| -------------------- | ------------------------------------------------------------------------------------ |
| Road temperature     | °C                                                                                   |
| Air temperature      | °C                                                                                   |
| Road surface         | Dry, moist, wet, wet and salty, frost, snow, ice, probably moist and salty or slushy |
| Grip                 | Friction coefficient µ, 0–1                                                          |
| Grip condition       | Good or fair grip, good or fair winter conditions, slippery or very slippery         |
| Road weather warning | OK, beware, alarm, frost or rain                                                     |
| Wind speed           | m/s                                                                                  |
| Wind gusts           | m/s                                                                                  |
| Precipitation        | None, or light, moderate or heavy rain, snow or sleet                                |
| Precipitation type   | None, drizzle, rain, snow, sleet, hail, freezing drizzle, freezing rain and others   |
| Rain intensity       | mm/h                                                                                 |
| Visibility           | km                                                                                   |

Stations have up to four road sensors and two optical sensors, and many lack the first of them. Each value comes from
the first sensor that has one, road sensors before optical ones. A value that the station doesn't measure at all stays
unknown. Values are fetched every 300 seconds, and **Change road weather station** changes the interval. Wind is in
m/s, as Finnish weather services give it. If you prefer km/h, change the unit in the entity's settings.

#### Grip condition

The grip condition follows the slipperiness classification of the Finnish Road Administration, as published by the
Finnish Meteorological Institute (Nurmi, Hippi and Juga, *Evaluation of FMI's new forecast model of road surface
friction*, SIRWEC 2010). The classification puts the two highest classes together as a good road condition. Here
they are kept apart as good and fair grip.

| Grip µ      | Condition              | Typical surface         | On the map |
| ----------- | ---------------------- | ----------------------- | ---------- |
| 0.45 and up | Good grip              | Clear                   |            |
| 0.30–0.44   | Fair grip              | Clear                   |            |
| 0.25–0.29   | Good winter conditions | Rough ice, packed snow  | Amber      |
| 0.20–0.24   | Fair winter conditions | Packed snow             | Amber      |
| 0.15–0.19   | Slippery               | Icy                     | Amber      |
| below 0.15  | Very slippery          | Wet ice                 | Red        |

A value on a limit belongs to the class above it. The condition comes from the grip alone. The road surface sensor
tells whether the road is dry or wet, and a wet road often still has good grip.

### Weather camera

Add with **Add weather camera** to get the pictures of one camera anywhere in Finland. The camera becomes a device with
an image entity for each of its views, named after the direction it looks, such as *Imatralle*. Cameras take a new
picture about every ten minutes, and the image entity updates when they do. New pictures are checked for every 600
seconds, and **Change weather camera** changes the interval.

### Station departures

Add with **Add station departures** to get a sensor with the next passenger trains to leave one station, to reach it,
or both. Both makes two sensors from one request, the arrivals named after the departures with "arrivals" added. The
direction is chosen when the station is added, and can't be changed after. Cargo and work trains are left out.

<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/station-departures-light.png#gh-light-mode-only" width="510" alt="A station departures sensor on departures-card, with a track works notice, the next train large with its delay and track, and a cancelled train among the ones after it">
<img src="https://raw.githubusercontent.com/jesmak/digitraffic_live/main/docs/images/station-departures-dark.png#gh-dark-mode-only" width="510" alt="A station departures sensor on departures-card, with a track works notice, the next train large with its delay and track, and a cancelled train among the ones after it">

| Name             | Type    | Description                                                                                             | Default    |
| ---------------- | ------- | ------------------------------------------------------------------------------------------------------- | ---------- |
| Name             | string  | Name of the sensor                                                                                      |            |
| Station          | station | The station the trains leave from or arrive at                                                          |            |
| Trains           | choice  | Departures, arrivals or both                                                                            | departures |
| Stops at         | station | Only departing trains that stop at this station later, such as only those from Helsinki to Lappeenranta | none       |
| Number of trains | number  | How many of the next trains not cancelled each sensor lists, 1–20, with the cancelled ones among them   | 5          |
| Update interval  | seconds | How often the trains are fetched, at least 30                                                           | 60         |

## Sensors

Every feed has one sensor, whose state is the number of items in the feed: ships, trains, traffic messages,
maintenance vehicles, weather stations or cameras. For road condition feeds it is the number of road sections with
poor or extremely poor conditions, which is handy in automations. The attributes follow the
[Map Feed format](https://github.com/jesmak/map-feed-card/blob/main/docs/map-feed-format.md):

| Name               | Description                                        |
| ------------------ | -------------------------------------------------- |
| `map_feed_version` | Always `1`                                         |
| `geojson`          | The feed's items as a GeoJSON FeatureCollection    |
| `area`             | The feed's area, if it has one                     |
| `updated`          | When the feed was last fetched                     |
| `attribution`      | Data credit                                        |
| `feed_type`        | `ship`, `train` or `road`, what the feed is about  |
| `list`             | For trains, the orders the card's list offers      |

None of the attributes are stored in the recorder, only the count. A feed that can't be fetched becomes
unavailable until the next successful update.

### Station departures

A station departures sensor's state is the time of the next train that isn't cancelled, and an arrivals sensor's the
time of the next one that hasn't come in either. The time is the live estimate when there is one, otherwise the
timetable time. The attributes follow the
[departures format](https://github.com/jesmak/departures-card/blob/main/docs/departures-format.md), which
[departures-card](https://github.com/jesmak/departures-card) shows:

| Name                 | Description                                                  |
| -------------------- | ------------------------------------------------------------ |
| `departures_version` | Always `1`                                                   |
| `direction`          | `arrivals`, or `departures` for a station of both directions |
| `stop_id`            | The station's short code, e.g. `HKI`                         |
| `stop_name`          | The station's name                                           |
| `notices`            | Station-wide notices in force now                            |
| `departures`         | The next departures or arrivals, soonest first               |
| `attribution`        | Data credit                                                  |

Each departure has its train (`IC 45`, or the line letter of a commuter train), where it is heading, the timetable
time and the live estimate, the delay in seconds, the track, and whether it is cancelled. A train's own passenger
notice, such as "Passengers are directed to train S 106", is in `notice`. Without one, a cancelled or late train has
the reason there instead, in the integration's language: rolling stock, track work, traffic control and so on.
Digitraffic gives the reasons as category codes; their texts are the integration's own.

An arrivals sensor lists the trains coming in, in the same shape, with where each comes from, its first station, in
place of where it is heading. A train that starts at the station has no arrival, and a train through it is on both
sensors. A ring train back where it started, as the I and P trains at Helsinki, comes from there, and one through the
station twice, as they pass Pasila, is listed once, by its pass still to come. An arrival that has come in is marked
`arrived`, with its actual time as the estimate, and stays for half an hour after it, as does a cancelled one. A
departure is listed until a minute past its time, a cancelled one too. The number of trains counts those not cancelled,
still to come for arrivals, and the cancelled ones among them are listed too, so a run of cancellations doesn't push the
next train off the list. The latest two arrivals that are over, come in or cancelled and past their time, are listed
besides them. "Stops at" limits departures only, so it can't be set for arrivals or both.

`notices` holds Digitraffic's passenger notices for the whole station while they are in force, such as track works
with buses replacing trains, in the integration's language when Digitraffic has it, otherwise in Finnish. The
departures and the notices aren't stored in the recorder, only the next departure time and the station's other,
small attributes.

## Actions

### `digitraffic_live.get_train_composition`

Returns a train's cars and services as detail rows. The map feed card calls it when a train is selected.

| Field            | Description                               |
| ---------------- | ----------------------------------------- |
| `departure_date` | The date the train left its first station |
| `train_number`   | For example `8` for IC 8                  |

## Examples

Maps are drawn by [map-feed-card](https://github.com/jesmak/map-feed-card), whose README has examples. Entity IDs are made from the station or camera name and Home Assistant's language, so
check yours on the device's page.

### A road weather station

[road-conditions-card](https://github.com/jesmak/road-conditions-card) finds a station's sensors by itself, so it
needs only the station's device. Pick it in the card's visual editor:

```yaml
type: custom:road-conditions-card
stations:
  - device: 0123456789abcdef0123456789abcdef
    name: Road 9 Hillside
```

Home Assistant's own cards work too:

```yaml
type: entities
title: Road 9 Hillside
entities:
  - sensor.road_9_example_hillside_grip_condition
  - sensor.road_9_example_hillside_road_temperature
  - sensor.road_9_example_hillside_road_surface
  - sensor.road_9_example_hillside_precipitation_type
  - sensor.road_9_example_hillside_road_weather_warning
```

### Station departures

```yaml
type: custom:departures-card
entities:
  - entity: sensor.trains_tampere_helsinki
    subtitle: to Helsinki
```

A station's departures and arrivals as one list, by time:

```yaml
type: custom:departures-card
combine: true
entities:
  - sensor.trains_tampere
  - sensor.trains_tampere_arrivals
```

### Weather cameras

Each picture is a `picture-entity` card. In a sections view, `columns: 6` puts two cards side by side:

```yaml
type: grid
cards:
  - type: picture-entity
    entity: image.road_9_example_hillside_towards_example
    name: Road 9 Hillside
    show_state: false
    fit_mode: cover
    grid_options:
      columns: 6
  - type: picture-entity
    entity: image.road_9_example_hillside_towards_sample
    name: Road 9 Hillside
    show_state: false
    fit_mode: cover
    grid_options:
      columns: 6
```

## Upgrading from 1.0

Nothing is required. Road weather stations get their new sensors (grip condition, wind, precipitation and
visibility) on the next restart, and entity IDs and attributes carry over. Swedish is no longer one of the
integration's languages. An integration set to Swedish is switched to English when it starts, and can be set to
Finnish in its settings.

## Data

Traffic data: [Fintraffic / digitraffic.fi](https://www.digitraffic.fi/), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Requests carry a `Digitraffic-User` header with the integration's name and version, as Digitraffic asks. It
contains no personal information. AIS only shows vessels that transmit it, which leaves out most small leisure
boats.

Keep areas to what a map shows at once, a radius of a few tens of kilometres. A 200 km traffic message or maintenance
feed is several hundred kilobytes, which Home Assistant sends to every open dashboard on each update. Weather station
and camera feeds look up each station's details once a day, one request per station.

Traffic messages are published in Finnish only. Their labels and the restriction and work types are written in the
integration's language. Road geometries are simplified to keep the feeds small.

## Translating

The integration's own texts are in two places. `translations/<language>.json` has Home Assistant's UI, and
`texts/<language>.json` the texts written into feeds. To add a language, copy both `en.json` files to the new
language's code, translate the values, and add the code to `LANGUAGES` in `const.py`. The tests check that every
language has the same keys and placeholders as English. Names of stations, places and traffic messages come from
Digitraffic as they are.

## Development

Requires Python 3.14.

```
python3.14 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest
.venv/bin/ruff check .
```

| Path                                | What it contains                                      |
| ----------------------------------- | ----------------------------------------------------- |
| `__init__.py`                       | Setup: one coordinator per feed                       |
| `config_flow.py`                    | The integration, feed, station and camera forms       |
| `coordinator.py`                    | Fetching feeds, and data shared between feeds         |
| `sensor.py`                         | The feed sensors and road weather station sensors     |
| `image.py`                          | Weather camera image entities                         |
| `ships.py`, `trains.py`             | Interpreting Digitraffic data and building feed items |
| `traffic_messages.py`, `maintenance.py`, `road_conditions.py`, `weather_stations.py`, `weather_cameras.py` | The same for road data |
| `geo.py`                            | Areas, geometry tests and line simplification         |
| `cache.py`                          | Caching station details                               |
| `feed.py`                           | Map Feed format building blocks                       |
| `api.py`                            | Digitraffic HTTP client                               |
| `services.py`                       | The composition action                                |
| `texts.py`, `texts/<language>.json` | Texts written into feeds                              |
| `translations/<language>.json`      | Home Assistant UI texts                               |
| `docs/screenshots.json`             | The made-up data the README's screenshots are taken from |

## Support

Hey dude! Help me out for a couple of :beers: or a :coffee:!

[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://www.buymeacoffee.com/jesmak)

## License

MIT, see [LICENSE](LICENSE).

[releases-shield]: https://img.shields.io/github/release/jesmak/digitraffic_live.svg?style=for-the-badge
[release-date-shield]: https://img.shields.io/github/release-date/jesmak/digitraffic_live?style=for-the-badge
[releases]: https://github.com/jesmak/digitraffic_live/releases
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://hacs.xyz/docs/faq/custom_repositories/
[license-shield]: https://img.shields.io/github/license/jesmak/digitraffic_live.svg?style=for-the-badge
