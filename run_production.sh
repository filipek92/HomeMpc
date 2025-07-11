#!/bin/bash
echo "Starting PowerStreamPlan optimizer with Gunicorn (Production/Docker)..."

# Exportuj proměnné pro Home Assistant
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"
export HA_ADDON="power_stream_plan"
export HA_ADDON_DATA="/data"

# Spusť aplikaci pomocí Gunicorn
gunicorn --config gunicorn.conf.py powerplan_server:app
