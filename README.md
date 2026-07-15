# udiNetro
Node server to use Netro Home's irrigation controllers and moisture sensors in the ISY
The node allows basic control of the irrigation system but also gives insight in the operation e.g. allowing monitoring of when system wants to irrigate in teh future (next irrigation)

The node takes a list of device API keys, one per owned device, and creates an instance for each device.  Controllers have subnodes for each zone

On top of this a little trending data for each zone is shown - essentially a slop of the predicted moisture over the last few days

Control parameters are:
SERIALID - list of device API keys, one per device (generated from the Netro website/app)
EVENT_DAYS - The number of days to go back in time to look for events (Negative number)
SCH_DAYS - The number of days to look into the future to find next irrigation event
MOIST_DATS - the number of days to go back to calculate the moisture slope (NEgative number)
TEMP - Temperature unit (C of F)

The polling is as follows:
ShortPoll - sends a heart beat (one per device in list)
LongPoll - polls the latest data from teh sensor (Sensor may be sleeping so data from before it started sleeping)

Note, there is a 2000calls/day limit for each device - so do not longpoll too often (there is typically 4 calls per poll for a controller)

