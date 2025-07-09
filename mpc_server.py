#!/usr/bin/env python3

import os
import json
import csv
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, request
from flask_apscheduler import APScheduler

from home_mpc import run_mpc_optimizer, VARIABLES_SPEC
from data_connector import prepare_data, publish_to_ha
from presentation import presentation
from actions import mpc_to_actions, mpc_to_actions_timeline, ACTION_ATTRIBUTES
from mpc_settings import settings_bp, load_settings, save_settings
from publish_version import get_current_version

ENABLE_PUBLISH = bool(os.environ.get("HA_ADDON"))

if ENABLE_PUBLISH:
    print("Publishing to Home Assistant is enabled.")
else:
    print("Publishing to Home Assistant is disabled. Set HA_ADDON environment variable to enable it.")


app = Flask(__name__)

DATA_DIR = os.environ.get("HA_ADDON_DATA", ".")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
LATEST_LINK = os.path.join(RESULTS_DIR, "latest.json")
# Ensure results directory exists on startup
os.makedirs(RESULTS_DIR, exist_ok=True)

class Config:                                    # <-- nový blok
    # spustí miniaturní REST rozhraní na /scheduler (můžeš vypnout)
    SCHEDULER_API_ENABLED = False

app.config.from_object(Config())

app.register_blueprint(settings_bp)

# --- Výpočet a cache ------------------------------------------------------

def compute_and_cache():
    data = prepare_data()
    settings = load_settings()

    series_keys = [
        "tuv_demand",
        "heating_demand",
        "fve_pred",
        "buy_price",
        "sell_price",
        "load_pred",
        "outdoor_temps",
    ]

    initials_keys = ["bat_soc", "temp_upper", "temp_lower"]

    dt = [1.0] * len(data["hours"])  # předpokládáme hodinový krok
    remain_slot_part = data["hours"][1].astimezone(None) - datetime.now().astimezone(None)
    dt[0] = remain_slot_part.total_seconds() / 3600.0  # zbytek aktuálního slotu v hodinách

    solution = run_mpc_optimizer(
        {k: data[k] for k in series_keys},
        {k: data[k] for k in initials_keys},
        data["hours"],
        settings,
        dt
    )
    # Tag solution with current app version
    solution["version"] = get_current_version()

    actions = mpc_to_actions(solution)
    actions_timeline = mpc_to_actions_timeline(solution)

    solution["actions"] = actions
    solution["actions_timeline"] = actions_timeline

    extra = {
        "generated_at": solution["generated_at"],
        # parse the first timestamp string back to datetime for further use
        "current_slot": solution["times"][0],
    }

    print("Solution results", json.dumps(solution["results"], indent=2))

    if ENABLE_PUBLISH:
        publish_to_ha(actions, "mpc_", ACTION_ATTRIBUTES, extra)

        publish_to_ha({
            "debug": extra["current_slot"]
        }, "mpc_", {
            "debug": solution["results"]
        })
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Save the solution to a timestamped file using current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(RESULTS_DIR, f"result_{timestamp}.json")
    # Use absolute path for symlink target to avoid relative resolution issues
    abs_result_file = os.path.abspath(result_file)
    with open(result_file, "w") as f:
        json.dump(solution, f, indent=4)

    # Create CSV export
    csv_file = os.path.join(RESULTS_DIR, f"result_{timestamp}.csv")
    abs_csv_file = os.path.abspath(csv_file)
    create_csv_export(solution, csv_file)

    # Update the latest symlinks
    latest_json_link = LATEST_LINK
    latest_csv_link = os.path.join(RESULTS_DIR, "latest.csv")
    
    # JSON symlink
    if os.path.islink(latest_json_link) or os.path.exists(latest_json_link):
        os.remove(latest_json_link)
    os.symlink(abs_result_file, latest_json_link)
    
    # CSV symlink
    if os.path.islink(latest_csv_link) or os.path.exists(latest_csv_link):
        os.remove(latest_csv_link)
    os.symlink(abs_csv_file, latest_csv_link)

    return solution

def load_cache(filename=None):
    try:
        if filename is None:
            filename = LATEST_LINK
        else:
            filename = os.path.join(RESULTS_DIR, filename)
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        # If the file does not exist or is corrupted, return None
        print("Cache file not found or corrupted, recomputing...")
        return None

