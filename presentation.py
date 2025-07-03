from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.io as pio
from datetime import timedelta, datetime

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

def presentation(hours, ts, outdoor_temps):
    SOCs = ["B_SOC_percent", "H_SOC_percent"]
    inverted = ["G_sell", "H_out", "B_discharge"]
    steps = ["H_in", "H_out", "fve", "load"]
    bars = ["B_charge", "B_discharge", "G_sell", "G_buy"]

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

    bar_offset = 1 / (len(bars) + 1)
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

    fig.update_yaxes(title_text="Energie [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]", row=3, col=1)
    fig.update_yaxes(title_text="kWh, °C", row=4, col=1)

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")