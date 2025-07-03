#!/bin/bash
echo "Starting MPC optimizer..."

# Exportuj proměnné, pokud chceš použít HASSIO_TOKEN
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"

# Spusť aplikaci
python3 mpc_server.py