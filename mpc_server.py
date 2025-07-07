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
from mpc_settings import settings_bp, load_settings, save_settings
from publish_version import get_current_version

ENABLE_PUBLISH = bool(os.environ.get("HA_ADDON"))

if ENABLE_PUBLISH:
    print("Publishing to Home Assistant is enabled.")
else:
    print("Publishing to Home Assistant is disabled. Set HA_ADDON environment variable to enable it.")


app = Flask(__name__)

# Directory for storing all optimization results and symlink to latest
if os.path.isdir("/data"):
    # If running in Docker, use /data for storing results
    # This allows persistent storage across container restarts
    # and makes it accessible outside the container.

    RESULTS_DIR = "/data/results"
else:
    # If running locally, use the current directory
    # This is useful for development and testing.
    # Results will be stored in a "results" subdirectory.
    RESULTS_DIR = "results"
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
    # Tag solution with current app version
    solution["version"] = get_current_version()

    actions, meta = mpc_to_actions(solution)

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
            "debug": meta
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
        with open(LATEST_LINK, "r") as f:
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
    available_files = sorted(
        (f for f in os.listdir(RESULTS_DIR)
         if f.startswith('result_') and f.endswith('.json')),
        reverse=True
    )

    compare_file = request.args.get('compare')
    if not compare_file in available_files:

        # Load latest or cached solution
        solution = load_cache()
        if solution is None:
            # If cache is empty or corrupted, compute and cache the results
            solution = compute_and_cache()
        # Prepare list of past results for comparison

    else:
        solution = load_cache(compare_file)

    generated_at = datetime.fromisoformat(solution.get("generated_at"))
    # Generate graphs
    graph_html = presentation(solution)

    return render_template_string(
        """
        <html>
            <head>
                <title>Optimalizace energie</title>
                <meta charset="utf-8" />
                <meta http-equiv="refresh" content="300">
                <style>
                    table { border-collapse: collapse; margin-bottom: 2em; }
                    th, td { border: 1px solid #ccc; padding: 0.3em 0.7em; }
                    th { background: #f0f0f0; }
                </style>
            </head>
            <body style="background-color: #ffffff">
                <div style="position:absolute; top:10px; right:10px; font-size:0.9em; color:#666;">
                  Verze: {{ solution["version"] }}
                </div>
                <!-- Selector for comparing older results -->
                <form method="get" action="./">
                  <label for="compare">Porovnat s:</label>
                  <select name="compare" id="compare">
                    <option value="">Aktuální (latest)</option>
                    {% for f in available_files %}
                      <option value="{{ f }}" {% if f==compare_file %}selected{% endif %}>{{ f }}</option>
                    {% endfor %}
                  </select>
                  <button type="submit">Zobrazit</button>
                </form>
                {% if compare_file %}
                <h1>Vizualizace výsledků {{compare_file}}</h1>
                {% else %}
                <h1>Vizualizace aktuálních výsledků</h1>
                {% endif %}
                {{ graph | safe }}
                <h2>Actions</h2>
                {% set actions = solution["actions"] %}
                {% if actions is string %}
                  <pre>{{ actions }}</pre>
                {% elif actions is mapping %}
                  <table>
                    <tr>{% for k in actions.keys() %}<th>{{ k }}</th>{% endfor %}</tr>
                    <tr>{% for v in actions.values() %}<td>{{ v }}</td>{% endfor %}</tr>
                  </table>
                {% elif actions is iterable %}
                  {% for action in actions %}
                    {% if action is mapping %}
                      <table>
                        <tr>{% for k in action.keys() %}<th>{{ k }}</th>{% endfor %}</tr>
                        <tr>{% for v in action.values() %}<td>{{ v }}</td>{% endfor %}</tr>
                      </table>
                    {% else %}
                      <pre>{{ action }}</pre>
                    {% endif %}
                  {% endfor %}
                {% else %}
                  <pre>{{ actions }}</pre>
                {% endif %}
                <h2>Results</h2>
                <table>
                  <tr><th>Klíč</th><th>Hodnota</th></tr>
                  {% for k, v in solution["results"].items() %}
                    <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
                  {% endfor %}
                </table>
                <h2>Nastavnení <a href="settings">Edit</a></h2>
                <table>
                  <tr><th>Parametr</th><th>Hodnota</th></tr>
                  {% for k, v in solution["options"].items() %}
                    <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
                  {% endfor %}
                </table>
                {% if solution["version"] != version %}
                <p>Data vygenerována: {{ generated_at }} (v{{ solution["version"] }})</p>
                {% else %}
                <p>Data vygenerována: {{ generated_at }}</p>
                {% endif %}
                <form action="./regenerate" method="post">
                    <button type="submit">Přegenerovat</button>
                </form>
            </body>
        </html>
        """,
        graph=graph_html,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        solution=solution,
        available_files=available_files,
        compare_file=compare_file,
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

