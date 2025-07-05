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
from options import VARIABLES_SPEC, get_option

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

    # Kontext pro odvozené hodnoty
    context = {}
    context["buy_price"] = series["buy_price"]

    heating_enabled = get_option(options, "heating_enabled")
    charge_bat_min = get_option(options, "charge_bat_min")
    B_CAP = get_option(options, "B_CAP")
    B_MIN = get_option(options, "B_MIN", context=context)
    B_MAX = get_option(options, "B_MAX", context=context)
    B_POWER = get_option(options, "B_POWER")
    B_EFF_IN = get_option(options, "B_EFF_IN")
    B_EFF_OUT = get_option(options, "B_EFF_OUT")
    H_CAP = get_option(options, "H_CAP")
    H_POWER = get_option(options, "H_POWER")
    GRID_LIMIT = get_option(options, "GRID_LIMIT")
    INVERTER_LIMIT = get_option(options, "INVERTER_LIMIT")
    final_boiler_price = get_option(options, "final_boler_price", context=context)
    BAT_THRESHOLD_PCT = get_option(options, "BAT_THRESHOLD_PCT")
    BAT_PRICE_BELOW = get_option(options, "BAT_PRICE_BELOW", context=context)
    BAT_PRICE_ABOVE = get_option(options, "BAT_PRICE_ABOVE", context=context)
    battery_penalty = get_option(options, "battery_penalty")
    fve_unused_penalty = get_option(options, "fve_unused_penalty")

    tuv_demand = series["tuv_demand"]
    heating_demand = series["heating_demand"]
    fve_pred = series["fve_pred"]
    buy_price = series["buy_price"]
    sell_price = series["sell_price"]
    load_pred = series["load_pred"]

    soc_bat_init = clamp(initials["bat_soc"] / 100 * B_CAP, B_MIN, B_MAX)
    soc_boiler_init = clamp(initials["boiler_E"], 0, H_CAP)

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
    FVE_unused = LpVariable.dicts("FVE_unused", indexes, 0)

    threshold = BAT_THRESHOLD_PCT * B_CAP
    t_end = max(indexes)
    B_short = LpVariable("B_short", 0, threshold)
    B_surplus = LpVariable("B_surplus", 0, B_CAP - threshold)
    prob += B_short + B_surplus == B_SOC[t_end]

    for t in indexes:
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    prob += (
        lpSum(
            (G_buy[t] * buy_price[t] - G_sell[t] * sell_price[t] + battery_penalty * B_discharge[t] + fve_unused_penalty * FVE_unused[t]) * dt[t]
            for t in indexes
        )
        - BAT_PRICE_ABOVE * B_surplus
        + BAT_PRICE_BELOW * (threshold - B_short)
        - final_boiler_price * H_SOC[t_end]
    )

    for t in indexes:
        prob += (
            fve_pred[t] + G_buy[t] + B_discharge[t] * B_EFF_OUT ==
            load_pred[t] + B_charge[t] / B_EFF_IN + H_in[t] + G_sell[t] + FVE_unused[t]
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
        "buy_cost": [G_buy[t].varValue * buy_price[t] for t in indexes],
        "sell_income": [G_sell[t].varValue * sell_price[t] for t in indexes],
        "net_step_cost": [G_buy[t].varValue * buy_price[t] - G_sell[t].varValue * sell_price[t] for t in indexes],
        "FVE_unused": [FVE_unused[t].varValue for t in indexes],
    }

    results = {k: v[0] for k, v in outputs.items() if isinstance(v, list)}
    results["total_buy_cost"] = sum(outputs["buy_cost"])
    results["total_sell_income"] = sum(outputs["sell_income"])
    results["net_bilance"] = sum(outputs["net_step_cost"])

    return {
        "generated_at": datetime.now().isoformat(),
        "times": [h.isoformat() for h in hours],
        "inputs": series,
        "outputs": outputs,
        "results": results,
        "options": options,
    }
