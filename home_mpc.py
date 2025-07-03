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

This structure eliminates a long positional parameter list and makes it clear
which values belong in which category – future options can be added without
breaking the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence, Mapping, Any, List, Dict
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatusOptimal

from models.tank_losses import estimate_heating_losses

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_mpc_optimizer(
    series: Mapping[str, Sequence[float]],
    initials: Mapping[str, float],
    hours: Sequence[datetime],
    options: Mapping[str, Any] | None = None,
) -> Dict[str, Dict[str, List[float]]]:
    """Run a linear MPC optimisation for the given horizon.

    Parameters
    ----------
    series
        Mapping whose items are *sequences* – one value per timestep.
    initials
        Mapping whose items are *scalars* – battery/boiler state at ``hours[0]``.
    hours
        Sequence of datetimes that defines the optimisation horizon (one entry
        per timestep).
    options
        Miscellaneous switches and parameter overrides.  Unknown keys are
        ignored.
    """

    options = options or {}

    # -------------------------------------------------------------------
    # Switches
    # -------------------------------------------------------------------
    heating_enabled: bool = bool(options.get("heating_enabled", False))

    # -------------------------------------------------------------------
    # System parameters (allow override via *options*)
    # -------------------------------------------------------------------
    B_CAP          = float(options.get("B_CAP", 17.4))
    B_MIN          = float(options.get("B_MIN", B_CAP * 0.15))
    B_MAX          = float(options.get("B_MAX", B_CAP))
    B_POWER        = float(options.get("B_POWER", 9))
    B_EFF_IN       = float(options.get("B_EFF_IN", 0.94))
    B_EFF_OUT      = float(options.get("B_EFF_OUT", 0.94))

    H_CAP          = float(options.get("H_CAP", 81.0))
    H_POWER        = float(options.get("H_POWER", 12))

    GRID_LIMIT     = float(options.get("GRID_LIMIT", 18))
    INVERTER_LIMIT = float(options.get("INVERTER_LIMIT", 15))

    # -------------------------------------------------------------------
    # Input unpacking
    # -------------------------------------------------------------------
    tuv_demand:      Sequence[float] = series["tuv_demand"]
    heating_demand:  Sequence[float] = series["heating_demand"]
    fve_pred:        Sequence[float] = series["fve_pred"]
    buy_price:       Sequence[float] = series["buy_price"]
    sell_price:      Sequence[float] = series["sell_price"]
    load_pred:       Sequence[float] = series["load_pred"]

    soc_bat_init:    float = initials["soc_bat"]
    soc_boiler_init: float = initials["soc_boiler"]

    indexes = range(len(hours))

    # -------------------------------------------------------------------
    # Model definition
    # -------------------------------------------------------------------
    prob = LpProblem("EnergyMPC", LpMinimize)

    # Decision variables --------------------------------------------------
    B_power      = LpVariable.dicts("B_power",      indexes, -B_POWER, B_POWER)
    B_SOC        = LpVariable.dicts("B_SOC",        indexes, B_MIN,   B_MAX)
    B_charge     = LpVariable.dicts("B_charge",     indexes, 0,        B_POWER)
    B_discharge  = LpVariable.dicts("B_discharge",  indexes, 0,        B_POWER)

    H_in         = LpVariable.dicts("H_in",         indexes, 0,        H_POWER)
    H_SOC        = LpVariable.dicts("H_SOC",        indexes, 0,        H_CAP)
    H_out        = LpVariable.dicts("H_out",        indexes, 0)

    G_buy        = LpVariable.dicts("G_buy",        indexes, 0)
    G_sell       = LpVariable.dicts("G_sell",       indexes, 0)

    # Link helper variables to main power variable -----------------------
    for t in indexes:
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    # Objective ----------------------------------------------------------
    final_boiler_price = min(buy_price) - 0.5
    final_bat_price    = min(buy_price)
    battery_penalty    = 1.0            # Kč / kWh discharged (degradation)

    prob += (
        lpSum(
            G_buy[t]  * buy_price[t]  -
            G_sell[t] * sell_price[t] +
            battery_penalty * B_discharge[t]
            for t in indexes
        )
        # Reward remaining stored energy at the cheapest observed tariffs
        - final_bat_price    * B_SOC[max(indexes)]
        - final_boiler_price * H_SOC[max(indexes)]
    )

    # Constraints --------------------------------------------------------
    prob += B_SOC[max(indexes)] >= B_MAX*0.6

    for t in indexes:
        # Power balance --------------------------------------------------
        prob += (
            fve_pred[t] +
            G_buy[t] +
            B_discharge[t] * B_EFF_OUT
            == load_pred[t] + B_charge[t] / B_EFF_IN + H_in[t] + G_sell[t]
        )

        # Hardware limits ----------------------------------------------
        prob += H_in[t] <= H_POWER
        prob += G_buy[t] + B_charge[t] + H_in[t] <= GRID_LIMIT
        prob += B_discharge[t] + H_in[t] + G_sell[t] <= INVERTER_LIMIT

        # Thermal demand -----------------------------------------------
        prob += H_out[t] == (
            tuv_demand[t] + (heating_demand[t] if heating_enabled else 0)
        )

        # Tank thermal losses ------------------------------------------
        loss = estimate_heating_losses(
            (H_SOC[t - 1] if t > 0 else soc_boiler_init),
            H_CAP,
            T_ambient=20,
            cirk_time=0.3,
        )

        # Storage dynamics ---------------------------------------------
        if t == 0:
            prob += (
                B_SOC[t] == soc_bat_init +
                B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT
            )
            prob += H_SOC[t] == soc_boiler_init + H_in[t] - H_out[t]
        else:
            prob += (
                B_SOC[t] == B_SOC[t - 1] +
                B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT
            )
            prob += (
                H_SOC[t] == H_SOC[t - 1] + H_in[t] - H_out[t] - loss
            )

    # -------------------------------------------------------------------
    # Solve optimisation problem
    # -------------------------------------------------------------------
    prob.solve()

    if prob.status != LpStatusOptimal:
        raise RuntimeError("Optimal solution not found – model infeasible")

    # -------------------------------------------------------------------
    # Collect results into plain Python structures (easy to serialise)
    # -------------------------------------------------------------------
    outputs = {
        "B_power":       [B_power[t].varValue       for t in indexes],
        "B_charge":      [B_charge[t].varValue      for t in indexes],
        "B_discharge":   [B_discharge[t].varValue   for t in indexes],
        "B_SOC":         [B_SOC[t].varValue         for t in indexes],
        "B_SOC_percent": [int(100 * B_SOC[t].varValue / B_MAX) for t in indexes],
        "H_SOC":         [H_SOC[t].varValue         for t in indexes],
        "H_SOC_percent": [100 * H_SOC[t].varValue / H_CAP for t in indexes],
        "H_in":          [H_in[t].varValue          for t in indexes],
        "H_out":         [H_out[t].varValue         for t in indexes],
        "G_buy":         [G_buy[t].varValue         for t in indexes],
        "G_sell":        [G_sell[t].varValue        for t in indexes],
    }


    results = {k:v[0] for k, v in outputs.items()}

    return {
        "generated_at": datetime.now().isoformat(),
        "times": [h.isoformat() for h in hours],
        "inputs": series,
        "outputs": outputs,
        "results": results,
    }
