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
        "B_CAP":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 17.4},
        "B_MIN":           {"type": "float", "unit": "kWh", "range": [0, None]},  # default se neuvádí, vždy dopočítat
        "B_MAX":           {"type": "float", "unit": "kWh", "range": [0, None]},  # default se neuvádí, vždy dopočítat
        "B_POWER":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 9},
        "B_EFF_IN":        {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "B_EFF_OUT":       {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "H_CAP":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 45.0},
        "H_POWER":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 12},
        "GRID_LIMIT":      {"type": "float", "unit": "kW",  "range": [0, None], "default": 18},
        "INVERTER_LIMIT":  {"type": "float", "unit": "kW",  "range": [0, None], "default": 15},
        "final_boler_price": {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "BAT_THRESHOLD_PCT": {"type": "float", "unit": "-", "range": [0, 1], "default": 0.40},
        "BAT_PRICE_BELOW":   {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "BAT_PRICE_ABOVE":   {"type": "float", "unit": "Kč/kWh", "default": 0.5},
        "battery_penalty":   {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "fve_unused_penalty": {"type": "float", "unit": "Kč/kWh", "default": 0.1},
        "WATER_PRIORITY_BONUS": {"type": "float", "unit": "Kč/kWh", "default": 1.0},
        "BAT_UNDER_PENALTY": {"type": "float", "unit": "Kč/kWh", "default": 0.1},
        # Přidáno pro ocenění energie v nádrži v konkrétní hodinu
        "tank_value_hour": {"type": "int", "unit": "hodina", "default": 18, "desc": "Hodina dne, kdy se oceňuje energie v nádrži"},
        "tank_value_bonus": {"type": "float", "unit": "Kč/kWh", "default": 1.0, "desc": "Odměna za energii v nádrži v danou hodinu"},
        "PARASITIC_WATER_HEATING": {"type": "float", "unit": "-", "default": 0.05, "desc": "Podíl parazitní energie při ohřevu vody"},
    }
}

def get_option(options, key, spec=VARIABLES_SPEC["options"], context=None):
    """Vrací hodnotu z options, nebo default ze spec, případně dopočítá (např. B_MIN, B_MAX)."""
    # Pro B_MIN a B_MAX ignoruj 0.0 a None a vždy dopočítej, pokud není v options kladná hodnota
    if key in ("B_MIN", "B_MAX"):
        val = options.get(key, None)
        if val is not None and val > 0:
            return val
        if key == "B_MIN":
            B_CAP = get_option(options, "B_CAP", spec)
            return B_CAP * 0.15
        if key == "B_MAX":
            B_CAP = get_option(options, "B_CAP", spec)
            return B_CAP * 1.0
    if key in options:
        return options[key]
    if key == "final_boler_price" and context and "buy_price" in context:
        return min(context["buy_price"]) - 0.5
    if key == "BAT_PRICE_BELOW" and context and "buy_price" in context:
        return min(context["buy_price"])
    if key == "BAT_PRICE_ABOVE" and context and "buy_price" in context:
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
