# Netro Irrigation Configuration

This node server uses **Netro Public API v2** to connect your Netro smart irrigation controllers (Sprite, Spark, Pixie) and soil moisture sensors (Whisperer) to ISY / eisy.

### Obtaining Your Device API Keys (Netro API v2)

Netro Public API v2 uses **unique per-device API keys** rather than 12-character hardware serial numbers. Each controller and sensor has its own distinct API key:

1. Log in to your Netro account via browser at [https://www.netrohome.com/shop](https://www.netrohome.com/shop).
2. Click on the **Account** menu and select **API Key** in the left sidebar menu.
3. Your registered devices will be listed—click **Generate API Key** for each controller and sensor to create its unique API key string (e.g. `Sh6CZ1NWLj04crC_Hk7c3pBHdsvLLKurHtfjdx-Bi18`).
4. **Manually highlight and copy (`Cmd+C` / `Ctrl+C`)** the distinct API key text for each device directly from the page (do **not** use Netro's "Copy" button, which has a bug on their website that copies the first device's key for every row). Paste the keys into `SERIALID` separated by a single space (`key1 key2 key3`), then click **Save Changes**.

---

### Custom Configuration Parameters

| Key | Default | Description |
| :--- | :--- | :--- |
| **`SERIALID`** | *(Required)* | Space-separated list of **Netro v2 device API keys** (one unique key per controller or sensor). Example: `key1 key2 key3` |
| **`TEMP`** | `F` | Temperature unit for Netro sensors: `F` (Fahrenheit, `SENSORF`) or `C` (Celsius, `SENSORC`). |
| **`EVENT_DAYS`** | `-5` | Number of days back in time to look for watering and online/offline events (negative integer, e.g. `-5`). |
| **`SCH_DAYS`** | `7` | Number of days into the future to look for upcoming irrigation schedules (positive integer, e.g. `7`). |
| **`MOIST_DAYS`** | `-3` | Number of days back in time used to calculate the zone moisture trend slope (negative integer, e.g. `-3`). |

---

### Created Nodes & Profile Refresh

- **`CONTROLLER`**: Primary service node.
- **`IRRCTRL`**: Created for each Netro controller key; automatically creates child **`IRRZONE`** nodes for each enabled zone (or a single hose zone for 1-zone controllers).
- **`SENSORF` / `SENSORC`**: Created for each Netro Whisperer soil sensor key.
- **Dynamic Profile**: Node definitions and NLS labels are pushed automatically once all nodes finish initializing. You can also click **Discover** in PG3x to refresh the profile at any time.

---

### Polling & Rate Limits

- **shortPoll**: Sends a heartbeat pulse (`DON`, waits 5 seconds, then sends `DOF`) to ISY for each controller and sensor node.
- **longPoll**: Polls the Netro Public API v2 for the latest device status, schedules, events, moisture estimates, and sensor data.
- **Rate Limit**: Netro enforces a limit of **2,000 API calls per day** per device (a controller `longPoll` uses 4 calls; a sensor `longPoll` uses 2 calls). Avoid setting `longPoll` too short.


