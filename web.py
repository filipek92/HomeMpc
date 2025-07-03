from flask import Flask, render_template_string, redirect, url_for
from datetime import timedelta, datetime
from home_mpc import run_mpc_optimizer
from prepare_data import prepare_data
from presentation import presentation

import json
import os

app = Flask(__name__)

RESULTS_FILE = "mpc_results_cache.json"

# --- Výpočet a cache ------------------------------------------------------

def compute_and_cache():
    (
        hours,
        tuv_demand,
        heating_demand,
        fve,
        buy,
        sell,
        base,
        soc_bat,
        soc_boiler,
        outdoor_temps,
    ) = prepare_data()

    ts = run_mpc_optimizer(
        {
            "tuv_demand": tuv_demand,
            "heating_demand": heating_demand,
            "fve": fve,
            "buy": buy,
            "sell": sell,
            "load": base,
        },
        {
            "soc_bat": soc_bat,
            "soc_boiler": soc_boiler,
        },
        hours
    )["time_series"]

    generated_at = datetime.now()

    cache = {
        "generated_at": generated_at.isoformat(),
        "hours": [h.isoformat() for h in hours],
        "ts": ts,
        "outdoor_temps": outdoor_temps,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(cache, f, indent=4)

    return generated_at, hours, ts, outdoor_temps


def load_cache():
    if not os.path.exists(RESULTS_FILE):
        return None
    with open(RESULTS_FILE, "r") as f:
        data = json.load(f)
    hours = [datetime.fromisoformat(s) for s in data["hours"]]
    return datetime.fromisoformat(data["generated_at"]), hours, data["ts"], data["outdoor_temps"]

# --- Web routes -----------------------------------------------------------

@app.route("/regenerate", methods=["POST"])
def regenerate():
    compute_and_cache()
    return redirect(url_for("index"))

@app.route("/")
def index():
    cache = load_cache()
    generated_at, hours, ts, outdoor_temps = cache if cache else compute_and_cache()

    if(generated_at < datetime.now() - timedelta(minutes=1)):
        # If the cache is older than 1 minute, regenerate it
        generated_at, hours, ts, outdoor_temps = compute_and_cache()
    

    graph_html = presentation(hours, ts, outdoor_temps)

    return render_template_string(
        """
        <html>
            <head>
                <title>Optimalizace energie</title>
                <meta charset="utf-8" />
            </head>
            <body>
                <h1>Vizualizace výsledků</h1>
                <p>Data vygenerována: {{ generated_at }}</p>
                <form action="/regenerate" method="post">
                    <button type="submit">Přegenerovat</button>
                </form>
                {{ graph | safe }}
            </body>
        </html>
        """,
        graph=graph_html, generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
