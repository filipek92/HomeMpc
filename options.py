# options.py
"""
Obsahuje specifikaci proměnných a funkce pro získání hodnot s výchozími hodnotami a odvozeninami.
"""

VARIABLES_SPEC = {
    # Vstupní vektory (series)
    "series": {
        "tuv_demand":    {"type": "list[float]", "unit": "kWh", "range": [0, None]},
        "heating_demand":{"type": "list[float]", "unit": "kWh", "range": [0, None]},
        "fve_pred":      {"type": "list[float]", "unit": "kW",  "range": [0, None]},
        "buy_price":     {"type": "list[float]", "unit": "Kč/kWh", "range": [0, None]},
        "sell_price":    {"type": "list[float]", "unit": "Kč/kWh", "range": [0, None]},
        "load_pred":     {"type": "list[float]", "unit": "kW",  "range": [0, None]},
    },
    # Počáteční stavy (initials)
    "initials": {
        "bat_soc":   {"type": "float", "unit": "%", "range": [0, 100]},
        "boiler_E":  {"type": "float", "unit": "kWh", "range": [0, 81]},
    },
    # Parametry a volby (options)
    "options": {
        "heating_enabled": {"type": "bool", "default": False},
        "charge_bat_min":  {"type": "bool", "default": False},
        "b_cap":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 17.4},
        "b_min":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 17.4*0.15},  # default se neuvádí, vždy dopočítat
        "b_max":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 17.4},  # default se neuvádí, vždy dopočítat
        "b_power":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 9},
        "b_eff_in":        {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "b_eff_out":       {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "h_cap":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 45.0},
        "h_power":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 12},
        "grid_limit":      {"type": "float", "unit": "kW",  "range": [0, None], "default": 18},
        "inverter_limit":  {"type": "float", "unit": "kW",  "range": [0, None], "default": 15},
        "final_boiler_price": {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "bat_threshold_pct": {"type": "float", "unit": "-", "range": [0, 1], "default": 0.40},
        "bat_price_below":   {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "bat_price_above":   {"type": "float", "unit": "Kč/kWh", "default": 0.5},
        "battery_penalty":   {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "fve_unused_penalty": {"type": "float", "unit": "Kč/kWh", "default": 0.1},
        "water_priority_bonus": {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "bat_under_penalty": {"type": "float", "unit": "Kč/kWh", "default": 0.1},
        # Přidáno pro ocenění energie v nádrži v konkrétní hodinu
        "tank_value_hour": {"type": "int", "unit": "hodina", "default": 18, "desc": "Hodina dne, kdy se oceňuje energie v nádrži"},
        "tank_value_bonus": {"type": "float", "unit": "Kč/kWh", "default": 1.0, "desc": "Odměna za energii v nádrži v danou hodinu"},
        "parasitic_water_heating": {"type": "float", "unit": "-", "default": 0.05, "desc": "Podíl parazitní energie při ohřevu vody"},
    }
}

def get_option(options, key, spec=VARIABLES_SPEC["options"], context=None):
    """Vrací hodnotu z options, nebo default ze spec, případně dopočítá (např. b_min, b_max)."""
    # Pro b_min a b_max ignoruj 0.0 a None a vždy dopočítej, pokud není v options kladná hodnota
    if key in ("b_min", "b_max"):
        val = options.get(key, None)
        if val is not None and val > 0:
            return val
        if key == "b_min":
            b_cap = get_option(options, "b_cap", spec)
            return b_cap * 0.15
        if key == "b_max":
            b_cap = get_option(options, "b_cap", spec)
            return b_cap * 1.0
    if key in options:
        return options[key]
    if key == "final_boiler_price" and context and "buy_price" in context:
        return min(context["buy_price"]) - 0.5
    if key == "bat_price_below" and context and "buy_price" in context:
        return min(context["buy_price"])
    if key == "bat_price_above" and context and "buy_price" in context:
        return min(context["buy_price"]) - 0.5
    meta = spec.get(key, {})
    if "default" in meta:
        return meta["default"]
    # Výchozí pro bool/float
    if meta.get("type") == "bool":
        return False
    if meta.get("type") == "float":
        return 0.0
    return None
