"""
HomeOptim - Presentation Layer
Refactored visualization module for energy optimization dashboard
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
    BATTERY_CHARGE = "#10B981"
    BATTERY_DISCHARGE = "#EF4444"
    
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

        fig.update_layout(
            height=config.height,
            margin=config.margin,
            title="🌡️ Teploty a tepelné ztráty",
            title_x=0.5,
            title_font_size=16,
            yaxis_title="Teplota [°C] / Ztráty [kWh]",
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
            go.Scatter(
                x=[t + timedelta(hours=1) for t in times],
                y=ts[key],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
                line=dict(width=2),
            ),
            row=1,
            col=1,
        )

    # Hlavní výkony (jen nejdůležitější)
    inverted = ["g_sell", "h_out_lower", "h_out_upper", "b_discharge"]
    for key in main_steps:
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
    
    # Režimy střídače jako barevné bloky
    charger_modes = ["Self Use", "Back Up Mode", "Feedin Priority", "Manual"]
    mode_colors = ["#4db6ac", "#0f9d58", "#8353d1", "#f06292"]
    
    for i, mode in enumerate(charger_modes):
        mode_values = [i+1 if m == mode else None for m in actions_timeline["charger_mode"]]
        if any(v for v in mode_values if v is not None):
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=mode_values,
                    name=f"Režim: {mode}",
                    mode="lines",
                    line_shape="hv",
                    marker_color=mode_colors[i],
                    line=dict(width=4),
                ),
                row=3,
                col=1,
            )

    fig.update_yaxes(title_text="SoC [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Režim", row=3, col=1)

    fig.update_layout(
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=True,
        title="🏠 Přehled optimalizace",
        autosize=True,
        width=None
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
        'responsive': True,
        'fillFrame': True,
        'frameMargins': 0
    })

def create_states_graph(times, ts, socs):
    """Graf stavů baterie a bojleru"""
    fig = go.Figure()

    for key in socs:
        fig.add_trace(
            go.Scatter(
                x=[t + timedelta(hours=1) for t in times],
                y=ts[key],
                name=labels.get(key, key),
                marker_color=ha_color.get(key, "black"),
                line=dict(width=3),
            )
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
            )
        )

    fig.update_layout(
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        title="🔋 Stavy baterie a bojleru",
        yaxis_title="SoC [%] / Energie [kWh]",
        xaxis_title="Čas",
        autosize=True
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True
    })

def create_power_graph(times, ts, steps, bars, inverted):
    """Graf výkonů a energií"""
    fig = go.Figure()

    for key in steps:
        fig.add_trace(
            go.Scatter(
                x=times,
                y=[-v if key in inverted else v for v in ts[key]],
                name=labels.get(key, key),
                line_shape="hv",
                mode="lines",
                marker_color=ha_color.get(key, "black"),
            )
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
            )
        )

    fig.update_layout(
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        title="⚡ Výkony a toky energie",
        yaxis_title="Výkon [kW]",
        xaxis_title="Čas",
        autosize=True
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True
    })

def create_prices_graph(times, ts):
    """Graf cen elektřiny"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts["buy_price"],
            name=labels["buy_price"],
            line_shape="hv",
            mode="lines+markers",
            marker_color=ha_color["buy_price"],
            line=dict(width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts["sell_price"],
            name=labels["sell_price"],
            line_shape="hv",
            mode="lines+markers",
            marker_color=ha_color["sell_price"],
            line=dict(width=3),
        )
    )

    fig.update_layout(
        height=350,
        margin=dict(l=50, r=50, t=80, b=50),
        title="💰 Ceny elektřiny",
        yaxis_title="Cena [Kč/kWh]",
        xaxis_title="Čas",
        autosize=True
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True
    })

