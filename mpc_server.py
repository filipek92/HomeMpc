#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, request
from flask_apscheduler import APScheduler

from home_mpc import run_mpc_optimizer, VARIABLES_SPEC
from data_connector import prepare_data, publish_to_ha
from presentation import presentation
from actions import mpc_to_actions, ACTION_ATTRIBUTES
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
LATEST_LINK = os.path.join(RESULTS_DIR, "latest")
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

    solution["actions"] = actions

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

    # Update the latest symlink
    if os.path.islink(LATEST_LINK) or os.path.exists(LATEST_LINK):
        os.remove(LATEST_LINK)
    os.symlink(abs_result_file, LATEST_LINK)

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
        grouped_files[date_part].append((time_part, fname))
    grouped_files = dict(sorted(grouped_files.items(), reverse=True))

    # Připravit seznam dnů a časů
    available_days = list(grouped_files.keys())
    compare_day = request.args.get('day')
    compare_time = request.args.get('time')
    selected_file = None
    available_times = []
    if compare_day and compare_day in grouped_files:
        available_times = [t for t, _ in grouped_files[compare_day]]
        if compare_time and compare_time in available_times:
            # Najít odpovídající soubor
            for t, f in grouped_files[compare_day]:
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
    graph_html = presentation(solution)

    return render_template(
        'index.html',
        graph=graph_html,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        solution=solution,
        available_days=available_days,
        available_times=available_times,
        compare_day=compare_day,
        compare_time=compare_time,
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

