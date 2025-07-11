#!/bin/bash
echo "Starting PowerStreamPlan optimizer with Gunicorn..."

# Exportuj proměnné pro Home Assistant addon
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"
export HA_ADDON="power_stream_plan"
export HA_ADDON_DATA="/data"

# Spusť aplikaci pomocí Gunicorn
gunicorn --config gunicorn.conf.py powerplan_server:app