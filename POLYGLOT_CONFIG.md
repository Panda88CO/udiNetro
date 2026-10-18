# Netro Irrigation Configuration

This node server uses **Netro Public API v2** to connect your Netro smart irrigation controllers (Sprite, Spark, Pixie) and soil moisture sensors (Whisperer) to ISY / eisy.

### Obtaining Your Device API Keys (Netro API v2)

Netro Public API v2 uses **unique per-device API keys** rather than 12-character hardware serial numbers. Each controller and sensor has its own distinct API key:

1. Log in to the **Netro Home Web Portal** at [https://home.netrohome.com](https://home.netrohome.com) using your Netro account credentials.
2. Go to **Settings / Account -> API Key** (or select a device and open its **Device Settings**).
3. Select your controller or sensor and generate/copy its **API Key** (a ~43-character token such as `Sh6CZ1NWLj04crC_Hk7c3pBHdsvLLKurHtfjdx-Bi18`).
4. **Repeat for each device**: Switch to each of your other controllers and sensors in the Netro portal to obtain the unique API key for each one.
5. Paste all device API keys into the `SERIALID` parameter below, separated by a single space (`key1 key2 key3`).

---

### Custom Configuration Parameters

| Key | Default | Description |
| :--- | :--- | :--- |
| **`SERIALID`** | *(Required)* | Space-separated list of **Netro v2 device API keys** (one unique key per controller or sensor). Example: `key1 key2 key3` |
| **`TEMP`** | `F` | Temperature unit for Netro sensors: `F` (Fahrenheit) or `C` (Celsius). |
| **`EVENT_DAYS`** | `-5` | Number of days back in time to look for watering and online/offline events (negative integer, e.g. `-5`). |
| **`SCH_DAYS`** | `7` | Number of days into the future to look for upcoming irrigation schedules (positive integer, e.g. `7`). |
| **`MOIST_DAYS`** | `-3` | Number of days back in time used to calculate the zone moisture trend slope (negative integer, e.g. `-3`). |

---

### Polling & Rate Limits

- **shortPoll**: Sends a heartbeat (`DON`/`DOF`) to ISY for each controller and sensor node.
- **longPoll**: Polls the Netro Public API v2 for the latest device status, schedules, events, moisture estimates, and sensor data.
- **Rate Limit**: Netro enforces a limit of **2,000 API calls per day** per device (a controller `longPoll` uses 4 calls; a sensor `longPoll` uses 2 calls). Avoid setting `longPoll` too short.

