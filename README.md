# udiNetro

Universal Devices ISY / eisy Polyglot v3 (PG3) Node Server for **Netro Home** smart irrigation controllers (Sprite, Spark, Pixie) and soil moisture sensors (Whisperer).

This node server uses **Netro Public API v2** (`https://api.netrohome.com/npa/v2`) to provide status monitoring, schedule insights, moisture trending, and irrigation control directly inside ISY/IoX.

---

## Features

- **Netro API v2 Support**: Uses per-device API keys generated from the Netro Home portal/app.
- **Irrigation Controllers (`irrctrl`)**:
  - Monitors controller status (`Standby`, `Setup`, `Online`, `Watering`, `Offline`, `Sleeping`, `Power Off`), active zone count, next scheduled start time, previous end time, last online/offline events, battery level (for battery-powered controllers like Pixie), remaining daily API calls, and last API update time.
  - Supports enabling/disabling the controller, skipping watering for `N` days, stopping all watering, and manual data refresh.
- **Irrigation Zones (`zone`)**:
  - Automatically creates a child node for each enabled zone (or a single hose zone for 1-zone controllers).
  - Reports zone status, zone number, zone configuration (`Smart`, `Assistant`, `Timer`), estimated moisture level (`0–100%`), multi-day moisture trend slope (`%/day`), previous start/end times, and next scheduled start/end times.
  - Supports manual watering with configurable duration and start delay, as well as stopping active watering.
- **Moisture Sensors (`sensor` / `sensorF`)**:
  - Reports soil moisture (`%`), ambient temperature (`°C` or `°F`), sunlight (`lux`), battery level (`%`), connection status, sensor report timestamp, and last API update timestamp.
- **Dynamic Profile Generation**:
  - Automatically populates driver names from dynamic/static profile definitions and pushes dynamic JSON profiles (`updateJsonProfile`) once all nodes have finished initializing.

---

## Configuration Parameters

Configure the following custom parameters in the Polyglot v3 UI under **Configuration**:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `SERIALID` | *(Required)* | Space-separated list of **Netro v2 device API keys** (one key per controller or sensor, generated from the Netro app/website). |
| `EVENT_DAYS` | `-5` | Number of days back in time to query for watering and online/offline events (negative integer, e.g. `-5`). |
| `SCH_DAYS` | `7` | Number of days ahead to query for upcoming irrigation schedules (positive integer, e.g. `7`). |
| `MOIST_DAYS` | `-3` | Number of days back in time used to compute the linear moisture trend slope (negative integer, e.g. `-3`). |
| `TEMP` | `F` | Temperature unit for Netro sensors: `F` (Fahrenheit) or `C` (Celsius). |

---

## Polling & API Rate Limits

- **ShortPoll**: Sends a heartbeat (`DON`/`DOF`) to ISY for each controller and sensor node.
- **LongPoll**: Queries the Netro Public API v2 for the latest device status, events, schedules, moisture estimates, and sensor readings (note: battery-powered sensors may sleep between reports, so the most recent reading before sleep is reported).

> **Note on Rate Limits**: Netro enforces a limit of **2,000 API calls per day** per device. A controller `longPoll` typically uses 4 API calls (`info`, `moistures`, `schedules`, and `events`), while a sensor `longPoll` uses 2 API calls (`info` and `sensor_data`). Avoid setting `longPoll` too aggressively.

---

## Changelog

- **0.2.3**
  - Ported Netro Public API v2 support (`https://api.netrohome.com/npa/v2`) and base36 ISY node addressing for device API keys.
  - Added driver `'name'` definitions and dynamic JSON profile generation (`updateJsonProfile` with static `profile/` fallback) deferred until node initialization completes.
  - Fixed `TEMP`, `EVENT_DAYS`, `SCH_DAYS`, and `MOIST_DAYS` custom parameter parsing in `customParamsHandler`.
  - Fixed sensor `ISYupdate`/`longpoll` data persistence, controller `Enable` status mapping, zone `NO SCHEDULE` state handling, and HTTP session reuse.
- **0.2.1 / 0.2.0**
  - Initial Netro Public API v2 support and API key handling.
- **0.1.18**
  - Netro Public API v1 release.
