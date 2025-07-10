"""
HomeOptim - Refactored Presentation Layer
Modern visualization module for energy optimization dashboard
"""

from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.io as pio
from datetime import timedelta, datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from actions import mpc_to_actions_timeline


@dataclass
class ChartTheme:
    """Centralizované téma pro všechny grafy"""
    # Hlavní barvy
    PRIMARY = "#3B82F6"
    SECONDARY = "#8B5CF6" 
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    INFO = "#06B6D4"
    
    # Specifické barvy pro komponenty
    BATTERY_SOC = "#4db6ac"
    BATTERY_DISCHARGE = "#10B981"
    BATTERY_CHARGE = "#EF4444"
    
    HEATING_LOWER = "#c2185b"
    HEATING_UPPER = "#e91e63"
    HEATING_OUTPUT_LOWER = "#00796b"
    HEATING_OUTPUT_UPPER = "#004d40"
    HEATING_TRANSFER = "#ff69e6"
    
    GRID_BUY = "#488fc2"
    GRID_SELL = "#8353d1"
    
    PV_PRODUCTION = "#ff9800"
    LOAD_CONSUMPTION = "#488fc2"
    
    PRICE_BUY = "#488fc2"
    PRICE_SELL = "#8353d1"
    
    TEMPERATURE_OUTDOOR = "#ff9800"
    TEMPERATURE_LOWER = "#ff8f00"
    TEMPERATURE_UPPER = "#ffc107"
    
    # Režimy střídače
    MODE_SELF_USE = "#4db6ac"
    MODE_BACKUP = "#0f9d58"
    MODE_FEEDIN = "#8353d1"
    MODE_MANUAL = "#f06292"
    
    # Akce
    ACTION_UPPER_ACCUMULATION = "#c97a94"
    ACTION_LOWER_ACCUMULATION = "#0f9d58"
    ACTION_MAX_HEAT = "#ff9800"
    ACTION_HEATING_BLOCKED = "#f44336"
    ACTION_FVE_SURPLUS = "#ffeb3b"
    ACTION_BATTERY_RESERVE = "#4db6ac"


@dataclass
class ChartConfig:
    """Konfigurace pro jednotlivé grafy"""
    height: int = 400
    show_legend: bool = True
    responsive: bool = True
    margin: Dict[str, int] = None
    
    def __post_init__(self):
        if self.margin is None:
            self.margin = dict(l=50, r=50, t=80, b=50)


class DataProcessor:
    """Třída pro zpracování dat pro vizualizaci"""
    
    @staticmethod
    def prepare_time_series(solution: Dict[str, Any]) -> Dict[str, Any]:
        """Připraví časové řady pro vizualizaci"""
        times = [datetime.fromisoformat(t) for t in solution["times"]]
        ts = {**solution["inputs"], **solution["outputs"]}
        
        # Kategorizace dat
        soc_keys = ["b_soc_percent", "h_soc_lower_percent", "h_soc_upper_percent"]
        power_keys = ["h_in_lower", "h_in_upper", "h_out_lower", "h_out_upper", "fve_pred", "load_pred"]
        inverted_keys = ["g_sell", "h_out_lower", "h_out_upper", "b_discharge"]
        bar_keys = ["b_charge", "b_discharge", "g_buy", "g_sell", "h_to_upper"]
        
        options = solution.get("options", {})
        heating_enabled = options.get("heating_enabled", False)
        
        actions_timeline = mpc_to_actions_timeline(solution)
        
        return {
            'times': times,
            'ts': ts,
            'soc_keys': soc_keys,
            'power_keys': power_keys,
            'inverted_keys': inverted_keys,
            'bar_keys': bar_keys,
            'heating_enabled': heating_enabled,
            'actions_timeline': actions_timeline,
            'options': options
        }


