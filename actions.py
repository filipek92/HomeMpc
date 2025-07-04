#!/usr/bin/env python3
"""
mpc_to_actions.py
-----------------
Převádí výstupy z `run_mpc_optimizer` na konkrétní akce pro Home Assistant.

Klíče ve výstupu:
• charger_use_mode      → pro select.solax_charger_use_mode
• acumulation_on        → bool, switch.acumulation_enable
• max_heat_on           → bool, switch.max_heat
• battery_power         → W, záporné = vybíjení
• battery_discharge_current → A, kladné
• battery_target        → cílové SOC (%)
"""

from datetime import datetime
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Parametry systému
# ---------------------------------------------------------------------------
DC_BUS_V = 360
BATTERY_POWER_MAX = 9000  # W

# Heuristiky
P_MAN_DIS   = 0.10
P_EXTRA_EXP = 0.10
P_GBUY_GRID = 8.0
P_HIN_GRID  = 11.0

# ---------------------------------------------------------------------------
def mpc_to_actions(sol: Dict[str, Any]) -> Dict[str, Any]:
    out   = sol["outputs"]
    Hin   = out["H_in"][0]
    Gsell = out["G_sell"][0]
    Gbuy  = out["G_buy"][0]
    Bdis  = out["B_discharge"][0]
    Bchrg = out["B_charge"][0]
    B_SOC = out["B_SOC_percent"][0]

    fve   = sol["inputs"]["fve_pred"][0]
    load  = sol["inputs"]["load_pred"][0]

    # Režim měniče → select
    feed_in_pv   = max(0.0, fve - load)
    extra_export = Gsell - feed_in_pv

    if Bdis > P_MAN_DIS and extra_export > P_EXTRA_EXP:
        charger_use_mode = "Manual Mode"
    elif Gsell > 0.1:
        charger_use_mode = "Feedin Priority"
    else:
        charger_use_mode = "Back Up Mode"

    # Režim ohřevu → přepínače
    if Hin > P_HIN_GRID and Gbuy > P_GBUY_GRID:
        acumulation_on = False
        max_heat_on = True
    elif Hin > 0.1:
        acumulation_on = True
        max_heat_on = False
    else:
        acumulation_on = False
        max_heat_on = False

    # Zbývající čas slotu
    curr_slot = sol["times"][0]
    next_slot = sol["times"][1]
    remaining_slot_part = (
        datetime.fromisoformat(next_slot).astimezone()
        - datetime.now().astimezone()
    ).total_seconds() / 3600.0
    remaining_slot_part = max(0.0, round(remaining_slot_part, 2))

    # Výkon/proud baterie
    raw_pwr_w = -int(Bdis * 1000) if charger_use_mode == "Manual Discharge" else 0
    scaled_pwr_w = raw_pwr_w / remaining_slot_part if remaining_slot_part > 0.01 else 0
    battery_power = max(scaled_pwr_w, -BATTERY_POWER_MAX)
    battery_current = round(-battery_power / DC_BUS_V, 2)

    return [{
            "charger_use_mode":        charger_use_mode,
            "acumulation_on":          acumulation_on,
            "max_heat_on":             max_heat_on,
            "battery_power":           battery_power,
            "battery_discharge_current": battery_current,
            "battery_target":          B_SOC,
        },
        {
            "heater_power": out["H_in"][0],
            "grid_export": out["G_sell"][0],
            "grid_import": out["G_buy"][0],
            "battery_charge": out["B_charge"][0],
            "battery_discharge": out["B_discharge"][0],
            "tuv_soc_target_pct": out.get("H_SOC_percent", [None])[0],
            "load_forecast": sol["inputs"]["load_pred"][0],
            "tuv_demand": sol["inputs"]["tuv_demand"][0],
            "heating_demand": sol["inputs"]["heating_demand"][0],
        }]

ACTION_ATTRIBUTES: dict[str, dict[str, str]] = {
    "charger_use_mode": {
        "friendly_name": "Režim měniče",
        "icon": "mdi:transmission-tower-export",
    },
    "acumulation_on": {
        "friendly_name": "Akumulace TUV povolena",
        "device_class": "switch",
        "icon": "mdi:water-pump",
    },
    "max_heat_on": {
        "friendly_name": "Maximální ohřev povolen",
        "device_class": "switch",
        "icon": "mdi:fire",
    },
    "battery_power": {
        "friendly_name": "Výkon baterie",
        "unit_of_measurement": "W",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-charging-high",
    },
    "battery_discharge_current": {
        "friendly_name": "Vybíjecí proud baterie",
        "unit_of_measurement": "A",
        "device_class": "current",
        "state_class": "measurement",
        "icon": "mdi:current-dc",
    },
    "battery_target": {
        "friendly_name": "Cílové nabití baterie",
        "unit_of_measurement": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery",
    }
}