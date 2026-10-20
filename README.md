# udiNetro

Universal Devices ISY / eisy Polyglot v3 (PG3x) Node Server for **Netro Home** smart irrigation controllers (Sprite, Spark, Pixie) and soil moisture sensors (Whisperer).

This node server uses **Netro Public API v2** (`https://api.netrohome.com/npa/v2`) to provide status monitoring, schedule insights, moisture trending, and irrigation control directly inside ISY/IoX.

---

## Features & Node Types

- **Service Node (`CONTROLLER`)**:
  - Primary service node managing configuration, device discovery, and dynamic profile synchronization.
- **Irrigation Controllers (`IRRCTRL`)**:
  - Monitors controller status (`Standby`, `Setup`, `Online`, `Watering`, `Offline`, `Sleeping`, `Power Off`, `Valve Error`), active zone count, next scheduled start time, previous end time, last online/offline events, battery level (for battery-powered controllers like Pixie), remaining daily API calls, last API update time (`GV19`), and last successful poll time (`TIME`).
  - **Commands**:
    - `UPDATE` (*Update Data*): Refreshes controller and child zone data from Netro API v2.
    - `ENABLE` (*Controller*): Enables (`Enabled`) or disables (`Disabled`) the controller.
    - `SKIPDAYS` (*Days to Skip Watering*): Skips scheduled watering for `0–365` days.
    - `STOPWATER` (*Stop All Watering*): Immediately stops watering across all zones.
- **Irrigation Zones (`IRRZONE`)**:
  - Automatically creates a child node for each enabled zone (or a single hose zone for 1-zone controllers like Pixie).
  - Reports zone status (`Awaiting Schedule start`, `Schedule Executing`, `Schedule Executed`, `No Schedule Defined`), zone number, zone configuration (`Smart`, `Smart Basic`, `Timer`), estimated moisture level (`0–100%`), multi-day moisture trend slope (`%/day`), previous start/end times, and next scheduled start/end times.
  - **Commands**:
    - `WATER` (*Water Zone*): Starts manual watering with configurable `DURATION` (*Water Run Time*, `0–120` minutes) and `DELAY` (*Start Delay*, `0–120` minutes).
    - `STOPWATER` (*Stop Watering*): Immediately stops active watering.
- **Moisture Sensors (`SENSORC` / `SENSORF`)**:
  - Uses `SENSORF` when `TEMP` is set to `F` (Fahrenheit) or `SENSORC` when `TEMP` is set to `C` (Celsius).
  - Reports soil moisture (`0–100%`), ambient temperature (`°F` or `°C`), sunlight (`LUX`), battery level (`0–100%`), connection status (`Offline`, `Online`, `Sleeping`), sensor data report timestamp, and last API update timestamp.
  - **Commands**:
    - `UPDATE` (*Update Data*): Polls the latest sensor readings from Netro API v2.
- **Dynamic Profile Generation**:
  - Automatically populates driver display names from dynamic/static profile definitions and pushes dynamic JSON profiles (`updateJsonProfile`, with static `profile/` fallback) after initial configuration and node creation complete. Pressing **Discover** in PG3x also refreshes the profile.

---

## How to Obtain Your Netro API v2 Keys

Netro Public API v2 uses **unique per-device API keys** rather than hardware serial numbers. Each controller and each soil sensor has its own distinct API key.

