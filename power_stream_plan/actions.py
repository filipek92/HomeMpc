#!/usr/bin/env python3
"""
actions.py
----------
Převádí výstupy z `run_mpc_optimizer` na konkrétní akce pro Home Assistant.

ZMĚNY v mapování entit:
• charger_use_mode           → select.solax_charger_use_mode (jednotné výstupy pro všechny režimy)
• upper_accumulation_on      → switch.tepelnaakumulace_povolen_horn_akumulace
• lower_accumulation_on      → switch.tepelnaakumulace_povolen_spodn_akumulace  
• max_heat_on               → switch.tepelnaakumulace_maxim_ln_oh_ev_ze_s_t
• forced_heating_block      → switch.tepelnaakumulace_blokov_n_nucen_ho_oh_evu
• comfort_heating_grid      → switch.tepelnaakumulace_povolen_komfortn_ho_oh_evu (NOVÉ)

LOGIKA:
- Využívá oficiální režimy X3 G4: Feedin Priority, Back Up Mode, Manual Mode
- Manual Charge → Manual Mode + Force Charge
- Manual Discharge → Manual Mode + Force Discharge  
- Manual Idle → Manual Mode + Stop Charge and Discharge (jen při specifických podmínkách)
  * Používá se pouze když: nákup ze sítě (>0.2kW) a nízký výkon FVE (<0.6kW)
  * Zamezuje zbytečnému vybíjení baterie při nedostatku FVE a nákupu ze sítě
- Feedin Priority pro optimalizaci prodeje přebytků
- Back Up Mode: optimalizuje vlastní spotřebu + záložní napájení (standardní režim)
- Konfigurovatelný preferovaný standardní režim (PREFERRED_STANDARD_MODE)
- Automatické režimy využívají inteligenci střídače pro 0W na elektroměru

LOGIKA OHŘEVU AKUMULACE:
- Respektuje automatické režimy akumulace (pokud nejsou blokovány):
  * Udržuje alespoň 45°C nahoře pro základní komfort
  * Po 16h připravuje 65°C nahoře pro koupání (55°C pokud je dole teplo)
  * Při FVE přebytku: nejdříve nahoře na 70°C, pak celou nádrž na 90°C
- Horní a spodní akumulace se ovládají podle MPC signálů a aktuálních teplot
- Maximální ohřev (12kW) se zapíná při velkém přebytku pro celou nádrž
- Blokování nuceného ohřevu pouze v kritických situacích (zachovává komfort)
- NOVÉ: Komfortní ohřev ze sítě (comfort_heating_grid):
  * Povoluje ohřev horní části nádrže na 65°C i ze sítě (bez FVE)
  * Aktivuje se při teplotě pod komfort, před koupáním, nebo MPC signálu
  * Připojuje se na switch.tepelnaakumulace_povolen_komfortn_ho_oh_evu
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

# Konfigurace režimů střídače
# Dostupné režimy: "Feedin Priority", "Back Up Mode", "Manual Mode"
# "Back Up Mode" - optimalizuje vlastní spotřebu + záložní napájení  
# "Feedin Priority" - priorita prodeje přebytků do sítě
# "Manual Mode" - ruční řízení nabíjení/vybíjení
PREFERRED_STANDARD_MODE = "Back Up Mode"

# Heuristiky
P_MAN_DIS   = 3.5        # kW - práh pro Manual režim (reálný minimální výkon)
P_EXTRA_EXP = 0.10       # kW - práh pro extra export
P_GBUY_GRID = 8.0        # kW - práh pro nákup ze sítě
P_HIN_GRID  = 11.0       # kW - práh pro ohřev ze sítě
FVE_SURPLUS_THRESHOLD = 2.0  # kW - přebytek FVE pro akumulaci

# Teplotní limity pro akumulaci
TEMP_COMFORT_MIN = 45    # °C - minimální teplota nahoře pro komfort
TEMP_BATH_TARGET = 65    # °C - cílová teplota nahoře po 18h pro koupání  
TEMP_BATH_REDUCED = 55   # °C - snížená teplota když je dole teplo
TEMP_ACCUMULATION = 70   # °C - teplota nahoře při FVE přebytku
TEMP_FULL_TANK = 90      # °C - cílová teplota celé nádrže
TEMP_LOWER_WARM = 50     # °C - práh "teplá spodní zóna"

# ---------------------------------------------------------------------------
def powerplan_to_actions(sol: Dict[str, Any], slot_index: int = 0) -> Dict[str, Any]:
    """
    Převádí výstupy z optimizátoru na konkrétní akce pro daný slot.
    
    Args:
        sol: Slovník s výstupy Powerplan optimizátoru
        slot_index: Index slotu (0 = aktuální/první slot)
    """
    out = sol["outputs"]  # outputs now use lower_snake_case keys
    inp = sol.get("inputs", {})  # inputs contain predictions
    Hin_upper = out["h_in_upper"][slot_index]
    Hin_lower = out["h_in_lower"][slot_index]
    Hin_total = Hin_upper + Hin_lower
    Gsell = out["g_sell"][slot_index]
    Gbuy = out["g_buy"][slot_index]
    Bdis = out["b_discharge"][slot_index]
    Bchrg = out["b_charge"][slot_index]
    B_SOC = out["b_soc_percent"][slot_index]

    # Současné teploty nádrže z MPC
    temp_upper_current = out["temp_upper"][slot_index]  # °C
    temp_lower_current = out["temp_lower"][slot_index]  # °C

    # Výpočet FVE přebytku
    fve_output = inp.get("fve_pred", [])[slot_index] if slot_index < len(inp.get("fve_pred", [])) else 0
    load_demand = inp.get("load_pred", [])[slot_index] if slot_index < len(inp.get("load_pred", [])) else 0
    fve_surplus = max(0, fve_output - load_demand)

    # Vylepšená logika ohřevu pro aktuální slot
    heating = enhanced_heating_logic(
        fve_surplus, B_SOC, Hin_upper, Hin_lower, Gbuy,
        temp_upper_current, temp_lower_current
    )
    
    upper_accumulation_on = heating["upper_accumulation"]
    lower_accumulation_on = heating["lower_accumulation"] 
    max_heat_on = heating["max_heat"]
    forced_heating_block = heating["block_heating"]
    comfort_heating_grid = heating["comfort_heating_grid"]

    # Režim střídače
    if Bdis > P_MAN_DIS:
        charger_use_mode = "Manual Discharge"
    elif Bchrg > P_MAN_DIS:
        charger_use_mode = "Manual Charge"
    elif (abs(Bdis) < 0.1 and abs(Bchrg) < 0.1 and 
          Gbuy > 0.2 and fve_output < 0.6):
        # Manual Idle pouze při specifických podmínkách:
        # - žádné nabíjení/vybíjení baterie
        # - nákup ze sítě (Gbuy > 0.2 kW)
        # - nízký výkon FVE (< 0.6 kW)
        # Zamezuje vybíjení baterie při nedostatku FVE a nákupu ze sítě
        charger_use_mode = "Manual Idle"
    elif Gsell > P_EXTRA_EXP:
        charger_use_mode = "Feedin Priority"
    else:
        charger_use_mode = PREFERRED_STANDARD_MODE

    # Výpočet výkonů a proudů baterie
    if charger_use_mode in ["Manual Charge", "Manual Discharge", "Manual Idle"]:
        # Manual režim - explicitní řízení
        if Bdis > P_MAN_DIS:
            # Vybíjení
            battery_power_w = -int(Bdis * 1000)
            battery_discharge_power = max(0, int(Bdis * 1000))
        elif Bchrg > P_MAN_DIS:
            # Nabíjení
            battery_power_w = int(Bchrg * 1000)
            battery_discharge_power = 0
        else:
            # Idle - baterie se nepoužívá
            battery_power_w = 0
            battery_discharge_power = 0
    else:
        # Automatické režimy (Feedin Priority, Back Up Mode) - střídač řídí sám
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
        "comfort_heating_grid":    comfort_heating_grid,
        "battery_discharge_power": battery_discharge_power,
        "battery_target_soc":      round(B_SOC, 1),
        "reserve_power_charging":  reserve_power_charging,
        "minimum_battery_soc":     minimum_battery_soc,
    }

ACTION_ATTRIBUTES: dict[str, dict[str, str]] = {
    "charger_use_mode": {
        "friendly_name": "Režim měniče (Feedin Priority/Back Up Mode/Manual Charge/Manual Discharge/Manual Idle)",
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
    "comfort_heating_grid": {
        "friendly_name": "Komfortní ohřev ze sítě povolen",
        "device_class": "switch",
        "icon": "mdi:water-thermometer",
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
}

# ---------------------------------------------------------------------------
def enhanced_heating_logic(fve_surplus: float, B_SOC: float, Hin_upper: float, 
                          Hin_lower: float, Gbuy: float, temp_upper: float, 
                          temp_lower: float) -> Dict[str, bool]:
    """
    Vylepšená logika ohřevu podle aktuálních teplot a požadavků:
    
    Automatické režimy akumulace (pokud nejsou blokovány):
    - Udržuje alespoň 45°C nahoře pro komfort
    - Po 18h cílí na 65°C nahoře pro koupání (55°C pokud je dole teplo)
    - Při FVE přebytku: nejdříve nahoře na 70°C, pak celá nádrž na 90°C
    
    MPC optimalizátor by měl toto chování řídit podle budoucích podmínek.
    """
    from datetime import datetime
    
    # Základní podmínky
    battery_above_40 = B_SOC > 40
    cheap_electricity = Gbuy < P_GBUY_GRID
    expensive_electricity = Gbuy > P_HIN_GRID
    current_hour = datetime.now().hour
    is_evening_prep = current_hour >= 16  # Příprava na večerní koupání
    lower_is_warm = temp_lower > TEMP_LOWER_WARM
    
    # Kontrola základních komfortních teplot
    upper_needs_comfort = temp_upper < TEMP_COMFORT_MIN
    upper_needs_bath = is_evening_prep and temp_upper < (TEMP_BATH_REDUCED if lower_is_warm else TEMP_BATH_TARGET)
    
    # Logika pro horní akumulaci
    upper_on = (
        # Kritické - pod komfortní teplotou (nutné nezávisle na energii)
        upper_needs_comfort or
        # Příprava na koupání podle času
        upper_needs_bath or
        # FVE přebytek - akumulace nad 70°C
        (fve_surplus > FVE_SURPLUS_THRESHOLD and battery_above_40 and temp_upper < TEMP_ACCUMULATION) or
        # MPC signál + levná elektřina
        (cheap_electricity and Hin_upper > 0.1) or
        # Velký FVE přebytek - vždy využít
        (fve_surplus > 5.0)
    )
    
    # Logika pro spodní akumulaci
    lower_on = (
        # MPC signál pro topení (heating_demand > 0)
        (Hin_lower > 0.1) or
        # FVE přebytek + dobrá baterie
        (fve_surplus > 1.0 and battery_above_40) or
        # Levná elektřina + MPC signál
        (cheap_electricity and Hin_lower > 0.1) or
        # Střední FVE přebytek
        (fve_surplus > 3.0)
    )
    
    # Celkový topný požadavek z MPC
    total_heating_demand = Hin_upper + Hin_lower
    
    # Kontrola záporné ceny energie (měl by už řešit MPC, ale pro jistotu)
    negative_price = Gbuy < 0
    
    # Maximální ohřev (12kW) - pouze když máme skutečně velký přebytek energie
    max_heat_on = (
        # Velký FVE přebytek - využít maximum (nezatěžuje síť)
        (fve_surplus > 8.0 and battery_above_40 and 
         temp_upper < TEMP_FULL_TANK and temp_lower < TEMP_FULL_TANK) or
        # Záporná cena energie - topíme na maximum (platí nám za spotřebu)
        (negative_price and battery_above_40 and
         (temp_upper < TEMP_FULL_TANK or temp_lower < TEMP_FULL_TANK))
    )
    
    # Blokování nuceného ohřevu - jen když je situace kritická
    # POZOR: blokuje i základní komfortní ohřevy!
    block_heating = (
        # Velmi kritická situace - málo energie + slabá baterie + drahá elektřina
        (fve_surplus < 0.2 and B_SOC < 20 and expensive_electricity and 
         not upper_needs_comfort) or  # Neblokuj při kritickém nedostatku tepla
        # Extrémně slabá baterie (ale ne při kritických teplotách)
        (B_SOC < 15 and not upper_needs_comfort)
    )
    
    # NOVÉ: Komfortní ohřev ze sítě - povolí ohřev horní části na 65°C i ze sítě
    # Připojuje se na switch.tepelnaakumulace_povolen_komfortn_ho_oh_evu
    comfort_heating_grid = (
        # Teplota pod komfortní - vždy povolit ohřev ze sítě
        upper_needs_comfort or
        # Příprava na koupání - povolit ohřev ze sítě (i když není FVE)
        upper_needs_bath or
        # MPC signál pro horní ohřev + rozumná cena elektřiny
        (Hin_upper > 0.1 and cheap_electricity) or
        # Záporná cena - vždy nahřát
        negative_price
    )
    
    return {
        "upper_accumulation": upper_on,
        "lower_accumulation": lower_on, 
        "max_heat": max_heat_on,
        "block_heating": block_heating,
        "comfort_heating_grid": comfort_heating_grid
    }

# ---------------------------------------------------------------------------
def powerplan_to_actions_timeline(sol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generuje plán akcí pro všechny časové sloty podle výstupů MPC optimizátoru.
    Výsledek obsahuje časové řady pro vizualizaci v grafech.
    """
    out = sol["outputs"]
    inp = sol.get("inputs", {})  # inputs contain predictions
    num_slots = len(out["h_in_upper"])
    
    # Příprava výstupních časových řad
    timeline = {
        "charger_mode": [],
        "upper_accumulation": [],
        "lower_accumulation": [],
        "max_heat": [],
        "heating_blocked": [],
        "comfort_heating_grid": [],
        "battery_target_soc": [],
        "reserve_power": [],
        "minimum_soc": [],
        "fve_surplus": [],
        "heating_logic": [],
    }
    
    for slot in range(num_slots):
        # Extrakce hodnot pro daný slot
        Hin_upper = out["h_in_upper"][slot]
        Hin_lower = out["h_in_lower"][slot]
        Hin_total = Hin_upper + Hin_lower
        Gsell = out["g_sell"][slot]
        Gbuy = out["g_buy"][slot]
        Bdis = out["b_discharge"][slot]
        Bchrg = out["b_charge"][slot]
        B_SOC = out["b_soc_percent"][slot]
        temp_upper = out["temp_upper"][slot]
        temp_lower = out["temp_lower"][slot]
        
        # Výpočet FVE přebytku
        fve_output = inp.get("fve_pred", [])[slot] if slot < len(inp.get("fve_pred", [])) else 0
        load_demand = inp.get("load_pred", [])[slot] if slot < len(inp.get("load_pred", [])) else 0
        fve_surplus = max(0, fve_output - load_demand)
        
        # Vylepšená logika ohřevu
        heating = enhanced_heating_logic(
            fve_surplus, B_SOC, Hin_upper, Hin_lower, Gbuy,
            temp_upper, temp_lower
        )
        
        # Režim střídače
        if Bdis > P_MAN_DIS:
            charger_mode = "Manual Discharge"
        elif Bchrg > P_MAN_DIS:
            charger_mode = "Manual Charge"
        elif (abs(Bdis) < 0.1 and abs(Bchrg) < 0.1 and 
              Gbuy > 0.2 and fve_output < 0.6):
            # Manual Idle pouze při specifických podmínkách:
            # - žádné nabíjení/vybíjení baterie
            # - nákup ze sítě (Gbuy > 0.2 kW)
            # - nízký výkon FVE (< 0.6 kW)
            # Zamezuje vybíjení baterie při nedostatku FVE a nákupu ze sítě
            charger_mode = "Manual Idle"
        elif Gsell > P_EXTRA_EXP:
            charger_mode = "Feedin Priority"
        else:
            charger_mode = PREFERRED_STANDARD_MODE
        
        # Rezervovaný výkon pro dobíjení
        reserve_power = max(0, int(Bchrg * 1000)) if B_SOC < 90 else 0
        
        # Minimální SOC
        minimum_soc = MIN_SOC_RESERVE if heating["max_heat"] else max(MIN_SOC_RESERVE - 10, 20)
        
        # Uložení do časových řad
        timeline["charger_mode"].append(charger_mode)
        timeline["upper_accumulation"].append(heating["upper_accumulation"])
        timeline["lower_accumulation"].append(heating["lower_accumulation"])
        timeline["max_heat"].append(heating["max_heat"])
        timeline["heating_blocked"].append(heating["block_heating"])
        timeline["comfort_heating_grid"].append(heating["comfort_heating_grid"])
        timeline["battery_target_soc"].append(round(B_SOC, 1))
        timeline["reserve_power"].append(reserve_power)
        timeline["minimum_soc"].append(minimum_soc)
        timeline["fve_surplus"].append(fve_surplus)
        
        # Logické kombinace pro vizualizaci
        heating_active = heating["upper_accumulation"] or heating["lower_accumulation"]
        timeline["heating_logic"].append({
            "heating_active": heating_active,
            "max_heat_active": heating["max_heat"],
            "heating_blocked": heating["block_heating"],
            "comfort_heating_grid": heating["comfort_heating_grid"],
            "charger_manual": charger_mode in ["Manual Charge", "Manual Discharge", "Manual Idle"],
            "charger_feedin": charger_mode == "Feedin Priority",
        })
    
    return timeline
