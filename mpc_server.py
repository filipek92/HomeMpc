#!/usr/bin/env python3

from flask import Flask, render_template_string, redirect, url_for
from datetime import timedelta, datetime
from home_mpc import run_mpc_optimizer
from data_connector import prepare_data, publish_to_ha
from presentation import presentation
from actions import mpc_to_actions, ACTION_ATTRIBUTES

from flask_apscheduler import APScheduler  

import json
import os

app = Flask(__name__)

RESULTS_FILE = "mpc_results_cache.json"

class Config:                                    # <-- nový blok
    # spustí miniaturní REST rozhraní na /scheduler (můžeš vypnout)
    SCHEDULER_API_ENABLED = False

app.config.from_object(Config())

# --- Výpočet a cache ------------------------------------------------------

def compute_and_cache():
    data = prepare_data()

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
    data["hours"][0] = data["hours"][1] - remain_slot_part # zajištění, že čas je v UTC

    solution = run_mpc_optimizer(
        {k: data[k] for k in series_keys},
        {k: data[k] for k in initials_keys},
        data["hours"],
        {},
        dt
    )

    actions, meta = mpc_to_actions(solution)

    solution["actions"] = actions

    extra = {
        "generated_at": solution["generated_at"],
        "current_slot": solution["times"][0],
    }

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
                <pre>{{ solution["actions"] | tojson(indent=2) }}</pre>
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
