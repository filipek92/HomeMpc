#!/usr/bin/env python3

"""Linear MPC optimizer for household energy management

Arguments are grouped into three dictionaries to keep the call‑site tidy and
self‑explanatory:

* ``series`` – every *vector* that spans the optimisation horizon (one value
  per timestep):

  - ``tuv_demand`` (\[kWh\])
  - ``heating_demand`` (\[kWh\])
  - ``fve`` – photovoltaic production (\[kW\])
  - ``buy`` – grid purchase prices (\[Kč / kWh\])
  - ``sell`` – feed‑in tariffs (\[Kč / kWh\])
  - ``load`` – household base load (\[kW\])

* ``initials`` – *scalars* that describe the initial state of storage systems:

  - ``soc_bat`` – battery state‑of‑charge at *t = 0* (\[kWh\])
  - ``soc_boiler`` – boiler energy content at *t = 0* (\[kWh\])

* ``options`` – miscellaneous switches **and** parameter overrides.  Unknown
  keys are ignored.

  Boolean knobs:
  ~~~~~~~~~~~~~~
  - ``heating_enabled`` – include space‑heating demand if **True** (default
    **False**)

  Numeric parameter overrides (all optional – defaults shown):
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  - ``B_CAP``          = 17.4   – battery capacity (kWh)
  - ``B_MIN``          = B_CAP*0.15 – minimum SOC (kWh)
  - ``B_MAX``          = B_CAP  – maximum SOC (kWh)
  - ``B_POWER``        = 9      – battery (dis)charge limit (kW)
  - ``B_EFF_IN``       = 0.94   – charging efficiency (–)
  - ``B_EFF_OUT``      = 0.94   – discharging efficiency (–)
  - ``H_CAP``          = 81.0   – boiler capacity (kWh)
  - ``H_POWER``        = 12     – electric heater limit (kW)
  - ``GRID_LIMIT``     = 18     – main breaker (kW)
  - ``INVERTER_LIMIT`` = 15     – PV inverter export limit (kW)

* ``dt`` – optional list of time step lengths [h], one per timestep. Default: 1.0.

This structure eliminates a long positional parameter list and makes it clear
which values belong in which category – future options can be added without
breaking the API.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence, Mapping, Any, List, Dict
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatusOptimal

from models.tank_losses import estimate_heating_losses

VARIABLES_SPEC = {
    # Vstupní vektory (series)
    "series": {
        "tuv_demand":    {"type": "list[float]", "unit": "kWh", "range": [0, None]},
        "heating_demand":{"type": "list[float]", "unit": "kWh", "range": [0, None]},
        "fve_pred":      {"type": "list[float]", "unit": "kW",  "range": [0, None]},
        "buy_price":     {"type": "list[float]", "unit": "Kč/kWh", "range": [0, None]},
        "sell_price":    {"type": "list[float]", "unit": "Kč/kWh", "range": [0, None]},
        "load_pred":     {"type": "list[float]", "unit": "kW",  "range": [0, None]},
    },
    # Počáteční stavy (initials)
    "initials": {
        "bat_soc":   {"type": "float", "unit": "%", "range": [0, 100]},
        "boiler_E":  {"type": "float", "unit": "kWh", "range": [0, 81]},
    },
    # Parametry a volby (options)
    "options": {
        "heating_enabled": {"type": "bool"},
        "charge_bat_min":  {"type": "bool"},
        "B_CAP":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 17.4},
        "B_MIN":           {"type": "float", "unit": "kWh", "range": [0, None]},
        "B_MAX":           {"type": "float", "unit": "kWh", "range": [0, None]},
        "B_POWER":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 9},
        "B_EFF_IN":        {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "B_EFF_OUT":       {"type": "float", "unit": "-",   "range": [0, 1], "default": 0.94},
        "H_CAP":           {"type": "float", "unit": "kWh", "range": [0, None], "default": 81.0},
        "H_POWER":         {"type": "float", "unit": "kW",  "range": [0, None], "default": 12},
        "GRID_LIMIT":      {"type": "float", "unit": "kW",  "range": [0, None], "default": 18},
        "INVERTER_LIMIT":  {"type": "float", "unit": "kW",  "range": [0, None], "default": 15},
        "final_boler_price": {"type": "float", "unit": "Kč/kWh"},
        "BAT_THRESHOLD_PCT": {"type": "float", "unit": "-", "range": [0, 1], "default": 0.40},
        "BAT_PRICE_BELOW":   {"type": "float", "unit": "Kč/kWh"},
        "BAT_PRICE_ABOVE":   {"type": "float", "unit": "Kč/kWh"},
        "battery_penalty":   {"type": "float", "unit": "Kč/kWh"},
    }
}

def clamp(value, min_value, max_value):
    """Omezí hodnotu na zadaný rozsah."""
    return max(min_value, min(value, max_value))

def run_mpc_optimizer(
    series: Mapping[str, Sequence[float]],
    initials: Mapping[str, float],
    hours: Sequence[datetime],
    options: Mapping[str, Any] | None = None,
    dt: Sequence[float] | None = None,
) -> Dict[str, Dict[str, List[float]]]:
    """Run a linear MPC optimisation for the given horizon."""

    options = options or {}
    indexes = range(len(hours))
    if dt is None:
        dt = [1.0] * len(hours)

    heating_enabled: bool = bool(options.get("heating_enabled", False))
    charge_bat_min: bool = bool(options.get("charge_bat_min", False))

    B_CAP = float(options.get("B_CAP", 17.4))
    B_MIN = float(options.get("B_MIN", B_CAP * 0.15))
    B_MAX = float(options.get("B_MAX", B_CAP * 1.00))
    B_POWER = float(options.get("B_POWER", 9))
    B_EFF_IN = float(options.get("B_EFF_IN", 0.94))
    B_EFF_OUT = float(options.get("B_EFF_OUT", 0.94))

    H_CAP = float(options.get("H_CAP", 81.0))
    H_POWER = float(options.get("H_POWER", 12))

    GRID_LIMIT = float(options.get("GRID_LIMIT", 18))
    INVERTER_LIMIT = float(options.get("INVERTER_LIMIT", 15))

    tuv_demand = series["tuv_demand"]
    heating_demand = series["heating_demand"]
    fve_pred = series["fve_pred"]
    buy_price = series["buy_price"]
    sell_price = series["sell_price"]
    load_pred = series["load_pred"]

    soc_bat_init = clamp(initials["bat_soc"] / 100 * B_CAP, B_MIN, B_MAX)
    soc_boiler_init = initials["boiler_E"]

    final_boiler_price = float(options.get("final_boler_price", min(buy_price) - 0.5))
    BAT_THRESHOLD_PCT = float(options.get("BAT_THRESHOLD_PCT", 0.40))
    BAT_PRICE_BELOW = float(options.get("BAT_PRICE_BELOW", min(buy_price)))
    BAT_PRICE_ABOVE = float(options.get("BAT_PRICE_ABOVE", min(buy_price) - 0.5))
    battery_penalty = float(options.get("battery_penalty", 0))

    prob = LpProblem("EnergyMPC", LpMinimize)

    B_power = LpVariable.dicts("B_power", indexes, -B_POWER, B_POWER)
    B_SOC = LpVariable.dicts("B_SOC", indexes, B_MIN, B_MAX)
    B_charge = LpVariable.dicts("B_charge", indexes, 0, B_POWER)
    B_discharge = LpVariable.dicts("B_discharge", indexes, 0, B_POWER)
    H_in = LpVariable.dicts("H_in", indexes, 0, H_POWER)
    H_SOC = LpVariable.dicts("H_SOC", indexes, 0, H_CAP)
    H_out = LpVariable.dicts("H_out", indexes, 0)
    G_buy = LpVariable.dicts("G_buy", indexes, 0)
    G_sell = LpVariable.dicts("G_sell", indexes, 0)

    threshold = BAT_THRESHOLD_PCT * B_CAP
    t_end = max(indexes)
    B_short = LpVariable("B_short", 0, threshold)
    B_surplus = LpVariable("B_surplus", 0, B_CAP - threshold)
    prob += B_short + B_surplus == B_SOC[t_end]

    for t in indexes:
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    prob += (
        lpSum(
            (G_buy[t] * buy_price[t] - G_sell[t] * sell_price[t] + battery_penalty * B_discharge[t]) * dt[t]
            for t in indexes
        )
        - BAT_PRICE_ABOVE * B_surplus
        + BAT_PRICE_BELOW * (threshold - B_short)
        - final_boiler_price * H_SOC[t_end]
    )

    for t in indexes:
        prob += (
            fve_pred[t] + G_buy[t] + B_discharge[t] * B_EFF_OUT ==
            load_pred[t] + B_charge[t] / B_EFF_IN + H_in[t] + G_sell[t]
        )
        prob += H_in[t] <= H_POWER
        prob += G_buy[t] + B_charge[t] + H_in[t] <= GRID_LIMIT
        prob += B_discharge[t] + H_in[t] + G_sell[t] <= INVERTER_LIMIT
        prob += H_out[t] == tuv_demand[t] + (heating_demand[t] if heating_enabled else 0)

        loss = estimate_heating_losses(
            (H_SOC[t - 1] if t > 0 else soc_boiler_init), H_CAP, T_ambient=20, cirk_time=0.3
        )

        if t == 0:
            prob += (
                B_SOC[t] == soc_bat_init +
                (B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT) * dt[t]
            )
            prob += H_SOC[t] == soc_boiler_init + (H_in[t] - H_out[t]) * dt[t]
        else:
            prob += (
                B_SOC[t] == B_SOC[t - 1] +
                (B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT) * dt[t]
            )
            prob += (
                H_SOC[t] == H_SOC[t - 1] + (H_in[t] - H_out[t] - loss) * dt[t]
            )

    # Dynamické omezení SOC baterie podle plánu ohřevu nádrže
    for t in indexes:
        if heating_demand[t] > 0 or tuv_demand[t] > 0:
            prob += B_SOC[t] <= B_CAP * 0.9
        else:
            prob += B_SOC[t] <= B_CAP
        prob += B_SOC[t] >= B_MIN
        # Pokud je baterie pod 60 %, neohříváme vodu
        if charge_bat_min:
            prob += H_in[t] <= H_POWER * (B_SOC[t] >= B_CAP * 0.6)

    prob.solve()

    if prob.status != LpStatusOptimal:
        raise RuntimeError("Optimal solution not found – model infeasible")

    outputs = {
        "B_power": [B_power[t].varValue for t in indexes],
        "B_charge": [B_charge[t].varValue for t in indexes],
        "B_discharge": [B_discharge[t].varValue for t in indexes],
        "B_SOC": [B_SOC[t].varValue for t in indexes],
        "B_SOC_percent": [int(100 * B_SOC[t].varValue / B_CAP) for t in indexes],
        "H_SOC": [H_SOC[t].varValue for t in indexes],
        "H_SOC_percent": [100 * H_SOC[t].varValue / H_CAP for t in indexes],
        "H_in": [H_in[t].varValue for t in indexes],
        "H_out": [H_out[t].varValue for t in indexes],
        "G_buy": [G_buy[t].varValue for t in indexes],
        "G_sell": [G_sell[t].varValue for t in indexes],
        # Celková cena za nakoupenou energii
        "buy_cost": [G_buy[t].varValue * buy_price[t] for t in indexes],
        # Celkový příjem za prodanou energii
        "sell_income": [G_sell[t].varValue * sell_price[t] for t in indexes],
        # Průběh čistých nákladů v každém kroku
        "net_step_cost": [G_buy[t].varValue * buy_price[t] - G_sell[t].varValue * sell_price[t] for t in indexes],
    }

    results = {k: v[0] for k, v in outputs.items() if isinstance(v, list)}
    # Přidání souhrnných hodnot i do results
    results["total_buy_cost"] = sum(outputs["buy_cost"])
    results["total_sell_income"] = sum(outputs["sell_income"])
    # Přidání celkového součtu čistých nákladů
    results["net_bilance"] = sum(outputs["net_step_cost"])

    return {
        "generated_at": datetime.now().isoformat(),
        "times": [h.isoformat() for h in hours],
        "inputs": series,
        "outputs": outputs,
        "results": results,
        "options": options,
    }
