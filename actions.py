#!/usr/bin/env python3
"""
actions.py
----------
Převádí výstupy z `run_mpc_optimizer` na konkrétní akce pro Home Assistant.

ZMĚNY v mapování entit:
• charger_use_mode           → select.solax_charger_use_mode
• upper_accumulation_on      → switch.tepelnaakumulace_povolen_horn_akumulace
• lower_accumulation_on      → switch.tepelnaakumulace_povolen_spodn_akumulace  
• max_heat_on               → switch.tepelnaakumulace_maxim_ln_oh_ev_ze_s_t
• forced_heating_block      → switch.tepelnaakumulace_blokov_n_nucen_ho_oh_evu
• battery_discharge_power   → number.tepelnaakumulace_povolen_vyb_jec_v_kon_baterie
• battery_target_soc        → number.tepelnaakumulace_po_adovan_stav_nabit_baterie
• reserve_power_charging    → number.tepelnaakumulace_rezervovan_v_kon_pro_dob_jen_baterie
• minimum_battery_soc       → number.tepelnaakumulace_minim_ln_stav_nabit_baterie

LOGIKA:
- Pokud je baterie nad 40%, systém se snaží využít FVE přebytek pro ohřev
- Horní a spodní akumulace se ovládají samostatně podle velikosti přebytku
- Maximální ohřev (12kW) se zapíná pouze při velkém přebytku nebo levné elektřině
- Blokování nuceného ohřevu chrání při nedostatku energie
"""

from datetime import datetime
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Parametry systému
# ---------------------------------------------------------------------------
DC_BUS_V = 360
BATTERY_POWER_MAX = 9000  # W
MIN_SOC_RESERVE = 40     # % - minimální rezerva baterie
MAX_HEAT_POWER = 12000   # W - maximální výkon ohřevu

# Heuristiky
P_MAN_DIS   = 0.10       # kW - práh pro Manual Discharge
P_EXTRA_EXP = 0.10       # kW - práh pro extra export
P_GBUY_GRID = 8.0        # kW - práh pro nákup ze sítě
P_HIN_GRID  = 11.0       # kW - práh pro ohřev ze sítě
FVE_SURPLUS_THRESHOLD = 2.0  # kW - přebytek FVE pro akumulaci

# ---------------------------------------------------------------------------
def mpc_to_actions(sol: Dict[str, Any]) -> Dict[str, Any]:
    out   = sol["outputs"]  # outputs now use lower_snake_case keys
    Hin_upper = out["h_in_upper"][0]
    Hin_lower = out["h_in_lower"][0]
    Hin_total = Hin_upper + Hin_lower
    Gsell = out["g_sell"][0]
    Gbuy  = out["g_buy"][0]
    Bdis  = out["b_discharge"][0]
    Bchrg = out["b_charge"][0]
    B_SOC = out["b_soc_percent"][0]

    fve   = sol["inputs"]["fve_pred"][0]
    load  = sol["inputs"]["load_pred"][0]

    # Výpočet přebytku FVE
    fve_surplus = max(0.0, fve - load)
    
    # Režim měniče → select.solax_charger_use_mode
    if B_SOC >= 100:
        # Plná baterie - záloha
        charger_use_mode = "Back Up Mode"
    elif Bdis > P_MAN_DIS:
        # Potřebujeme vybíjet baterii manuálně
        charger_use_mode = "Manual Discharge"
    elif Bchrg > P_MAN_DIS and fve_surplus < 1.0:
        # Nabíjíme ze sítě
        charger_use_mode = "Manual Charge" 
    elif Gsell > 0.1 or fve_surplus > 1.0:
        # Máme přebytek energie pro export
        charger_use_mode = "Feedin Priority"
    elif B_SOC < MIN_SOC_RESERVE:
        # Nízká baterie - záloha s nabíjením
        charger_use_mode = "Back Up Mode"
    else:
        # Standardní záložní režim
        charger_use_mode = "Back Up Mode"

    # Logika ohřevu na základě dostupné energie a cen
    heating_decisions = enhanced_heating_logic(
        fve_surplus, B_SOC, Hin_upper, Hin_lower, Gbuy
    )
    
    upper_accumulation_on = heating_decisions["upper_accumulation"]
    lower_accumulation_on = heating_decisions["lower_accumulation"] 
    max_heat_on = heating_decisions["max_heat"]
    forced_heating_block = heating_decisions["block_heating"]

    # Výpočet výkonů a proudů baterie
    if charger_use_mode in ["Manual Discharge", "Manual Charge"]:
        # V manuálním režimu nastavujeme konkrétní výkon
        battery_power_w = -int(Bdis * 1000) if Bdis > 0 else int(Bchrg * 1000)
        battery_discharge_power = max(0, int(Bdis * 1000))
    else:
        battery_power_w = 0
        battery_discharge_power = 0
    
    # Rezervovaný výkon pro dobíjení baterie
    reserve_power_charging = max(0, int(Bchrg * 1000)) if B_SOC < 90 else 0
    
    # Minimální SOC podle situace
    minimum_battery_soc = MIN_SOC_RESERVE if max_heat_on else max(MIN_SOC_RESERVE - 10, 20)

    return {
        "charger_use_mode":        charger_use_mode,
        "upper_accumulation_on":   upper_accumulation_on,
        "lower_accumulation_on":   lower_accumulation_on,
        "max_heat_on":             max_heat_on,
        "forced_heating_block":    forced_heating_block,
        "battery_discharge_power": battery_discharge_power,
        "battery_target_soc":      round(B_SOC, 1),
        "reserve_power_charging":  reserve_power_charging,
        "minimum_battery_soc":     minimum_battery_soc,
        # Zachováváme pro kompatibilitu
        "acumulation_on":          upper_accumulation_on or lower_accumulation_on,
        "battery_power":           battery_power_w,
        "battery_discharge_current": round(-battery_power_w / DC_BUS_V, 2),
    }

