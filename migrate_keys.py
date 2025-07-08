import os
import json
import shutil
import glob

# Pokud běží v HA addonu, používej HA_ADDON_DATA jako pracovní adresář
DATA_DIR = os.environ.get("HA_ADDON_DATA", ".")
MIGRATION_FLAG = os.path.join(DATA_DIR, ".migration_done")

RESULTS_DIR = os.path.join(DATA_DIR, "results")
SETTINGS_FILES = [
    os.path.join(DATA_DIR, "mpc_settings.json"),
]

def migrate_keys(obj, key_map):
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            new_key = key_map.get(k, k.lower() if k.isupper() else k)
            new_obj[new_key] = migrate_keys(v, key_map)
        return new_obj
    elif isinstance(obj, list):
        return [migrate_keys(x, key_map) for x in obj]
    else:
        return obj

def migrate_json_file(path, key_map):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    new_data = migrate_keys(data, key_map)
    shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print(f"Migrated: {path}")

def run_migration():
    if os.path.exists(MIGRATION_FLAG):
        print("Migration already done, skipping.")
        return
    KEY_MAP = {
        # outputs/results
        "B_power": "b_power",
        "B_charge": "b_charge",
        "B_discharge": "b_discharge",
        "B_SOC": "b_soc",
        "B_SOC_percent": "b_soc_percent",
        "H_SOC": "h_soc",
        "H_SOC_percent": "h_soc_percent",
        "H_in": "h_in",
        "H_out": "h_out",
        "G_buy": "g_buy",
        "G_sell": "g_sell",
        "FVE_unused": "fve_unused",
        "buy_cost": "buy_cost",
        "sell_income": "sell_income",
        "net_step_cost": "net_step_cost",
        # parametry/options
        "B_CAP": "b_cap",
        "B_MIN": "b_min",
        "B_MAX": "b_max",
        "B_POWER": "b_power",
        "B_EFF_IN": "b_eff_in",
        "B_EFF_OUT": "b_eff_out",
        "H_CAP": "h_cap",
        "H_POWER": "h_power",
        "GRID_LIMIT": "grid_limit",
        "INVERTER_LIMIT": "inverter_limit",
        "final_boler_price": "final_boiler_price",
        "BAT_THRESHOLD_PCT": "bat_threshold_pct",
        "BAT_PRICE_BELOW": "bat_price_below",
        "BAT_PRICE_ABOVE": "bat_price_above",
        "battery_penalty": "battery_penalty",
        "fve_unused_penalty": "fve_unused_penalty",
        "WATER_PRIORITY_BONUS": "water_priority_bonus",
        "BAT_UNDER_PENALTY": "bat_under_penalty",
        "tank_value_hour": "tank_value_hour",
        "tank_value_bonus": "tank_value_bonus",
        "PARASITIC_WATER_HEATING": "parasitic_water_heating",
        "total_BAT_PRICE_ABOVE": "total_bat_price_above",
        "total_BAT_PRICE_BELOW": "total_bat_price_below",
        # další možné
        "soc_bat": "soc_bat",
        "soc_boiler": "soc_boiler",
        "heating_enabled": "heating_enabled",
        "charge_bat_min": "charge_bat_min",
    }
    # Migruj všechny výsledky v /results/
    if os.path.exists(RESULTS_DIR):
        for file in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
            migrate_json_file(file, KEY_MAP)
    # Migruj konfiguraci v konfiguraci
    for config in SETTINGS_FILES:
        if os.path.exists(config):
            migrate_json_file(config, KEY_MAP)
    # Zapiš flag, že migrace proběhla
    with open(MIGRATION_FLAG, "w") as f:
        f.write("Migration done.")
    print("Migration completed.")

# Spustí migraci automaticky při importu (např. v HA addonu)
run_migration()