1. Log in to your Netro account via browser at [https://www.netrohome.com/shop](https://www.netrohome.com/shop).
2. Click on the **Account** menu.
3. Select **API Key** in the left sidebar menu.
4. All of your registered devices will be listed—click **Generate API Key** next to each device to create its unique encrypted API key string (e.g. `Sh6CZ1NWLj04crC_Hk7c3pBHdsvLLKurHtfjdx-Bi18`).
5. **Manually highlight and copy (`Cmd+C` / `Ctrl+C`)** the distinct API key text for each controller and sensor directly from the table (do **not** rely on Netro's "Copy" button, which has a web portal bug that copies the first device's key for every row).
6. In the Polyglot v3 **Configuration** page, paste all of your device API keys into the `SERIALID` parameter separated by spaces, then click **Save Changes**:
   ```text
   key_for_device_1 key_for_device_2 key_for_device_3
   ```

> **Important**: Verify that each pasted key in `SERIALID` is different—Netro's "Copy" button on the Account -> API Key page often copies the first key repeatedly. If duplicate keys are detected in `SERIALID`, the node server will display a warning notice in Polyglot and deduplicate the list.

---

## Configuration Parameters

Configure the following custom parameters in the Polyglot v3 UI under **Configuration**:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `SERIALID` | *(Required)* | Space-separated list of **Netro v2 device API keys** (one unique key per controller or sensor). |
| `TEMP` | `F` | Temperature unit for Netro sensors: `F` (Fahrenheit, `SENSORF`) or `C` (Celsius, `SENSORC`). |
| `EVENT_DAYS` | `-5` | Number of days back in time to query for watering and online/offline events (negative integer, e.g. `-5`). |
| `SCH_DAYS` | `7` | Number of days ahead to query for upcoming irrigation schedules (positive integer, e.g. `7`). |
| `MOIST_DAYS` | `-3` | Number of days back in time used to compute the linear moisture trend slope (negative integer, e.g. `-3`). |

---

## Polling & API Rate Limits

- **ShortPoll**: Sends a heartbeat pulse (`DON`, waits 5 seconds, then sends `DOF`) to ISY for each controller and sensor node.
- **LongPoll**: Queries the Netro Public API v2 for the latest device status, events, schedules, moisture estimates, and sensor readings (note: battery-powered sensors may sleep between reports, so the most recent reading before sleep is reported).

> **Note on Rate Limits**: Netro enforces a limit of **2,000 API calls per day** per device. A controller `longPoll` typically uses 4 API calls (`info`, `moistures`, `schedules`, and `events`), while a sensor `longPoll` uses 2 API calls (`info` and `sensor_data`). Avoid setting `longPoll` too aggressively.

---

## Changelog

- **0.2.6**
  - Added comprehensive unused node detection and removal during startup in `udiNetro.py` and `netroController.py` to automatically remove obsolete controllers, child zones (e.g. legacy `_z` addresses), and sensors from ISY.
- **0.2.5**
  - Added `TIME` (*Last Poll Time*) driver to `IRRCTRL` (`netroController`), updated only when a Netro API call succeeds with valid data.
  - Updated `heartbeat` on `shortPoll` to send `DON`, wait 5 seconds, and send `DOF` on every poll instead of toggling between polls.
- **0.2.4**
  - Standardized all `nodeDef` IDs (`CONTROLLER`, `IRRCTRL`, `IRRZONE`, `SENSORC`, `SENSORF`), `editor` IDs, `nls` prefixes, command IDs (`UPDATE`, `STOPWATER`, `SKIPDAYS`, `ENABLE`, `WATER`), and command parameter IDs (`DURATION`, `DELAY`) to uppercase alphanumeric without special characters or reserved words.
  - Added full `"nls"` dictionary to dynamic JSON profile payload (`updateJsonProfile`).
  - Added duplicate API key detection and warning notice in `SERIALID` parsing.
  - Removed redundant `self.poly.ready()` calls in child device nodes.
- **0.2.3**
  - Ported Netro Public API v2 support (`https://api.netrohome.com/npa/v2`) and base36 ISY node addressing for device API keys.
  - Added driver `'name'` definitions and dynamic JSON profile generation (`updateJsonProfile` with static `profile/` fallback) deferred until node initialization completes.
  - Fixed `TEMP`, `EVENT_DAYS`, `SCH_DAYS`, and `MOIST_DAYS` custom parameter parsing in `customParamsHandler`.
  - Fixed sensor `ISYupdate`/`longpoll` data persistence, controller `Enable` status mapping, zone `NO SCHEDULE` state handling, and HTTP session reuse.
- **0.2.1 / 0.2.0**
  - Initial Netro Public API v2 support and API key handling.
- **0.1.18**
  - Netro Public API v1 release.
