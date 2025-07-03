import yaml
import requests
from models import (
    get_electricity_price,
    get_electricity_load,
    get_tuv_demand,
    get_fve_forecast,
    get_estimate_heating_losses,
    get_temperature_forecast,
)


HA_URL = "http://homeassistant.local:8123"
TOKEN = "your_long_lived_access_token_here"

CREDENTIALS_FILE = "credentials.yaml"

try:
    with open(CREDENTIALS_FILE, "r") as f:
        credentials = yaml.safe_load(f)
        HA_URL = credentials["url"]
        TOKEN = credentials["token"]
except (FileNotFoundError, yaml.YAMLError, ValueError, KeyError) as e:
    print(f"Error reading {CREDENTIALS_FILE}:", e)
    with open(CREDENTIALS_FILE, "w") as f:
        yaml.dump({"url": HA_URL, "token": TOKEN}, f)
        print(f"Created {CREDENTIALS_FILE} with default values. Please update it.")
        exit(1)


HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# --- Pomocné funkce -------------------------------------------------------

def get_ha_states():
    response = requests.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()

def get_entity(state_list, entity_id, default=0.0):
    for e in state_list:
        if e["entity_id"] == entity_id:
            try:
                return float(e["state"])
            except ValueError:
                return default
    return default

def prepare_data():
    states = get_ha_states()

    # --- předpovědi a ceny -------------------------------------------------
    fve_raw = get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_today")
    fve_raw.extend(
        get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_tomorrow")
    )
    buy_raw = get_electricity_price(states, "sensor.current_buy_electricity_price")
    sell_raw = get_electricity_price(states, "sensor.current_sell_electricity_price")

    hours = [h for h, _ in buy_raw]
    horizon = len(hours)

    fve_pred = [v for _, v in fve_raw][:horizon]
    buy_price = [v for _, v in buy_raw][:horizon]
    sell_price = [v for _, v in sell_raw][:horizon]

    outdoor_forecast = get_temperature_forecast(hours)
    outdoor_temps = [temp for _, temp in outdoor_forecast]

    soc_bat = get_entity(states, "sensor.odhadovana_byvajici_kapacita", 11.0)
    soc_boiler = get_entity(states, "sensor.tepelnaakumulace_energie_n_dr_e", 25.0)

    tuv_demand = [get_tuv_demand(h) for h in hours]
    heating_demand = [get_estimate_heating_losses(t) for t in outdoor_temps]
    lod_pred = [get_electricity_load(h) for h in hours]

    return {
        "hours": hours,
        "tuv_demand": tuv_demand,
        "heating_demand": heating_demand,
        "fve_pred": fve_pred,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "load_pred": lod_pred,
        "soc_bat": soc_bat,
        "soc_boiler": soc_boiler,
        "outdoor_temps": outdoor_temps,
    }