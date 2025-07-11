#!/bin/bash
echo "Starting PowerStreamPlan optimizer in development mode..."

# Exportuj proměnné pro místní vývoj
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"
# Pro vývoj nepoužíváme HA_ADDON, aby se data ukládala lokálně
# export HA_ADDON="power_stream_plan"
export HA_ADDON_DATA="."

# Spusť aplikaci v development módu
python3 powerplan_server.py