def create_csv_export(solution, filename):
    """
    Vytvoří CSV soubor s přehlednými daty z optimalizace.
    """
    times = solution["times"]
    inputs = solution["inputs"]
    outputs = solution["outputs"]
    actions_timeline = solution["actions_timeline"]
    
    # Příprava CSV dat
    csv_data = []
    for i, time_str in enumerate(times):
        row = {
            # Čas
            "Cas": time_str,
            
            # Vstupy
            "FVE_vyroba_kW": inputs["fve_pred"][i],
            "Spotreba_kW": inputs["load_pred"][i],
            "Cena_nakup_Kc_kWh": inputs["buy_price"][i],
            "Cena_prodej_Kc_kWh": inputs["sell_price"][i],
            "Pozadavek_TUV_kW": inputs["tuv_demand"][i],
            "Pozadavek_topeni_kW": inputs["heating_demand"][i],
            "Venkovni_teplota_C": inputs["outdoor_temps"][i],
            
            # Výstupy - baterie
            "Baterie_vykon_kW": outputs["b_power"][i],
            "Baterie_nabijeni_kW": outputs["b_charge"][i],
            "Baterie_vybijeni_kW": outputs["b_discharge"][i],
            "Baterie_SOC_kWh": outputs["b_soc"][i],
            "Baterie_SOC_procenta": outputs["b_soc_percent"][i],
            
            # Výstupy - síť
            "Sit_nakup_kW": outputs["g_buy"][i],
            "Sit_prodej_kW": outputs["g_sell"][i],
            "Naklady_nakup_Kc": outputs["buy_cost"][i],
            "Prijmy_prodej_Kc": outputs["sell_income"][i],
            "Celkove_naklady_Kc": outputs["net_step_cost"][i],
            
            # Výstupy - ohřev
            "Ohrev_dolni_kW": outputs["h_in_lower"][i],
            "Ohrev_horni_kW": outputs["h_in_upper"][i],
            "Ohrev_celkem_kW": outputs["h_in_lower"][i] + outputs["h_in_upper"][i],
            "Odber_dolni_kW": outputs["h_out_lower"][i],
            "Odber_horni_kW": outputs["h_out_upper"][i],
            
            # Výstupy - akumulace
            "Akumulace_dolni_kWh": outputs["h_soc_lower"][i],
            "Akumulace_horni_kWh": outputs["h_soc_upper"][i],
            "Akumulace_dolni_procenta": outputs["h_soc_lower_percent"][i],
            "Akumulace_horni_procenta": outputs["h_soc_upper_percent"][i],
            
            # Teploty
            "Teplota_dolni_C": outputs["temp_lower"][i],
            "Teplota_horni_C": outputs["temp_upper"][i],
            
            # Akce
            "Rezim_menic": actions_timeline["charger_mode"][i],
            "Horni_akumulace": actions_timeline["upper_accumulation"][i],
            "Dolni_akumulace": actions_timeline["lower_accumulation"][i],
            "Maximalni_ohrev": actions_timeline["max_heat"][i],
            "Blokovani_ohrevu": actions_timeline["heating_blocked"][i],
            "Cilovy_SOC_procenta": actions_timeline["battery_target_soc"][i],
            "Rezervovany_vykon_W": actions_timeline["reserve_power"][i],
            "Minimalni_SOC_procenta": actions_timeline["minimum_soc"][i],
            
            # Vypočítané hodnoty
            "FVE_prebytek_kW": max(0, inputs["fve_pred"][i] - inputs["load_pred"][i]),
            "Nevyuzita_FVE_kW": outputs.get("fve_unused", [0] * len(times))[i],
            "Energeticka_bilance_kW": (
                inputs["fve_pred"][i] + outputs["b_discharge"][i] + outputs["g_buy"][i] -
                inputs["load_pred"][i] - outputs["b_charge"][i] - outputs["g_sell"][i] -
                outputs["h_in_lower"][i] - outputs["h_in_upper"][i]
            ),
        }
        csv_data.append(row)
    
    # Zápis do CSV
    if csv_data:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)

# --- Web routes -----------------------------------------------------------

@app.route("/regenerate", methods=["POST"])
def regenerate():
    compute_and_cache()
    return redirect('./')

@app.route("/")
def index():
    # List result files in descending order (newest first)
    all_files = sorted(
        (f for f in os.listdir(RESULTS_DIR)
         if f.startswith('result_') and f.endswith('.json')),
        reverse=True
    )
    # Seskupení podle data (YYYYMMDD)
    from collections import defaultdict
    grouped_files = defaultdict(list)
    for fname in all_files:
        date_part = fname.split('_')[1]  # např. '20250707'
        time_part = fname.split('_')[2].split('.')[0]  # např. '140000'
        # Převod času na čitelnější formát HH:MM:SS
        formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
        grouped_files[date_part].append((time_part, formatted_time, fname))
    grouped_files = dict(sorted(grouped_files.items(), reverse=True))

    # Připravit seznam dnů a časů
    available_days = list(grouped_files.keys())
    compare_day = request.args.get('day')
    compare_time = request.args.get('time')
    selected_file = None
    available_times = []
    available_times_display = []
    if compare_day and compare_day in grouped_files:
        available_times = [t for t, _, _ in grouped_files[compare_day]]
        available_times_display = [display_t for _, display_t, _ in grouped_files[compare_day]]
        if compare_time and compare_time in available_times:
            # Najít odpovídající soubor
            for t, _, f in grouped_files[compare_day]:
                if t == compare_time:
                    selected_file = f
                    break
    # Pokud není vybrán konkrétní soubor, použij latest
    if not selected_file:
        solution = load_cache()
        if solution is None:
            solution = compute_and_cache()
    else:
        solution = load_cache(selected_file)
        print(f"Loaded solution from {selected_file} {solution['version']}")

    generated_at = datetime.fromisoformat(solution.get("generated_at"))
    graphs = presentation(solution)
    
    # Připravit dodatečná data pro template
    slots = solution.get("slots", [])
    first_slot_data = slots[0] if slots else {}
    current_results = solution.get("results", {})

    return render_template(
        'index.html',
        graphs=graphs,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        solution=solution,
        available_days=available_days,
        available_times=available_times,
        available_times_display=available_times_display,
        compare_day=compare_day,
        compare_time=compare_time,
        day=compare_day,  # Pro zpětnou kompatibilitu
        first_slot_data=first_slot_data,
        current_results=current_results,
        version=get_current_version(),
    )
if __name__ == "__main__":

    if os.environ.get("HA_ADDON"):
        # pokud běží v Dockeru, použij přepočítávej pravielně model

        scheduler = APScheduler()                        # <-- nový objekt
        scheduler.init_app(app)

        # registrace úlohy – každých 5 minut v celou (00, 05, 10, ...)
        scheduler.add_job(
            id="mpc_refresh",
            func=compute_and_cache,
            trigger="cron",
            minute="*/5",
        )

        scheduler.start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "26781")), debug=True)

