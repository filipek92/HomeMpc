from flask import Flask, render_template_string
import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
from datetime import timedelta
from home_mpc import run_mpc_optimizer
from models import (
    get_electricity_price,
    get_electricity_load,
    get_tuv_demand,
    get_fve_forecast,
    get_estimate_heating_losses,
    get_temperature_forecast,
)
import requests
import json

app = Flask(__name__)

HA_URL = "http://hass.lan:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlOWQ2MWJkMzBmNzY0ZDFlYTFlM2JiMGVhYWRlYzIwMyIsImlhdCI6MTc1MTM5NTg2MywiZXhwIjoyMDY2NzU1ODYzfQ.mFrACWhl4AyvEwMrTEipBuScHj5UkABSdN3Vc02rYNM"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

ha_color = {
    # stavy
    "B_SOC_percent": "#4db6ac",
    "H_SOC_percent": "#9d770f",
    # výkony
    "B_power": "#4db6ac",
    "B_charge": "#f06292",
    "B_discharge": "#4db6ac",
    "H_in": "#c97a94",
    "G_buy": "#488fc2",
    "G_sell": "#8353d1",
    "H_out": "#0f9d58",
    "fve": "#ff9800",
    "load": "#488fc2",
    # ceny
    "buy_price": "#488fc2",
    "sell_price": "#8353d1",
    # okolí
    "heating_demand": "#0f9d58",
    "outdoor_temps": "#ff9800",
}

labels = {
    "B_power": "Výkon baterie",
    "B_charge": "Nabíjení baterie",
    "B_discharge": "Vybíjení baterie",
    "G_buy": "Nákup ze sítě",
    "G_sell": "Prodej do sítě",
    "H_in": "Ohřev",
    "H_out": "Výstup z bojleru",
    "fve": "FVE výroba",
    "load": "Spotřeba",
    "buy_price": "Cena nákup",
    "sell_price": "Cena prodej",
    "heating_demand": "Tepelné ztráty",
    "outdoor_temps": "Venkovní teplota",
    "B_SOC_percent": "SoC baterie",
    "H_SOC_percent": "SoC bojleru",
}

# --- Pomocné funkce -------------------------------------------------------

def get_ha_states():
    response = requests.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()

def get_entity(state_list, entity_id, default=0.0):
    for e in state_list:
        if e["entity_id"] == entity_id:
            try:
                return float(e["state"])
            except ValueError:
                return default
    return default

def prepare_data():
    states = get_ha_states()

    # --- předpovědi a ceny -------------------------------------------------
    fve_raw = get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_today")
    fve_raw.extend(
        get_fve_forecast(states, "sensor.solcast_pv_forecast_forecast_tomorrow")
    )
    buy_raw = get_electricity_price(states, "sensor.current_buy_electricity_price")
    sell_raw = get_electricity_price(states, "sensor.current_sell_electricity_price")

    hours = [h for h, _ in buy_raw]
    horizon = len(hours)

    fve = [v for _, v in fve_raw][:horizon]
    buy = [v for _, v in buy_raw][:horizon]
    sell = [v for _, v in sell_raw][:horizon]

    outdoor_forecast = get_temperature_forecast(hours)
    outdoor_temps = [temp for _, temp in outdoor_forecast]

    soc_bat = get_entity(states, "sensor.odhadovana_byvajici_kapacita", 11.0)
    soc_boiler = get_entity(states, "sensor.tepelnaakumulace_energie_n_dr_e", 25.0)

    tuv_demand = [get_tuv_demand(h) for h in hours]
    heating_demand = [get_estimate_heating_losses(t) for t in outdoor_temps]
    base = [get_electricity_load(h) for h in hours]

    return (
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
    )

# --- Web route ------------------------------------------------------------

