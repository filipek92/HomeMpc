#!/usr/bin/env python3

import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
from home_mpc import run_mpc_optimizer
from models import get_electricity_price, get_electricity_load, get_tuv_demand, get_fve_forecast, get_estimate_heating_losses, get_temperature_forecast

HA_URL = "http://hass.lan:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlOWQ2MWJkMzBmNzY0ZDFlYTFlM2JiMGVhYWRlYzIwMyIsImlhdCI6MTc1MTM5NTg2MywiZXhwIjoyMDY2NzU1ODYzfQ.mFrACWhl4AyvEwMrTEipBuScHj5UkABSdN3Vc02rYNM"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def get_ha_states():
    response = requests.get(f"{HA_URL}/api/states", headers=HEADERS)
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

def post_state(entity_id, state):
    data = {"state": str(state)}
    response = requests.post(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, data=json.dumps(data))
    response.raise_for_status()

def main():
    states = get_ha_states()

    fve_raw = get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_today")
    fve_raw.extend(get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_tomorrow"))
    buy_raw = get_electricity_price(states, "sensor.current_buy_electricity_price")
    sell_raw = get_electricity_price(states, "sensor.current_sell_electricity_price")

    print("FVE forecast:")
    for hour, value in fve_raw:
        print(f"  {hour:%d.%m %H:%M}: {value:.2f} kWh")
    print("Buy prices:")
    for hour, price in buy_raw:
        print(f"  {hour:%d.%m %H:%M}: {price:.2f} Kč/kWh")
    print("Sell prices:")
    for hour, price in sell_raw:
        print(f"  {hour:%d.%m %H:%M}: {price:.2f} Kč/kWh")

    hours = [h for h, _ in buy_raw]
    fve = [v for _, v in fve_raw]
    buy = [v for _, v in buy_raw]
    sell = [v for _, v in sell_raw]

    horizon = min(len(fve), len(buy), len(sell))

    print(f"Using horizon: {horizon} hours")

    fve = fve[:horizon]
    buy = buy[:horizon]
    sell = sell[:horizon]
    hours = hours[:horizon]

    outdoor_forecast = get_temperature_forecast(hours)
    outdoor_temps = [temp for _, temp in outdoor_forecast]

    soc_bat = get_entity(states, "sensor.odhadovana_byvajici_kapacita", 11.0)
    soc_boiler = get_entity(states, "sensor.tepelnaakumulace_energie_n_dr_e", 25.0)

    tuv_demand = [get_tuv_demand(h) for h in hours]
    heating_demand = [get_estimate_heating_losses(t) for t in outdoor_temps]
    base_load =  [get_electricity_load(h) for h in hours]

    print("SoC bojleru:", soc_boiler)

    result = run_mpc_optimizer(tuv_demand, heating_demand, fve, buy, sell, base_load, soc_bat, soc_boiler, range(horizon))

    post_state("sensor.mpc_min_soc_battery", result["min_soc_battery"])
    post_state("sensor.mpc_target_temp_top", result["target_temp_top"])
    post_state("sensor.mpc_target_temp_rest", result["target_temp_rest"])
    post_state("switch.mpc_allow_export", "on" if result["allow_grid_export"] else "off")
    post_state("switch.mpc_force_discharge", "on" if result["force_discharge_to_grid_power"] > 0.5 else "off")
    post_state("switch.mpc_allow_heating_from_grid", "on" if result["allow_grid_heating"] else "off")

    # Vizualizace výstupů
    ts = result["time_series"]

    fig, axs = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

    axs[0].plot(hours, ts["B_SOC_percent"], label="SoC baterie")
    axs[0].plot(hours, ts["H_SOC_percent"], label="SoC bojleru")
    axs[0].set_ylabel("Energie [%]")
    axs[0].legend()
    axs[0].grid(True)

    axs[1].step(hours, ts["B_power"], label="Výkon baterie", where='mid')
    axs[1].step(hours, ts["H_store_top"], label="Ohřev horní", where='mid')
    axs[1].step(hours, ts["H_store_bottom"], label="Ohřev dolní", where='mid')
    axs[1].step(hours, ts["G_buy"], label="Nákup ze sítě", where='mid')
    axs[1].step(hours, ts["G_sell"], label="Prodej do sítě", where='mid')
    axs[1].step(hours, ts["H_out"], label="Výstup z bojleru", where='mid')
    axs[1].step(hours, ts["fve"], label="FVE výroba", where='mid')
    axs[1].step(hours, ts["load"], label="Spotřeba", where='mid')
    axs[1].set_ylabel("Výkon [kW]")
    axs[1].legend()
    axs[1].grid(True)

    axs[2].step(hours, ts["buy_price"], label="Cena nákup", where='mid')
    axs[2].step(hours, ts["sell_price"], label="Cena prodej", where='mid')
    axs[2].set_ylabel("kW / Kč")
    axs[2].legend()
    axs[2].grid(True)

    axs[3].plot(hours, ts["heating_demand"], label="Tepelné ztráty")
    axs[3].plot(hours, outdoor_temps, label="Venkovní teplota")
    axs[3].set_xlabel("Hodina")
    axs[3].set_ylabel("kWh / °C")
    axs[3].legend()
    axs[3].grid(True)

    # Zvýraznění událostí
    for idx, t in enumerate(hours):
        if ts["G_sell"][idx] > 0.5:
            axs[1].axvline(t, color='red', linestyle='--', alpha=0.3)
        if ts["G_buy"][idx] > 0.5:
            axs[1].axvline(t, color='green', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