class ChartFactory:
    """Továrna pro vytváření různých typů grafů"""
    
    def __init__(self, theme: ChartTheme = None):
        self.theme = theme or ChartTheme()
        self.labels = self._create_labels()
        self.color_map = self._create_color_map()
    
    def _create_labels(self) -> Dict[str, str]:
        """Vytvoří mapu labelů pro jednotlivé metriky"""
        return {
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
            "h_soc_lower_percent": "SoC dolní zóny (%)",
            "h_soc_upper_percent": "SoC horní zóny (%)",
            "temp_lower": "Teplota dolní zóny",
            "temp_upper": "Teplota horní zóny",
            "charger_mode": "Režim střídače",
            "upper_accumulation": "Horní akumulace",
            "lower_accumulation": "Spodní akumulace",
            "max_heat": "Maximální ohřev", 
            "heating_blocked": "Ohřev blokován",
            "fve_surplus": "FVE přebytek",
            "battery_reserve": "Rezerva baterie",
            "charger_mode_self": "Self Use",
            "charger_mode_backup": "Back Up Mode",
            "charger_mode_feedin": "Feedin Priority",
            "charger_mode_manual": "Manual",
        }
    
    def _create_color_map(self) -> Dict[str, str]:
        """Vytvoří mapu barev pro jednotlivé metriky"""
        return {
            "b_soc_percent": self.theme.BATTERY_SOC,
            "h_soc_percent": self.theme.WARNING,
            "b_power": self.theme.BATTERY_SOC,
            "b_charge": self.theme.BATTERY_CHARGE,
            "b_discharge": self.theme.BATTERY_DISCHARGE,
            "h_in": self.theme.HEATING_LOWER,
            "g_buy": self.theme.GRID_BUY,
            "g_sell": self.theme.GRID_SELL,
            "h_out": self.theme.SUCCESS,
            "fve_pred": self.theme.PV_PRODUCTION,
            "load_pred": self.theme.LOAD_CONSUMPTION,
            "buy_price": self.theme.PRICE_BUY,
            "sell_price": self.theme.PRICE_SELL,
            "heating_demand": self.theme.SUCCESS,
            "outdoor_temps": self.theme.TEMPERATURE_OUTDOOR,
            "h_in_lower": self.theme.HEATING_LOWER,
            "h_in_upper": self.theme.HEATING_UPPER,
            "h_out_lower": self.theme.HEATING_OUTPUT_LOWER,
            "h_out_upper": self.theme.HEATING_OUTPUT_UPPER,
            "h_to_upper": self.theme.HEATING_TRANSFER,
            "h_soc_lower": self.theme.TEMPERATURE_LOWER,
            "h_soc_upper": self.theme.TEMPERATURE_UPPER,
            "h_soc_lower_percent": self.theme.TEMPERATURE_LOWER,
            "h_soc_upper_percent": self.theme.TEMPERATURE_UPPER,
            "temp_lower": self.theme.TEMPERATURE_LOWER,
            "temp_upper": self.theme.TEMPERATURE_UPPER,
            "charger_mode_self": self.theme.MODE_SELF_USE,
            "charger_mode_backup": self.theme.MODE_BACKUP,
            "charger_mode_feedin": self.theme.MODE_FEEDIN,
            "charger_mode_manual": self.theme.MODE_MANUAL,
            "upper_accumulation": self.theme.ACTION_UPPER_ACCUMULATION,
            "lower_accumulation": self.theme.ACTION_LOWER_ACCUMULATION,
            "max_heat": self.theme.ACTION_MAX_HEAT,
            "heating_blocked": self.theme.ACTION_HEATING_BLOCKED,
            "fve_surplus": self.theme.ACTION_FVE_SURPLUS,
            "battery_reserve": self.theme.ACTION_BATTERY_RESERVE,
        }

    def create_overview_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Vytvoří přehledový graf s nejdůležitějšími metrikami"""
        config = config or ChartConfig(height=600)
        
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                "📊 Stavy baterie a bojleru (%)",
                "⚡ Klíčové výkony (kW)", 
                "🎯 Režim střídače a akce"
            ),
        )

        # Stavy SoC
        for key in data['soc_keys']:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=[t + timedelta(hours=1) for t in data['times']],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        marker_color=self.color_map.get(key, self.theme.PRIMARY),
                        line=dict(width=3),
                        mode='lines',
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Hodnota: %{y:.1f}%<br>" +
                                    "<extra></extra>"
                    ),
                    row=1,
                    col=1,
                )

        # Hlavní výkony
        main_power_keys = data['power_keys'][:4]  # Jen nejdůležitější
        for key in main_power_keys:
            if key in data['ts']:
                y_values = [-v if key in data['inverted_keys'] else v for v in data['ts'][key]]
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=y_values,
                        name=self.labels.get(key, key),
                        line_shape="hv",
                        mode="lines",
                        marker_color=self.color_map.get(key, self.theme.SECONDARY),
                        line=dict(width=2),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Výkon: %{y:.2f} kW<br>" +
                                    "<extra></extra>"
                    ),
                    row=2,
                    col=1,
                )
        
        # Režimy střídače
        self._add_charger_modes(fig, data, row=3)

        # Konfigurace os
        fig.update_yaxes(title_text="SoC [%]", row=1, col=1)
        fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
        fig.update_yaxes(title_text="Režim", row=3, col=1)

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            showlegend=config.show_legend,
            title="🏠 Přehled energetické optimalizace",
            title_x=0.5,
            title_font_size=20,
            autosize=True,
        )

        return self._render_chart(fig, config)

    def create_states_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Graf stavů baterie a bojleru"""
        config = config or ChartConfig()
        
        fig = go.Figure()

        # SoC v procentech
        for key in data['soc_keys']:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=[t + timedelta(hours=1) for t in data['times']],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        marker_color=self.color_map.get(key, self.theme.PRIMARY),
                        line=dict(width=3),
                        mode='lines+markers',
                        marker=dict(size=4),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "SoC: %{y:.1f}%<br>" +
                                    "<extra></extra>"
                    )
                )
        
        # SoC v kWh (čárkované čáry)
        energy_keys = ["h_soc_lower", "h_soc_upper"]
        for key in energy_keys:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=[t + timedelta(hours=1) for t in data['times']],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        line_dash="dot",
                        marker_color=self.color_map.get(key, self.theme.SECONDARY),
                        line=dict(width=2),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Energie: %{y:.2f} kWh<br>" +
                                    "<extra></extra>"
                    )
                )

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="🔋 Stavy energetických úložišť",
            title_x=0.5,
            title_font_size=16,
            yaxis_title="SoC [%] / Energie [kWh]",
            xaxis_title="Čas",
            autosize=True,
            showlegend=config.show_legend
        )

        return self._render_chart(fig, config)

    def create_power_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Graf výkonů a energetických toků"""
        config = config or ChartConfig(height=500)
        
        fig = go.Figure()

        # Výkonové křivky
        for key in data['power_keys']:
            if key in data['ts']:
                y_values = [-v if key in data['inverted_keys'] else v for v in data['ts'][key]]
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=y_values,
                        name=self.labels.get(key, key),
                        line_shape="hv",
                        mode="lines",
                        marker_color=self.color_map.get(key, self.theme.PRIMARY),
                        line=dict(width=2),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Výkon: %{y:.2f} kW<br>" +
                                    "<extra></extra>"
                    )
                )

        # Sloupcové grafy pro toky energie
        self._add_energy_bars(fig, data)

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="⚡ Výkony a energetické toky",
            title_x=0.5,
            title_font_size=16,
            yaxis_title="Výkon [kW]",
            xaxis_title="Čas",
            autosize=True,
            showlegend=config.show_legend
        )

        return self._render_chart(fig, config)

    def create_prices_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Graf cen elektřiny"""
        config = config or ChartConfig(height=350)
        
        fig = go.Figure()

        price_keys = ["buy_price", "sell_price"]
        for key in price_keys:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        line_shape="hv",
                        mode="lines+markers",
                        marker_color=self.color_map.get(key, self.theme.PRIMARY),
                        line=dict(width=3),
                        marker=dict(size=6),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Cena: %{y:.2f} Kč/kWh<br>" +
                                    "<extra></extra>"
                    )
                )

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="💰 Ceny elektřiny",
            title_x=0.5,
            title_font_size=16,
            yaxis_title="Cena [Kč/kWh]",
            xaxis_title="Čas",
            autosize=True,
            showlegend=config.show_legend
        )

        return self._render_chart(fig, config)

    def create_heating_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Graf tepelných ztrát a teplot"""
        config = config or ChartConfig()
        
        fig = go.Figure()

        # Tepelné ztráty a venkovní teplota
        environmental_keys = ["heating_demand", "outdoor_temps"]
        for key in environmental_keys:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        mode="lines",
                        marker_color=self.color_map.get(key, self.theme.WARNING),
                        line=dict(width=2),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Hodnota: %{y:.2f}<br>" +
                                    "<extra></extra>"
                    )
                )
        
        # Teploty z MPC výstupů
        temp_keys = ["temp_lower", "temp_upper"]
        dash_styles = ["dash", "dot"]
        for i, key in enumerate(temp_keys):
            if key in data['ts'] and data['ts'][key]:
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=data['ts'][key],
                        name=self.labels.get(key, key),
                        line_dash=dash_styles[i],
                        marker_color=self.color_map.get(key, self.theme.SECONDARY),
                        line=dict(width=2),
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Teplota: %{y:.1f}°C<br>" +
                                    "<extra></extra>"
                    )
                )

        # Sloupcový graf přenosu výkonu (dolní→horní)
        key = "h_to_upper"
        if key in data['ts']:
            # invert values so transfer appears upward
            y_values = [-v for v in data['ts'][key]]
            fig.add_trace(
                go.Bar(
                    x=data['times'],
                    y=y_values,
                    name=self.labels.get(key, key),
                    marker_color=self.color_map.get(key, self.theme.HEATING_TRANSFER),
                    opacity=0.7,
                    width=3600000/5,  # tenké sloupce, 1/5 kroku
                    yaxis="y2",  # use secondary y-axis
                    hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                  "Čas: %{x}<br>" +
                                  "Výkon: %{y:.2f} kW<br>" +
                                  "<extra></extra>"
                )
            )

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="🌡️ Teploty a tepelné ztráty",
            title_x=0.5,
            title_font_size=16,
            yaxis=dict(title="Teplota [°C] / Ztráty [kWh]"),  # primary axis
            yaxis2=dict(title="Přenos výkonu [kW]", overlaying="y", side="right"),  # secondary axis
            xaxis_title="Čas",
            autosize=True,
            showlegend=config.show_legend
        )

        return self._render_chart(fig, config)

    def create_actions_chart(self, data: Dict[str, Any], config: ChartConfig = None) -> str:
        """Graf plánovaných akcí a optimalizací"""
        config = config or ChartConfig(height=500)
        
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.12,
            subplot_titles=(
                "🔄 Režimy střídače a FVE přebytek",
                "🔥 Akce ohřevu a rezervovaný výkon"
            ),
        )

        # Graf 1: Režimy střídače
        self._add_charger_modes(fig, data, row=1)
        
        # FVE přebytek
        self._add_fve_surplus(fig, data, row=1)
        
        # Graf 2: Akce ohřevu  
        self._add_heating_actions(fig, data, row=2)
        
        # Rezervovaný výkon
        self._add_battery_reserve(fig, data, row=2)

        fig.update_yaxes(title_text="Aktivní", row=1, col=1)
        fig.update_yaxes(title_text="Aktivní", row=2, col=1)

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="🎯 Plán akcí a optimalizace",
            title_x=0.5,
            title_font_size=16,
            showlegend=config.show_legend,
            autosize=True
        )

        return self._render_chart(fig, config)

    def _add_charger_modes(self, fig: go.Figure, data: Dict[str, Any], row: int = 1):
        """Přidá režimy střídače do grafu"""
        actions = data['actions_timeline']
        charger_modes = ["Self Use", "Back Up Mode", "Feedin Priority", "Manual"]
        mode_colors = [self.theme.MODE_SELF_USE, self.theme.MODE_BACKUP, 
                      self.theme.MODE_FEEDIN, self.theme.MODE_MANUAL]
        
        # Přidání podbarvení podle režimu
        for i, mode in enumerate(charger_modes):
            # Parse hex color to rgba with transparency
            hex_color = mode_colors[i]
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            fill_color = f"rgba({r},{g},{b},0.2)"
            y_area = [1 if m == mode else 0 for m in actions["charger_mode"]]
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=y_area,
                    mode='none',
                    fill='tozeroy',
                    fillcolor=fill_color,
                    showlegend=False
                ),
                row=row,
                col=1,
            )

        # Původní body
        for i, mode in enumerate(charger_modes):
            mode_values = [i+1 if m == mode else None for m in actions["charger_mode"]]
            if any(v for v in mode_values if v is not None):
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=mode_values,
                        name=mode,
                        mode="markers",
                        marker=dict(
                            size=12,
                            color=mode_colors[i],
                            symbol="square"
                        ),
                        hovertemplate=f"<b>{mode}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "<extra></extra>"
                    ),
                    row=row,
                    col=1,
                )

    def _add_fve_surplus(self, fig: go.Figure, data: Dict[str, Any], row: int = 1):
        """Přidá FVE přebytek do grafu"""
        actions = data['actions_timeline']
        if 'fve_surplus' in actions and actions['fve_surplus']:
            max_surplus = max(actions["fve_surplus"]) if max(actions["fve_surplus"]) > 0 else 1
            normalized_surplus = [s/max_surplus for s in actions["fve_surplus"]]
            
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=normalized_surplus,
                    name=f"FVE přebytek (max: {max_surplus:.1f} kW)",
                    mode="lines",
                    line_shape="hv",
                    marker_color=self.theme.ACTION_FVE_SURPLUS,
                    line_dash="dot",
                    customdata=actions["fve_surplus"],
                    hovertemplate="<b>FVE přebytek</b><br>" +
                                "Čas: %{x}<br>" +
                                "Přebytek: %{customdata:.2f} kW<br>" +
                                "<extra></extra>",
                ),
                row=row,
                col=1,
            )

    def _add_heating_actions(self, fig: go.Figure, data: Dict[str, Any], row: int = 2):
        """Přidá akce ohřevu do grafu"""
        actions = data['actions_timeline']
        heating_actions = [
            ("upper_accumulation", "Horní akumulace", self.theme.ACTION_UPPER_ACCUMULATION),
            ("lower_accumulation", "Spodní akumulace", self.theme.ACTION_LOWER_ACCUMULATION),
            ("max_heat", "Maximální ohřev", self.theme.ACTION_MAX_HEAT),
            ("heating_blocked", "Ohřev blokován", self.theme.ACTION_HEATING_BLOCKED),
        ]
        
        for action_key, action_name, color in heating_actions:
            if action_key in actions:
                action_values = [1 if a else None for a in actions[action_key]]
                if any(v for v in action_values if v is not None):
                    fig.add_trace(
                        go.Scatter(
                            x=data['times'],
                            y=action_values,
                            name=action_name,
                            mode="markers",
                            marker=dict(
                                size=10,
                                color=color,
                                symbol="diamond"
                            ),
                            hovertemplate=f"<b>{action_name}</b><br>" +
                                        "Čas: %{x}<br>" +
                                        "<extra></extra>"
                        ),
                        row=row,
                        col=1,
                    )

    def _add_battery_reserve(self, fig: go.Figure, data: Dict[str, Any], row: int = 2):
        """Přidá rezervovaný výkon baterie do grafu"""
        actions = data['actions_timeline']
        if 'reserve_power' in actions and actions['reserve_power']:
            max_reserve = max(actions["reserve_power"]) if max(actions["reserve_power"]) > 0 else 1000
            normalized_reserve = [r/max_reserve for r in actions["reserve_power"]]
            
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=normalized_reserve,
                    name=f"Rezerva baterie (max: {max_reserve/1000:.1f} kW)",
                    mode="lines",
                    line_shape="hv",
                    marker_color=self.theme.ACTION_BATTERY_RESERVE,
                    line_dash="dash",
                    customdata=actions["reserve_power"],
                    hovertemplate="<b>Rezervovaný výkon</b><br>" +
                                "Čas: %{x}<br>" +
                                "Výkon: %{customdata:.0f} W<br>" +
                                "<extra></extra>",
                ),
                row=row,
                col=1,
            )

    def _add_energy_bars(self, fig: go.Figure, data: Dict[str, Any]):
        """Přidá sloupcové grafy pro energetické toky"""
        bar_keys = data['bar_keys']
        bar_offset = 1 / len(bar_keys)
        
        for i, key in enumerate(bar_keys):
            if key in data['ts']:
                offset_times = [t + timedelta(minutes=i*10) for t in data['times']]
                y_values = [-v if key in data['inverted_keys'] else v for v in data['ts'][key]]
                
                fig.add_trace(
                    go.Bar(
                        x=offset_times,
                        y=y_values,
                        name=self.labels.get(key, key),
                        marker_color=self.color_map.get(key, self.theme.SECONDARY),
                        opacity=0.7,
                        width=bar_offset * 3600000,  # Convert to milliseconds
                        hovertemplate=f"<b>{self.labels.get(key, key)}</b><br>" +
                                    "Čas: %{x}<br>" +
                                    "Výkon: %{y:.2f} kW<br>" +
                                    "<extra></extra>"
                    )
                )

    def _render_chart(self, fig: go.Figure, config: ChartConfig) -> str:
        """Vykreslí graf do HTML"""
        return pio.to_html(
            fig, 
            full_html=False, 
            include_plotlyjs="cdn",
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                'responsive': config.responsive,
                'fillFrame': True,
                'frameMargins': 0
            }
        )


# Hlavní API funkce pro zpětnou kompatibilitu
def presentation(solution: Dict[str, Any]) -> Dict[str, str]:
    """
    Hlavní funkce pro vytvoření všech grafů
    Vrací slovník s HTML reprezentacemi jednotlivých grafů
    """
    # Zpracování dat
    data = DataProcessor.prepare_time_series(solution)
    
    # Vytvoření továrny grafů
    chart_factory = ChartFactory()
    
    # Vytvoření jednotlivých grafů
    graphs = {}
    
    # Graf 1: Přehled - kombinovaný graf nejdůležitějších metrik
    graphs['overview'] = chart_factory.create_overview_chart(data, ChartConfig(height=600))
    
    # Graf 2: Stavy baterie a bojleru
    graphs['states'] = chart_factory.create_states_chart(data, ChartConfig(height=400))
    
    # Graf 3: Výkony a energie
    graphs['power'] = chart_factory.create_power_chart(data, ChartConfig(height=500))
    
    # Graf 4: Ceny elektřiny
    graphs['prices'] = chart_factory.create_prices_chart(data, ChartConfig(height=350))
    
    # Graf 5: Teploty a tepelné ztráty
    if data['heating_enabled'] or True:  # Always show for now
        graphs['heating'] = chart_factory.create_heating_chart(data, ChartConfig(height=400))
    
    # Graf 6: Plán akcí - removed per user request
    # graphs['actions'] = chart_factory.create_actions_chart(data, ChartConfig(height=500))

    return graphs


def presentation_single(solution: Dict[str, Any]) -> str:
    """
    Původní funkce pro jeden velký graf - refactored
    Zachována pro zpětnou kompatibilitu
    """
    data = DataProcessor.prepare_time_series(solution)
    chart_factory = ChartFactory()
    
    # Vytvoření jediného velkého grafu se všemi subploty
    fig = make_subplots(
        rows=6 if data['heating_enabled'] or True else 5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            "📊 Stavy energetických úložišť (SoC)",
            "⚡ Výkony a energetické toky",
            "💰 Ceny elektřiny",
            "🌡️ Tepelné ztráty a venkovní teplota",
            "🔄 Plán režimů střídače",
            "🎯 Plán akcí ohřevu a optimalizace",
        ),
    )

    # Stavy SoC
    for key in data['soc_keys']:
        if key in data['ts']:
            fig.add_trace(
                go.Scatter(
                    x=[t + timedelta(hours=1) for t in data['times']],
                    y=data['ts'][key],
                    name=chart_factory.labels.get(key, key),
                    marker_color=chart_factory.color_map.get(key, chart_factory.theme.PRIMARY),
                    line=dict(width=2),
                ),
                row=1,
                col=1,
            )
    
    # Přidání zónových SoC (kWh)
    for key in ["h_soc_lower", "h_soc_upper"]:
        if key in data['ts']:
            fig.add_trace(
                go.Scatter(
                    x=[t + timedelta(hours=1) for t in data['times']],
                    y=data['ts'][key],
                    name=chart_factory.labels.get(key, key),
                    line_dash="dot",
                    marker_color=chart_factory.color_map.get(key, chart_factory.theme.SECONDARY),
                ),
                row=1,
                col=1,
            )

    # Výkony
    for key in data['power_keys']:
        if key in data['ts']:
            y_values = [-v if key in data['inverted_keys'] else v for v in data['ts'][key]]
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=y_values,
                    name=chart_factory.labels.get(key, key),
                    line_shape="hv",
                    mode="lines",
                    marker_color=chart_factory.color_map.get(key, chart_factory.theme.PRIMARY),
                ),
                row=2,
                col=1,
            )

    # Sloupcové grafy pro toky energie
    bar_offset = 1 / len(data['bar_keys'])
    for i, key in enumerate(data['bar_keys']):
        if key in data['ts']:
            offset_times = [t + timedelta(minutes=i*10) for t in data['times']]
            y_values = [-v if key in data['inverted_keys'] else v for v in data['ts'][key]]
            fig.add_trace(
                go.Bar(
                    x=offset_times,
                    y=y_values,
                    name=chart_factory.labels.get(key, key),
                    marker_color=chart_factory.color_map.get(key, chart_factory.theme.SECONDARY),
                    opacity=0.7,
                    width=bar_offset * 3600000,
                ),
                row=2,
                col=1,
            )

    # Ceny elektřiny
    for key in ["buy_price", "sell_price"]:
        if key in data['ts']:
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=data['ts'][key],
                    name=chart_factory.labels.get(key, key),
                    line_shape="hv",
                    mode="lines",
                    marker_color=chart_factory.color_map.get(key, chart_factory.theme.PRIMARY),
                ),
                row=3,
                col=1,
            )
    
    # Teploty a tepelné ztráty
    if data['heating_enabled'] or True:
        for key in ["heating_demand", "outdoor_temps"]:
            if key in data['ts']:
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=data['ts'][key],
                        name=chart_factory.labels.get(key, key),
                        mode="lines",
                        marker_color=chart_factory.color_map.get(key, chart_factory.theme.WARNING),
                    ),
                    row=4,
                    col=1,
                )
        
        for key in ["temp_lower", "temp_upper"]:
            if key in data['ts'] and data['ts'][key]:
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=data['ts'][key],
                        name=chart_factory.labels.get(key, key),
                        line_dash="dash",
                        marker_color=chart_factory.color_map.get(key, chart_factory.theme.SECONDARY),
                    ),
                    row=4,
                    col=1,
                )

    # Režimy střídače
    actions = data['actions_timeline']
    charger_modes = ["Self Use", "Back Up Mode", "Feedin Priority", "Manual"]
    mode_colors = [chart_factory.theme.MODE_SELF_USE, chart_factory.theme.MODE_BACKUP, 
                  chart_factory.theme.MODE_FEEDIN, chart_factory.theme.MODE_MANUAL]
    
    for i, mode in enumerate(charger_modes):
        mode_values = [i+1 if m == mode else None for m in actions["charger_mode"]]
        if any(v for v in mode_values if v is not None):
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=mode_values,
                    name=mode,
                    mode="markers",
                    marker=dict(size=8, color=mode_colors[i], symbol="square"),
                ),
                row=5,
                col=1,
            )
    
    # FVE přebytek
    if 'fve_surplus' in actions and actions['fve_surplus']:
        max_surplus = max(actions["fve_surplus"]) if max(actions["fve_surplus"]) > 0 else 1
        normalized_surplus = [s/max_surplus for s in actions["fve_surplus"]]
        
        fig.add_trace(
            go.Scatter(
                x=data['times'],
                y=normalized_surplus,
                name=f"FVE přebytek (max: {max_surplus:.1f} kW)",
                mode="lines",
                line_shape="hv",
                marker_color=chart_factory.theme.ACTION_FVE_SURPLUS,
                line_dash="dot",
            ),
            row=5,
            col=1,
        )
    
    # Akce ohřevu
    heating_actions = [
        ("upper_accumulation", "Horní akumulace", chart_factory.theme.ACTION_UPPER_ACCUMULATION),
        ("lower_accumulation", "Spodní akumulace", chart_factory.theme.ACTION_LOWER_ACCUMULATION), 
        ("max_heat", "Maximální ohřev", chart_factory.theme.ACTION_MAX_HEAT),
        ("heating_blocked", "Ohřev blokován", chart_factory.theme.ACTION_HEATING_BLOCKED),
    ]
    
    for action_key, action_name, color in heating_actions:
        if action_key in actions:
            action_values = [1 if a else None for a in actions[action_key]]
            if any(v for v in action_values if v is not None):
                fig.add_trace(
                    go.Scatter(
                        x=data['times'],
                        y=action_values,
                        name=action_name,
                        mode="markers",
                        marker=dict(size=6, color=color, symbol="diamond"),
                    ),
                    row=6,
                    col=1,
                )
    
    # Rezervovaný výkon
    if 'reserve_power' in actions and actions['reserve_power']:
        max_reserve = max(actions["reserve_power"]) if max(actions["reserve_power"]) > 0 else 1000
        normalized_reserve = [r/max_reserve for r in actions["reserve_power"]]
        
        fig.add_trace(
            go.Scatter(
                x=data['times'],
                y=normalized_reserve,
                name=f"Rezervovaný výkon (max: {max_reserve/1000:.1f} kW)",
                mode="lines",
                line_shape="hv",
                marker_color=chart_factory.theme.ACTION_BATTERY_RESERVE,
                line_dash="dash",
            ),
            row=6,
            col=1,
        )
    
    # Konfigurace os
    fig.update_yaxes(title_text="Energie [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]", row=3, col=1)
    fig.update_yaxes(title_text="kWh, °C", row=4, col=1)
    fig.update_yaxes(title_text="Aktivní", side="left", row=5, col=1)
    fig.update_yaxes(title_text="Aktivní", side="left", row=6, col=1)

    fig.update_layout(
        height=900,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=True,
        title="🏠 HomeOptim - Kompletní energetická analýza",
        title_x=0.5,
        title_font_size=24,
        legend=dict(
            orientation="h",
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


# Zpětná kompatibilita - zachování starých názvů
def create_color_compatibility():
    """Vytvoří zpětnou kompatibilitu pro starý ha_color slovník"""
    theme = ChartTheme()
    return {
        "b_soc_percent": theme.BATTERY_SOC,
        "h_soc_percent": theme.WARNING,
        "b_power": theme.BATTERY_SOC,
        "b_charge": theme.BATTERY_CHARGE,
        "b_discharge": theme.BATTERY_DISCHARGE,
        "h_in": theme.HEATING_LOWER,
        "g_buy": theme.GRID_BUY,
        "g_sell": theme.GRID_SELL,
        "h_out": theme.SUCCESS,
        "fve_pred": theme.PV_PRODUCTION,
        "load_pred": theme.LOAD_CONSUMPTION,
        "buy_price": theme.PRICE_BUY,
        "sell_price": theme.PRICE_SELL,
        "heating_demand": theme.SUCCESS,
        "outdoor_temps": theme.TEMPERATURE_OUTDOOR,
        "h_in_lower": theme.HEATING_LOWER,
        "h_in_upper": theme.HEATING_UPPER,
        "h_out_lower": theme.HEATING_OUTPUT_LOWER,
        "h_out_upper": theme.HEATING_OUTPUT_UPPER,
        "h_to_upper": theme.HEATING_TRANSFER,
        "h_soc_lower": theme.TEMPERATURE_LOWER,
        "h_soc_upper": theme.TEMPERATURE_UPPER,
        "h_soc_lower_percent": theme.TEMPERATURE_LOWER,
        "h_soc_upper_percent": theme.TEMPERATURE_UPPER,
        "temp_lower": theme.TEMPERATURE_LOWER,
        "temp_upper": theme.TEMPERATURE_UPPER,
        "charger_mode_self": theme.MODE_SELF_USE,
        "charger_mode_backup": theme.MODE_BACKUP,
        "charger_mode_feedin": theme.MODE_FEEDIN,
        "charger_mode_manual": theme.MODE_MANUAL,
        "upper_accumulation": theme.ACTION_UPPER_ACCUMULATION,
        "lower_accumulation": theme.ACTION_LOWER_ACCUMULATION,
        "max_heat": theme.ACTION_MAX_HEAT,
        "heating_blocked": theme.ACTION_HEATING_BLOCKED,
        "fve_surplus": theme.ACTION_FVE_SURPLUS,
        "battery_reserve": theme.ACTION_BATTERY_RESERVE,
    }

# Pro zpětnou kompatibilitu
ha_color = create_color_compatibility()
labels = ChartFactory().labels