@app.route("/")
def index():
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
        tuv_demand, heating_demand, fve, buy, sell, base, soc_bat, soc_boiler, hours
    )["time_series"]

    # --- definice skupin pro grafy (převzato z matplotlib verze) ----------
    SOCs = ["B_SOC_percent", "H_SOC_percent"]
    inverted = ["G_sell", "H_out", "B_discharge"]  # odstraněn duplicitní "G_sell"
    steps = ["H_in", "H_out", "fve", "load"]
    bars = ["B_charge", "B_discharge", "G_sell", "G_buy"]

    # --- tvorba figure se 4 řádky ---------------------------------------
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=(
            "Stavy (SoC)",
            "Výkony",
            "Ceny elektřiny",
            "Tepelné ztráty a venkovní teplota",
        ),
    )

    # 1) Stavy ------------------------------------------------------------
    for key in SOCs:
        fig.add_trace(
            go.Scatter(
                x=[t + timedelta(hours=1) for t in hours],
                y=ts[key],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
            ),
            row=1,
            col=1,
        )

    # 2) Výkony -----------------------------------------------------------
    # krokové křivky
    for key in steps:
        fig.add_trace(
            go.Scatter(
                x=hours,
                y=[-v if key in inverted else v for v in ts[key]],
                name=labels.get(key, key),
                line_shape="hv",
                mode="lines",
                marker_color=ha_color.get(key, "black"),
            ),
            row=2,
            col=1,
        )

    # bar grafy – rozprostřeme je lehce do šířky časové osy, aby se nepřekrývaly
    bars_cnt = len(bars)
    bar_offset = 1 / (bars_cnt + 1)  # posun v hodinách

    for i, key in enumerate(bars):
        fig.add_trace(
            go.Bar(
                x=[t + timedelta(hours=i * bar_offset) for t in hours],
                y=[-v if key in inverted else v for v in ts[key]],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
                opacity=0.8,
            ),
            row=2,
            col=1,
        )

    # 3) Ceny -------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=ts["buy_price"],
            name=labels["buy_price"],
            line_shape="hv",
            mode="lines",
            marker_color=ha_color["buy_price"],
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=ts["sell_price"],
            name=labels["sell_price"],
            line_shape="hv",
            mode="lines",
            marker_color=ha_color["sell_price"],
        ),
        row=3,
        col=1,
    )

    # 4) Tepelné ztráty a venkovní teplota --------------------------------
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=ts["heating_demand"],
            name=labels["heating_demand"],
            mode="lines",
            marker_color=ha_color["heating_demand"],
        ),
        row=4,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=outdoor_temps,
            name=labels["outdoor_temps"],
            mode="lines",
            marker_color=ha_color["outdoor_temps"],
        ),
        row=4,
        col=1,
    )

    # --- Svislé čáry pro prodej/nákup -----------------------------------
    shapes = []
    for idx, t in enumerate(hours):
        if ts["G_sell"][idx] > 0.5:
            shapes.append(
                dict(
                    type="line",
                    x0=t,
                    x1=t,
                    yref="paper",
                    y0=0,
                    y1=1,
                    line=dict(color="red", dash="dash", width=1),
                    opacity=0.3,
                )
            )
        if ts["G_buy"][idx] > 0.5:
            shapes.append(
                dict(
                    type="line",
                    x0=t,
                    x1=t,
                    yref="paper",
                    y0=0,
                    y1=1,
                    line=dict(color="green", dash="dash", width=1),
                    opacity=0.3,
                )
            )

    fig.update_layout(
        xaxis_title="Čas",
        hovermode="x unified",
        shapes=shapes,
    )

    # po vytvoření všech trace
    fig.update_yaxes(title_text="Energie [%]",     row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]",     row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]",   row=3, col=1)
    fig.update_yaxes(title_text="kWh / °C",        row=4, col=1)

    # --- HTML výstup ------------------------------------------------------
    graph_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

    return render_template_string(
        """
        <html>
            <head>
                <title>Optimalizace energie (Plotly)</title>
                <meta charset="utf-8" />
            </head>
            <body>
                <h1>Vizualizace výsledků</h1>
                {{ graph | safe }}
            </body>
        </html>
        """,
        graph=graph_html,
    )

# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
