"""Constants for the companion ICONA bridge camera integration."""

DOMAIN = "comelit_icona_bridge"
MODEL = "6741W"

# Sensible defaults for HA OS + host_network add-on (same machine as Core).
# RTSP via loopback works for the Stream integration; API is probed/discovered.
DEFAULT_RTSP_URL = "rtsp://127.0.0.1:8557/intercom"
DEFAULT_API_URL = "http://homeassistant.local:8099"

CONF_RTSP_URL = "rtsp_url"
CONF_API_URL = "api_url"

# Hosts probed for GET http://<host>:8099/status during config flow.
DISCOVERY_HOSTS = (
    "homeassistant.local",
    "127.0.0.1",
    "localhost",
    "supervisor",
    "homeassistant",
    "hassio",
)

DEFAULT_API_PORT = 8099
DEFAULT_RTSP_PORT = 8557
DEFAULT_RTSP_PATH = "intercom"