def create_heating_graph(times, ts):
    """Graf tepelných ztrát a teplot"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts["heating_demand"],
            name=labels["heating_demand"],
            mode="lines",
            marker_color=ha_color["heating_demand"],
            line=dict(width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts["outdoor_temps"],
            name=labels["outdoor_temps"],
            mode="lines",
            marker_color=ha_color["outdoor_temps"],
            line=dict(width=2),
        )
    )
    
    # Teploty z výstupů MPC
    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts.get("temp_lower", []),
            name=labels.get("temp_lower", "temp_lower"),
            line_dash="dash",
            marker_color=ha_color.get("temp_lower", "black"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=ts.get("temp_upper", []),
            name=labels.get("temp_upper", "temp_upper"),
            line_dash="dot",
            marker_color=ha_color.get("temp_upper", "black"),
        )
    )

    fig.update_layout(
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        title="🌡️ Teploty a tepelné ztráty",
        yaxis_title="Teplota [°C] / Ztráty [kWh]",
        xaxis_title="Čas",
        autosize=True
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True
    })

def create_actions_graph(times, actions_timeline):
    """Graf plánovaných akcí"""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(
            "Režimy střídače a FVE přebytek",
            "Akce ohřevu a rezervovaný výkon"
        ),
    )

    # Graf 1: Plán režimů střídače
    charger_modes = ["Self Use", "Back Up Mode", "Feedin Priority", "Manual"]
    mode_colors = ["#4db6ac", "#0f9d58", "#8353d1", "#f06292"]
    
    for i, mode in enumerate(charger_modes):
        mode_values = [1 if m == mode else 0 for m in actions_timeline["charger_mode"]]
        if any(mode_values):
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=mode_values,
                    name=f"Režim: {mode}",
                    mode="lines",
                    line_shape="hv",
                    stackgroup="charger_modes",
                    marker_color=mode_colors[i],
                ),
                row=1,
                col=1,
            )
    
    # FVE přebytek
    max_surplus = max(actions_timeline["fve_surplus"]) if actions_timeline["fve_surplus"] and max(actions_timeline["fve_surplus"]) > 0 else 1
    normalized_surplus = [s/max_surplus for s in actions_timeline["fve_surplus"]]
    
    fig.add_trace(
        go.Scatter(
            x=times,
            y=normalized_surplus,
            name=f"FVE přebytek (max: {max_surplus:.1f} kW)",
            mode="lines",
            line_shape="hv",
            marker_color="#ffeb3b",
            line_dash="dot",
            customdata=actions_timeline["fve_surplus"],
        ),
        row=1,
        col=1,
    )
    
    # Graf 2: Plán akcí ohřevu
    heating_actions = [
        ("upper_accumulation", "Horní akumulace", "#c97a94"),
        ("lower_accumulation", "Spodní akumulace", "#0f9d58"), 
        ("max_heat", "Maximální ohřev", "#ff9800"),
        ("heating_blocked", "Ohřev blokován", "#f44336"),
    ]
    
    for action_key, action_name, color in heating_actions:
        action_values = [1 if v else 0 for v in actions_timeline[action_key]]
        if any(action_values):
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=action_values,
                    name=action_name,
                    mode="lines",
                    line_shape="hv",
                    stackgroup="heating_actions",
                    marker_color=color,
                ),
                row=2,
                col=1,
            )
    
    # Rezervovaný výkon
    max_reserve = max(actions_timeline["reserve_power"]) if actions_timeline["reserve_power"] and max(actions_timeline["reserve_power"]) > 0 else 1000
    normalized_reserve = [r/max_reserve for r in actions_timeline["reserve_power"]]
    
    fig.add_trace(
        go.Scatter(
            x=times,
            y=normalized_reserve,
            name=f"Rezerva baterie (max: {max_reserve/1000:.1f} kW)",
            mode="lines",
            line_shape="hv",
            marker_color="#4db6ac",
            line_dash="dash",
            customdata=actions_timeline["reserve_power"],
        ),
        row=2,
        col=1,
    )

    fig.update_yaxes(title_text="Aktivní", row=1, col=1)
    fig.update_yaxes(title_text="Aktivní", row=2, col=1)

    fig.update_layout(
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        title="🎯 Plán akcí a optimalizace",
        showlegend=True,
        autosize=True
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config={
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': True
    })

# Zachování původní funkce pro zpětnou kompatibilitu
def presentation_single(solution):
    """Původní funkce pro jeden velký graf"""
    times = [datetime.fromisoformat(t) for t in solution["times"]]

    ts = {**solution["inputs"], **solution["outputs"]}

    socs = ["b_soc_percent", "h_soc_lower_percent", "h_soc_upper_percent"]
    inverted = ["g_sell", "h_out_lower", "h_out_upper", "b_discharge"]
    steps = ["h_in_lower", "h_in_upper", "h_out_lower", "h_out_upper", "fve_pred", "load_pred"]
    bars = ["b_charge", "b_discharge", "g_buy", "g_sell", "h_to_upper"]

    options = solution.get("options", {})
    heating_enabled = options.get("heating_enabled", False)

    # Generování plánu akcí pro všechny sloty
    actions_timeline = mpc_to_actions_timeline(solution)

    fig = make_subplots(
        rows=6 if heating_enabled or True else 5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            "Stavy (SoC)",
            "Výkony",
            "Ceny elektřiny",
            "Tepelné ztráty a venkovní teplota",
            "Plán režimů střídače",
            "Plán akcí ohřevu",
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

    # === NOVÉ GRAFY PLÁNŮ AKCÍ ===
    
    # Graf 5: Plán režimů střídače
    charger_modes = ["Self Use", "Back Up Mode", "Feedin Priority", "Manual"]
    mode_colors = ["#4db6ac", "#0f9d58", "#8353d1", "#f06292"]
    
    for i, mode in enumerate(charger_modes):
        mode_values = [1 if m == mode else 0 for m in actions_timeline["charger_mode"]]
        if any(mode_values):  # Zobrazit pouze pokud se mode používá
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=mode_values,
                    name=f"Režim: {mode}",
                    mode="lines",
                    line_shape="hv",
                    stackgroup="charger_modes",
                    marker_color=mode_colors[i],
                    hovertemplate=f"<b>{mode}</b><br>" +
                                  "Čas: %{x}<br>" +
                                  "Aktivní: %{y}<br>" +
                                  "<extra></extra>",
                ),
                row=5,
                col=1,
            )
    
    # Přidání informací o FVE přebytku (normalizováno na 0-1 škálu)
    max_surplus = max(actions_timeline["fve_surplus"]) if actions_timeline["fve_surplus"] and max(actions_timeline["fve_surplus"]) > 0 else 1
    normalized_surplus = [s/max_surplus for s in actions_timeline["fve_surplus"]]
    
    fig.add_trace(
        go.Scatter(
            x=times,
            y=normalized_surplus,
            name=f"FVE přebytek (max: {max_surplus:.1f} kW)",
            mode="lines",
            line_shape="hv",
            marker_color="#ffeb3b",
            line_dash="dot",
            hovertemplate="<b>FVE přebytek</b><br>" +
                          "Čas: %{x}<br>" +
                          f"Přebytek: %{{customdata:.2f}} kW<br>" +
                          "<extra></extra>",
            customdata=actions_timeline["fve_surplus"],
        ),
        row=5,
        col=1,
    )
    
    # Graf 6: Plán akcí ohřevu
    heating_actions = [
        ("upper_accumulation", "Horní akumulace", "#c97a94"),
        ("lower_accumulation", "Spodní akumulace", "#0f9d58"), 
        ("max_heat", "Maximální ohřev", "#ff9800"),
        ("heating_blocked", "Ohřev blokován", "#f44336"),
    ]
    
    for action_key, action_name, color in heating_actions:
        action_values = [1 if v else 0 for v in actions_timeline[action_key]]
        if any(action_values):  # Zobrazit pouze pokud se akce používá
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=action_values,
                    name=action_name,
                    mode="lines",
                    line_shape="hv",
                    stackgroup="heating_actions",
                    marker_color=color,
                    hovertemplate=f"<b>{action_name}</b><br>" +
                                  "Čas: %{x}<br>" +
                                  "Aktivní: %{y}<br>" +
                                  "<extra></extra>",
                ),
                row=6,
                col=1,
            )
    
    # Přidání informací o rezervovaném výkonu (normalizováno)
    max_reserve = max(actions_timeline["reserve_power"]) if actions_timeline["reserve_power"] and max(actions_timeline["reserve_power"]) > 0 else 1000
    normalized_reserve = [r/max_reserve for r in actions_timeline["reserve_power"]]
    
    fig.add_trace(
        go.Scatter(
            x=times,
            y=normalized_reserve,
            name=f"Rezervovaný výkon (max: {max_reserve/1000:.1f} kW)",
            mode="lines",
            line_shape="hv",
            marker_color="#4db6ac",
            line_dash="dash",
            hovertemplate="<b>Rezervovaný výkon</b><br>" +
                          "Čas: %{x}<br>" +
                          f"Výkon: %{{customdata:.0f}} W<br>" +
                          "<extra></extra>",
            customdata=actions_timeline["reserve_power"],
        ),
        row=6,
        col=1,
    )
    
    # Aktualizace os pro nové grafy
    fig.update_yaxes(title_text="Energie [%]", row=1, col=1)
    fig.update_yaxes(title_text="Výkon [kW]", row=2, col=1)
    fig.update_yaxes(title_text="Cena [Kč/kWh]", row=3, col=1)
    fig.update_yaxes(title_text="kWh, °C", row=4, col=1)
    fig.update_yaxes(title_text="Aktivní", side="left", row=5, col=1)
    fig.update_yaxes(title_text="Aktivní", side="left", row=6, col=1)

    # Nastavení výšky grafu pro lepší čitelnost
    fig.update_layout(
        height=850,  # Zvýšená výška pro více grafů
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