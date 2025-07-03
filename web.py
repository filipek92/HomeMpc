from flask import Flask, render_template_string, redirect, url_for
from datetime import timedelta, datetime
from home_mpc import run_mpc_optimizer
from data_connector import prepare_data, publish_to_ha
from presentation import presentation
from actions import mpc_to_actions

import json

app = Flask(__name__)

RESULTS_FILE = "mpc_results_cache.json"

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

    solution = run_mpc_optimizer(
        {k: data[k] for k in series_keys},
        {k: data[k] for k in initials_keys},
        data["hours"]
    )

    actions = mpc_to_actions(solution)

    solution["actions"] = actions

    publish_to_ha(actions)

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
    return redirect(url_for("index"))

@app.route("/")
def index():
    solution = load_cache()
    if solution is None:
        # If cache is empty or corrupted, compute and cache the results
        solution = compute_and_cache()

    generated_at = datetime.fromisoformat(solution.get("generated_at"))

    if(generated_at < datetime.now() - timedelta(minutes=1)):
        # If the cache is older than 1 minute, regenerate it
        solution = compute_and_cache()
    

    graph_html = presentation(solution)

    return render_template_string(
        """
        <html>
            <head>
                <title>Optimalizace energie</title>
                <meta charset="utf-8" />
            </head>
            <body>
                <h1>Vizualizace výsledků</h1>
                <form action="/regenerate" method="post">
                    <button type="submit">Přegenerovat</button>
                </form>
                {{ graph | safe }}
                <pre>{{ solution["actions"] | tojson(indent=2) }}</pre>
                <p>Data vygenerována: {{ generated_at }}</p>
            </body>
        </html>
        """,
        graph=graph_html, generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"), solution=solution
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
