#!/command/with-contenv bashio
# ==============================================================================
# Comelit ICONA Bridge add-on entrypoint
# ==============================================================================
set -euo pipefail

bashio::log.info "Starting Comelit ICONA Bridge"

export PYTHONPATH="/opt/icona_bridge:${PYTHONPATH:-}"

exec python3 /opt/icona_bridge/main.py
