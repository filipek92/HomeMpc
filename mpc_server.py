#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta

from flask import Flask, render_template_string, redirect, url_for, request
from flask_apscheduler import APScheduler

from home_mpc import run_mpc_optimizer, VARIABLES_SPEC
from data_connector import prepare_data, publish_to_ha
from presentation import presentation
from actions import mpc_to_actions, ACTION_ATTRIBUTES
from mpc_settings import settings_bp

ENABLE_PUBLISH = bool(os.environ.get("HA_ADDON"))

if ENABLE_PUBLISH:
    print("Publishing to Home Assistant is enabled.")
else:
    print("Publishing to Home Assistant is disabled. Set HA_ADDON environment variable to enable it.")


app = Flask(__name__)

RESULTS_FILE = "mpc_results_cache.json"
SETTINGS_FILE = "mpc_settings.json"

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

    initials_keys = ["bat_soc", "boiler_E"]

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

    actions, meta = mpc_to_actions(solution)

    solution["actions"] = actions

    extra = {
        "generated_at": solution["generated_at"],
        "current_slot": solution["times"][0],
    }

    print("Solution results", json.dumps(solution["results"], indent=2))

    if ENABLE_PUBLISH:
        publish_to_ha(actions, "mpc_", ACTION_ATTRIBUTES, extra)

        publish_to_ha({
            "debug": extra["current_slot"]
        }, "mpc_", {
            "debug": meta
        })
    
    with open(RESULTS_FILE, "w") as f:
        json.dump(solution, f, indent=4)

    return solution

def load_cache():
    try:
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        # If the file does not exist or is corrupted, return None
        print("Cache file not found or corrupted, recomputing...")
        return None

# Načtení nastavení z JSON souboru

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {}

# Uložení nastavení do JSON souboru

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# --- Web routes -----------------------------------------------------------

@app.route("/regenerate", methods=["POST"])
def regenerate():
    compute_and_cache()
    return redirect('./')

@app.route("/")
def index():
    solution = load_cache()
    if solution is None:
        # If cache is empty or corrupted, compute and cache the results
        solution = compute_and_cache()

    generated_at = datetime.fromisoformat(solution.get("generated_at"))
    

    graph_html = presentation(solution)

    return render_template_string(
        """
        <html>
            <head>
                <title>Optimalizace energie</title>
                <meta charset="utf-8" />
            </head>
            <body style="background-color: #ffffff">
                <h1>Vizualizace výsledků</h1>
                {{ graph | safe }}
                <h2>Actions</h2>
                <pre>{{ solution["actions"] | tojson(indent=2) }}</pre>
                <h2>Results</h2>
                <pre>{{ solution["results"] | tojson(indent=2) }}</pre>
                <h2>Nastavnení <a href="settings">Edit</a></h2>
                <pre>{{ solution["options"] | tojson(indent=2) }}</pre>
                <p>Data vygenerována: {{ generated_at }}</p>
                <form action="./regenerate" method="post">
                    <button type="submit">Přegenerovat</button>
                </form>
            </body>
        </html>
        """,
        graph=graph_html, generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"), solution=solution
    )
if __name__ == "__main__":

    # --- Scheduler -----------------------------------------------------------
    scheduler = APScheduler()                        # <-- nový objekt
    scheduler.init_app(app)

    # registrace úlohy – co 5 minut zavolej compute_and_cache()
    scheduler.add_job(
        id="mpc_refresh",
        func=compute_and_cache,
        trigger="interval",
        minutes=5,
    )

    scheduler.start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "26781")), debug=True)

