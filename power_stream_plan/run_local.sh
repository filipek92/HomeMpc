#!/bin/bash
echo "Starting PowerStreamPlan optimizer with Gunicorn (Local Testing)..."

# Exportuj proměnné pro místní testování
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"
# Pro testování místně nepoužíváme HA_ADDON, aby se data ukládala lokálně
# export HA_ADDON="power_stream_plan"
export HA_ADDON_DATA="./data"

# Spusť aplikaci pomocí Gunicorn
gunicorn --config gunicorn.conf.py powerplan_server:app
