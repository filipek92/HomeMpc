#!/usr/bin/env python3

import requests
import json
import matplotlib.pyplot as plt
from datetime import timedelta
from home_mpc import run_mpc_optimizer
from models import get_electricity_price, get_electricity_load, get_tuv_demand, get_fve_forecast, get_estimate_heating_losses, get_temperature_forecast

HA_URL = "http://hass.lan:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlOWQ2MWJkMzBmNzY0ZDFlYTFlM2JiMGVhYWRlYzIwMyIsImlhdCI6MTc1MTM5NTg2MywiZXhwIjoyMDY2NzU1ODYzfQ.mFrACWhl4AyvEwMrTEipBuScHj5UkABSdN3Vc02rYNM"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

ha_color = {
    # stavy
    "B_SOC_percent":  "#4db6ac",  # baterie – stejná barva jako battery-out
    "H_SOC_percent":  "#9d770f",  # zásobník tepla – „non-fossil“

    # výkony
    "B_power":        "#4db6ac",  # baterie (- = vybíjení, + = nabíjení)
    "B_in":           "#f06292",  # baterie 
    "B_out":          "#4db6ac",  # baterie 
    "H_store_top":    "#4d2130",  # horní spirála nabíjení zásobníku
    "H_store_bottom": "#750d0d",  # dolní spirála
    "G_buy":          "#488fc2",  # nákup ze sítě
    "G_sell":         "#8353d1",  # prodej do sítě
    "H_out":          "#0f9d58",  # odběr z bojleru (teplo)
    "fve":            "#ff9800",  # FV výroba
    "load":           "#488fc2",  # okamžitá spotřeba (lze nechat stejný odstín jako grid)

    # ceny
    "buy_price":      "#488fc2",
    "sell_price":     "#8353d1",

    # okolí
    "heating_demand": "#0f9d58",
    "mean_temp":  "#ff00aa",
    "outdoor_temps":  "#ff9800",
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
    base =  [get_electricity_load(h) for h in hours]

    print("SoC bojleru:", soc_boiler)

    result = run_mpc_optimizer(tuv_demand, heating_demand, fve, buy, sell, base, soc_bat, soc_boiler, hours)

    post_state("sensor.mpc_min_soc_battery", result["min_soc_battery"])
    post_state("sensor.mpc_target_temp_top", result["target_temp_top"])
    post_state("sensor.mpc_target_temp_rest", result["target_temp_rest"])
    post_state("switch.mpc_allow_export", "on" if result["allow_grid_export"] else "off")
    post_state("switch.mpc_force_discharge", "on" if result["force_discharge_to_grid_power"] > 0.5 else "off")
    post_state("switch.mpc_allow_heating_from_grid", "on" if result["allow_grid_heating"] else "off")

    # Vizualizace výstupů
    ts = result["time_series"]

    ts["B_in"] = [v if v > 0 else 0 for v in ts["B_power"]]
    ts["B_out"] = [v if v < 0 else 0 for v in ts["B_power"]]

    fig, axs = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

    where = 'post'
    h = timedelta(hours=1)

    labels = {
        "B_power": "Výkon baterie",
        "G_buy": "Nákup ze sítě",
        "G_sell": "Prodej do sítě",
        "H_store_top": "Ohřev horní",
        "H_store_bottom": "Ohřev dolní",
        "H_out": "Výstup z bojleru",
        "fve": "FVE výroba",
        "load": "Spotřeba",
        "buy_price": "Cena nákup",
        "sell_price": "Cena prodej",
        "heating_demand": "Tepelné ztráty",
        "outdoor_temps": "Venkovní teplota",
        "B_SOC_percent": "SoC baterie",
        "H_SOC_percent": "SoC bojleru",
    }

    SOCs = ["B_SOC_percent", "H_SOC_percent"]
    inverted = ["G_sell", "H_out", "G_sell"]
    steps = ["H_store_top", "H_store_bottom", "H_out", "fve", "load"]
    bars = ["B_in", "B_out", "G_sell", "G_buy"]

    # 1) stavy
    for key in SOCs:
        axs[0].plot([t+h for t in hours], ts[key], label=labels.get(key, key), color=ha_color.get(key, "black"))
    axs[0].set_ylabel("Energie [%]")
    axs[0].legend()
    axs[0].grid(True)

    bars_cnt = len(bars)
    width = 0.04/bars_cnt # šířka sloupců pro barové grafy

    # 2) výkony
    for key in steps:
        axs[1].step(
            hours,
            [-v for v in ts[key]] if key in inverted else ts[key], 
            label=labels.get(key, key),
            where=where,
            color=ha_color.get(key, "black")
        )
    for i, key in enumerate(bars):
        axs[1].bar(
            [t + (i*h/bars_cnt) for t in hours],
            [-v for v in ts[key]] if key in inverted else ts[key],
            width=width,
            align="edge",
            color=ha_color.get(key, "black"),
            label=labels.get(key, key),
            alpha=0.8,          # lehká průhlednost, aby šly vidět mřížky i překryvy
        )

    axs[1].set_ylabel("Výkon [kW]")
    axs[1].legend()
    axs[1].grid(True)

    # 3) ceny
    axs[2].step(hours, ts["buy_price"],  label="Cena nákup", where=where, color=ha_color["buy_price"])
    axs[2].step(hours, ts["sell_price"], label="Cena prodej", where=where, color=ha_color["sell_price"])
    axs[2].set_ylabel("kW / Kč")
    axs[2].legend()
    axs[2].grid(True)

    # 4) teplo a venkovní teplota
    axs[3].plot(hours, ts["heating_demand"], label="Tepelné ztráty", color=ha_color["heating_demand"])
    axs[3].plot(hours, outdoor_temps, label="Venkovní teplota", color=ha_color["outdoor_temps"])
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

