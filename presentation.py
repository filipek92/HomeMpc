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
    "h_in_lower": "#c2185b",
    "h_in_upper": "#e91e63",
    "h_out_lower": "#00796b",
    "h_out_upper": "#004d40",
    "h_to_upper": "#ff69e6",
    "h_soc_lower": "#ff8f00",
    "h_soc_upper": "#ffc107",
    "h_soc_lower_percent": "#ff8f00",
    "h_soc_upper_percent": "#ffc107",
    # teplotní průběhy
    "temp_lower": "#ff8f00",
    "temp_upper": "#ffc107",
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
    "h_in_lower": "Ohřev dolní zóny",
    "h_in_upper": "Ohřev horní zóny",
    "h_out_lower": "Odběr topení (dolní)",
    "h_out_upper": "Odběr TUV (horní)",
    "h_to_upper": "Přenos dolní→horní",
    "h_soc_lower": "SoC dolní zóny",
    "h_soc_upper": "SoC horní zóny",
    "h_soc_lower_percent": "SoC dolní zóny",
    "h_soc_upper_percent": "SoC horní zóny",
    # teploty z dvou zón
    "temp_lower": "Teplota dolní zóny",
    "temp_upper": "Teplota horní zóny",
}

def presentation(solution):
    times = [datetime.fromisoformat(t) for t in solution["times"]]

    ts = {**solution["inputs"], **solution["outputs"]}

    socs = ["b_soc_percent", "h_soc_lower_percent", "h_soc_upper_percent"]
    inverted = ["g_sell", "h_out_lower", "h_out_upper", "b_discharge"]
    steps = ["h_in_lower", "h_in_upper", "h_out_lower", "h_out_upper", "fve_pred", "load_pred"]
    bars = ["b_charge", "b_discharge", "g_buy", "g_sell", "h_to_upper"]

    options = solution.get("options", {})
    heating_enabled = options.get("heating_enabled", False)

    fig = make_subplots(
        rows=4 if heating_enabled or True else 3,
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
    # Přidání zónových SoC (kWh)
    for key in ["h_soc_lower", "h_soc_upper"]:
        fig.add_trace(
            go.Scatter(
                x=[t + timedelta(hours=1) for t in times],
                y=ts[key],
                name=labels.get(key, key),
                line_dash="dot",
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
    if heating_enabled or True:
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
        # Teploty z výstupů MPC
        fig.add_trace(
            go.Scatter(
                x=times,
                y=ts.get("temp_lower", []),
                name=labels.get("temp_lower", "temp_lower"),
                line_dash="dash",
                marker_color=ha_color.get("temp_lower", "black"),
            ),
            row=4,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=times,
                y=ts.get("temp_upper", []),
                name=labels.get("temp_upper", "temp_upper"),
                line_dash="dot",
                marker_color=ha_color.get("temp_upper", "black"),
            ),
            row=4,
            col=1,
        )

    fig.update_yaxes(title_text="Energie [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]", row=3, col=1)
    if heating_enabled:
        fig.update_yaxes(title_text="kWh, °C", row=4, col=1)

    # Nastavení výšky grafu pro lepší čitelnost
    fig.update_layout(
        height=650,  # Celková výška grafu
        margin=dict(l=50, r=50, t=80, b=50),  # Okraje
        showlegend=True,
        legend=dict(
            orientation="h",  # Horizontální legenda
            yanchor="bottom",
            y=1.02,
            xanchor="right", 
            x=1
        )
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
        'responsive': True
    })