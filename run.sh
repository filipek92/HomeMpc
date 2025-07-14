#!/bin/bash

# Exportuj společné proměnné
export HASSIO_TOKEN=$HASSIO_TOKEN
export HA_URL="http://homeassistant:8123"

case "$1" in
    "dev")
        echo "Starting PowerStreamPlan optimizer in development mode..."

        # Pro vývoj nepoužíváme HA_ADDON, aby se data ukládala lokálně
        # export HA_ADDON="power_stream_plan"
        export HA_ADDON_DATA="./data"

        # Spusť aplikaci v development módu
        python3 powerplan_server.py
        ;;

    "local")
        #!/bin/bash
        echo "Starting PowerStreamPlan optimizer with Gunicorn (Local Testing)..."

        # Exportuj proměnné pro místní testování
        # Pro testování místně nepoužíváme HA_ADDON, aby se data ukládala lokálně
        # export HA_ADDON="power_stream_plan"
        export HA_ADDON_DATA="./data"

        # Spusť aplikaci pomocí Gunicorn
        gunicorn --config gunicorn.conf.py powerplan_server:app
        ;;
    *)
        echo "Starting PowerStreamPlan optimizer with Gunicorn..."

        # Exportuj proměnné pro Home Assistant addon
        export HA_ADDON="power_stream_plan"
        export HA_ADDON_DATA="/data"

        # Spusť aplikaci pomocí Gunicorn
        gunicorn --config gunicorn.conf.py powerplan_server:app
        ;;
esac

