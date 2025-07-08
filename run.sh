#!/bin/bash
echo "Starting MPC optimizer..."

# Exportuj proměnné, pokud chceš použít HASSIO_TOKEN
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"
export HA_ADDON="mpc_optimizer"
export HA_ADDON_DATA="/data"


# Spusť migraci klíčů (jen pokud ještě neproběhla)
python3 migrate_keys.py

# Spusť aplikaci
python3 mpc_server.py