ACTION_ATTRIBUTES: dict[str, dict[str, str]] = {
    "charger_use_mode": {
        "friendly_name": "Režim měniče",
        "icon": "mdi:transmission-tower-export",
    },
    "upper_accumulation_on": {
        "friendly_name": "Horní akumulace povolena", 
        "device_class": "switch",
        "icon": "mdi:water-pump",
    },
    "lower_accumulation_on": {
        "friendly_name": "Spodní akumulace povolena",
        "device_class": "switch", 
        "icon": "mdi:water-pump",
    },
    "max_heat_on": {
        "friendly_name": "Maximální ohřev povolen",
        "device_class": "switch",
        "icon": "mdi:fire",
    },
    "forced_heating_block": {
        "friendly_name": "Blokování nuceného ohřevu",
        "device_class": "switch",
        "icon": "mdi:block-helper",
    },
    "battery_discharge_power": {
        "friendly_name": "Povolený vybíjecí výkon baterie",
        "unit_of_measurement": "W",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-arrow-down",
    },
    "battery_target_soc": {
        "friendly_name": "Požadovaný stav nabití baterie",
        "unit_of_measurement": "%",
        "device_class": "battery",
        "state_class": "measurement", 
        "icon": "mdi:battery",
    },
    "reserve_power_charging": {
        "friendly_name": "Rezervovaný výkon pro nabíjení",
        "unit_of_measurement": "W",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-arrow-up",
    },
    "minimum_battery_soc": {
        "friendly_name": "Minimální stav nabití baterie",
        "unit_of_measurement": "%", 
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery-low",
    },
    # Zachováváme pro kompatibilitu
    "acumulation_on": {
        "friendly_name": "Akumulace TUV povolena",
        "device_class": "switch",
        "icon": "mdi:water-pump",
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
}

# ---------------------------------------------------------------------------
def enhanced_heating_logic(fve_surplus: float, B_SOC: float, Hin_upper: float, 
                          Hin_lower: float, Gbuy: float) -> Dict[str, bool]:
    """
    Vylepšená logika ohřevu podle požadavků:
    - Pokud je baterie nad 40%, snaží se vytěžit FVE do ohřevu
    - Zapíná patrony podle povolení horní a spodní akumulace
    - Při zapnutí maximálního výkonu spustí 12kW ohřev
    """
    
    # Základní podmínky
    battery_above_40 = B_SOC > 40
    cheap_electricity = Gbuy < P_GBUY_GRID
    expensive_electricity = Gbuy > P_HIN_GRID
    
    # Horní akumulace - konzervativnější
    upper_on = (
        # FVE přebytek + dobrá baterie
        (fve_surplus > FVE_SURPLUS_THRESHOLD and battery_above_40) or
        # Levná elektřina + signál z optimizátoru  
        (cheap_electricity and Hin_upper > 0.1) or
        # Velký přebytek FVE
        (fve_surplus > 5.0)
    )
    
    # Spodní akumulace - agresivnější využití přebytku
    lower_on = (
        # Jakýkoliv FVE přebytek + baterie nad 40%
        (fve_surplus > 1.0 and battery_above_40) or
        # Levná elektřina + signál
        (cheap_electricity and Hin_lower > 0.1) or
        # Střední přebytek FVE
        (fve_surplus > 3.0)
    )
    
    # Maximální ohřev - pouze při výjimečných podmínkách
    max_heat_on = (
        # Velký FVE přebytek + dobrá baterie
        (fve_surplus > 8.0 and battery_above_40) or
        # Velmi levná elektřina + vysoký signál
        (expensive_electricity and (Hin_upper + Hin_lower) > P_HIN_GRID)
    )
    
    # Blokování nuceného ohřevu - ochrana při nedostatku
    block_heating = (
        # Málo energie + slabá baterie + drahá elektřina
        (fve_surplus < 0.5 and B_SOC < 30 and expensive_electricity) or
        # Velmi slabá baterie
        (B_SOC < 20)
    )
    
    return {
        "upper_accumulation": upper_on,
        "lower_accumulation": lower_on, 
        "max_heat": max_heat_on,
        "block_heating": block_heating
    }

# ---------------------------------------------------------------------------