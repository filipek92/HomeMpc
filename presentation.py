from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.io as pio
from datetime import timedelta, datetime

ha_color = {
    # stavy
    "b_soc_percent": "#4db6ac",
    "h_soc_percent": "#9d770f",
    # výkony
    "b_power": "#4db6ac",
    "b_charge": "#f06292",
    "b_discharge": "#4db6ac",
    "h_in": "#c97a94",
    "g_buy": "#488fc2",
    "g_sell": "#8353d1",
    "h_out": "#0f9d58",
    "fve_pred": "#ff9800",
    "load_pred": "#488fc2",
    # ceny
    "buy_price": "#488fc2",
    "sell_price": "#8353d1",
    # okolí
    "heating_demand": "#0f9d58",
    "outdoor_temps": "#ff9800",
}

labels = {
    "b_power": "Výkon baterie",
    "b_charge": "Nabíjení baterie",
    "b_discharge": "Vybíjení baterie",
    "g_buy": "Nákup ze sítě",
    "g_sell": "Prodej do sítě",
    "h_in": "Ohřev",
    "h_out": "Výstup z bojleru",
    "fve_pred": "FVE výroba",
    "load_pred": "Spotřeba",
    "buy_price": "Cena nákup",
    "sell_price": "Cena prodej",
    "heating_demand": "Tepelné ztráty",
    "outdoor_temps": "Venkovní teplota",
    "b_soc_percent": "SoC baterie",
    "h_soc_percent": "SoC bojleru",
}

def presentation(solution):
    times = [datetime.fromisoformat(t) for t in solution["times"]]

    ts = {**solution["inputs"], **solution["outputs"]}

    socs = ["b_soc_percent", "h_soc_percent"]
    inverted = ["g_sell", "h_out", "b_discharge"]
    steps = ["h_in", "h_out", "fve_pred", "load_pred"]
    bars = ["b_charge", "b_discharge", "g_buy", "g_sell"]

    options = solution.get("options", {})
    heating_enabled = options.get("heating_enabled", False)

    fig = make_subplots(
        rows=4 if heating_enabled else 3,
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

    for key in socs:
        fig.add_trace(
            go.Scatter(
                x=[t + timedelta(hours=1) for t in times],
                y=ts[key],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
            ),
            row=1,
            col=1,
        )

    for key in steps:
        fig.add_trace(
            go.Scatter(
                x=times,
                y=[-v if key in inverted else v for v in ts[key]],
                name=labels.get(key, key),
                line_shape="hv",
                mode="lines",
                marker_color=ha_color.get(key, "black"),
            ),
            row=2,
            col=1,
        )

    bar_offset = 1 / len(bars)
    for i, key in enumerate(bars):
        fig.add_trace(
            go.Bar(
                x=[t + timedelta(hours=i * bar_offset + 0.125) for t in times],
                y=[-v if key in inverted else v for v in ts[key]],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
                opacity=0.8,
            ),
            row=2,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=times,
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
            x=times,
            y=ts["sell_price"],
            name=labels["sell_price"],
            line_shape="hv",
            mode="lines",
            marker_color=ha_color["sell_price"],
        ),
        row=3,
        col=1,
    )
    if heating_enabled:
        fig.add_trace(
            go.Scatter(
                x=times,
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
                x=times,
                y=ts["outdoor_temps"],
                name=labels["outdoor_temps"],
                mode="lines",
                marker_color=ha_color["outdoor_temps"],
            ),
            row=4,
            col=1,
        )

    fig.update_yaxes(title_text="Energie [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]", row=3, col=1)
    if heating_enabled:
        fig.update_yaxes(title_text="kWh, °C", row=4, col=1)

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")