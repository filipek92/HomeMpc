#!/usr/bin/env python3
"""
mpc_to_actions.py
-----------------
Převádí výstupy z `run_mpc_optimizer` na jednoznačné pokyny pro Home Assistant.
Vrací slovník hodnot, který pak můžeš publikovat jako REST senzory.

• Bojler          → sensor.mpc_heater_mode
• Režim měniče    → sensor.mpc_inverter_mode
• Výkon baterie   → sensor.mpc_battery_power  (W, záporný = vybíjení)
• Proud baterie   → sensor.mpc_battery_discharge_current (A)
• Další debugové a pomocné položky viz návratová hodnota.
"""

from datetime import datetime
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Konfigurovatelné konstanty
# ---------------------------------------------------------------------------
DC_BUS_V = 360               # [V] napětí (pro převod W → A)
BATTERY_POWER_MAX = 9000     # [W] max. (absolutní) vybíjecí výkon baterie

# Prahové hodnoty [kW] pro heuristiku
P_MAN_DIS   = 0.10           # minimální vybíjení baterie, aby se bralo vážně
P_EXTRA_EXP = 0.10           # minimální export navíc nad čistý přebytek FV
P_GBUY_GRID = 8.0            # min. nákup ze sítě ⇒ 'grid_max'
P_HIN_GRID  = 11.0           # výkon spirály indikující síťový ohřev

# ---------------------------------------------------------------------------
def mpc_to_actions(sol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Params
    ------
    sol : dict
        Kompletní výstup z run_mpc_optimizer (obsahuje 'outputs', 'inputs', 'times').

    Returns
    -------
    dict
        Klíč-hodnota pár pro publikaci do HA.
    """
    # --- Výstupy (aktuální slot = index 0) ---------------------------------
    out   = sol["outputs"]
    Hin   = out["H_in"][0]            # kW topný příkon
    Gsell = out["G_sell"][0]          # kW export do sítě
    Gbuy  = out["G_buy"][0]           # kW nákup ze sítě
    Bdis  = out["B_discharge"][0]     # kW vybíjení (kladné)
    Bchrg = out["B_charge"][0]        # kW nabíjení
    B_SOC = out["B_SOC_percent"][0]   # % SOC baterie

    # --- Vstupy (FV a zátěž) ----------------------------------------------
    fve   = sol["inputs"]["fve_pred"][0]   # kW FV výkon
    load  = sol["inputs"]["load_pred"][0]  # kW domácí zatížení

    # ----------------------------------------------------------------------
    # Heuristika pro bojler
    # ----------------------------------------------------------------------
    if Hin > P_HIN_GRID and Gbuy > P_GBUY_GRID:
        heater = "grid_max"
    elif Hin > 0.1:
        heater = "accum"
    else:
        heater = "off"

    # ----------------------------------------------------------------------
    # Heuristika pro režim měniče
    # ----------------------------------------------------------------------
    feed_in_pv   = max(0.0, fve - load)      # přebytek FV, pokud baterie = 0
    extra_export = Gsell - feed_in_pv        # export navíc (jde z baterie)

    if Bdis > P_MAN_DIS and extra_export > P_EXTRA_EXP:
        inv_mode = "manual_discharge"        # aktivní prodej z bat.
    elif Gsell > 0.1:
        inv_mode = "feed_in_priority"        # prodávají jen FV přebytky
    elif Bdis < 0.01 and Bchrg < 0.01:
        inv_mode = "no_use"                  # baterie se neúčastní
    else:
        inv_mode = "backup"                  # ukládej přebytky, neprodávej

    # ----------------------------------------------------------------------
    # Výpočet zbytku slotu (minulý vs. aktuální čas)
    # ----------------------------------------------------------------------
    curr_slot = sol["times"][0]
    next_slot = sol["times"][1]

    remaining_slot_part = (
        datetime.fromisoformat(next_slot).astimezone()
        - datetime.now().astimezone()
    ).total_seconds() / 3600.0  # → hodiny
    remaining_slot_part = max(0.0, round(remaining_slot_part, 2))

    # ----------------------------------------------------------------------
    # Přepočet výkonu baterie (W) a proudu (A) pro RC
    # ----------------------------------------------------------------------
    raw_pwr_w = -int(Bdis * 1000) if inv_mode == "manual_discharge" else 0

    # Kompenzace, pokud slot doběhne jen částečně
    scaled_pwr_w = (
        raw_pwr_w / remaining_slot_part if remaining_slot_part > 0.01 else 0
    )

    # Omez výkon na fyzikální maximum baterie
    battery_power = max(scaled_pwr_w, -BATTERY_POWER_MAX)  # záporné = discharge
    battery_current = round(-battery_power / DC_BUS_V, 2)  # A, kladné

    # ----------------------------------------------------------------------
    # Sestav návratový slovník
    # ----------------------------------------------------------------------
    return {
        "remaining_slot_part":       remaining_slot_part,    # h
        "heater_mode":               heater,                 # grid_max | accum | off
        "inverter_mode":             inv_mode,               # manual_discharge | feed_in_priority | backup | no_use
        "battery_power":             battery_power,          # W (záporné = vybíjení)
        "battery_discharge_current": battery_current,        # A (kladné)
        "active_slot":               curr_slot,              # ISO timestamp
        "battery_target":            B_SOC,                  # % aktuální SOC
        "comment": (f"H_in={Hin:.1f} G_sell={Gsell:.1f} "
                    f"FVE={fve:.1f} load={load:.1f} "
                    f"B_dis={Bdis:.2f} B_chg={Bchrg:.2f} "
                    f"⇒ {inv_mode}"),
    }
