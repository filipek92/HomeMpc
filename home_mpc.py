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
import logging

from models.tank_losses import estimate_heating_losses
from options import VARIABLES_SPEC, get_option

# Nastavení základního logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def debug(msg):
    logging.info(msg)

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
    debug(f"run_mpc_optimizer called with options: {options}")
    debug(f"series keys: {list(series.keys())}")
    debug(f"initials: {initials}")

    options = options or {}
    indexes = range(len(hours))
    if dt is None:
        dt = [1.0] * len(hours)

    # Kontext pro odvozené hodnoty
    context = {}
    context["buy_price"] = series["buy_price"]

    heating_enabled = get_option(options, "heating_enabled")
    charge_bat_min = get_option(options, "charge_bat_min")
    b_cap = get_option(options, "b_cap")
    b_min = get_option(options, "b_min", context=context)
    b_max = get_option(options, "b_max", context=context)
    b_power_max = get_option(options, "b_power")
    b_eff_in = get_option(options, "b_eff_in")
    b_eff_out = get_option(options, "b_eff_out")
    h_cap = get_option(options, "h_cap")
    h_power_max = get_option(options, "h_power")
    grid_limit = get_option(options, "grid_limit")
    inverter_limit = get_option(options, "inverter_limit")
    final_boiler_price = get_option(options, "final_boiler_price", context=context)
    bat_threshold_pct = get_option(options, "bat_threshold_pct")
    bat_price_below = get_option(options, "bat_price_below", context=context)
    bat_price_above = get_option(options, "bat_price_above", context=context)
    battery_penalty = get_option(options, "battery_penalty")
    fve_unused_penalty = get_option(options, "fve_unused_penalty")
    water_priority_bonus = get_option(options, "water_priority_bonus")

    tuv_demand = series["tuv_demand"]
    heating_demand = series["heating_demand"]
    fve_pred = series["fve_pred"]
    buy_price = series["buy_price"]
    sell_price = series["sell_price"]
    load_pred = series["load_pred"]

    soc_bat_init = clamp(initials["bat_soc"] / 100 * b_cap, b_min, b_max)
    soc_boiler_init = clamp(initials["boiler_E"], 0, h_cap)

    prob = LpProblem("EnergyMPC", LpMinimize)

    # Přejmenování všech stavových proměnných a výstupů na lower_snake_case
    b_power = LpVariable.dicts("b_power", indexes, -b_power_max, b_power_max)
    b_soc = LpVariable.dicts("b_soc", indexes, b_min, b_max)
    b_charge = LpVariable.dicts("b_charge", indexes, 0, b_power_max)
    b_discharge = LpVariable.dicts("b_discharge", indexes, 0, b_power_max)
    h_in = LpVariable.dicts("h_in", indexes, 0, h_power_max)
    h_soc = LpVariable.dicts("h_soc", indexes, 0, h_cap)
    h_out = LpVariable.dicts("h_out", indexes, 0)
    g_buy = LpVariable.dicts("g_buy", indexes, 0)
    g_sell = LpVariable.dicts("g_sell", indexes, 0)
    fve_unused = LpVariable.dicts("fve_unused", indexes, 0)

    # Penalizace za SOC pod prahem v každém kroku
    bat_under_penalty = get_option(options, "bat_under_penalty")
    bat_threshold = bat_threshold_pct * b_cap
    b_soc_under = LpVariable.dicts("b_soc_under", indexes, 0)
    for t in indexes:
        prob += b_soc_under[t] >= bat_threshold - b_soc[t]
        prob += b_soc_under[t] >= 0

    threshold = bat_threshold_pct * b_cap
    t_end = max(indexes)
    b_short = LpVariable("b_short", 0, threshold)
    b_surplus = LpVariable("b_surplus", 0, b_cap - threshold)
    prob += b_short + b_surplus == b_soc[t_end]

    for t in indexes:
        prob += b_power[t] == b_charge[t] - b_discharge[t]

    # Parametry pro ocenění energie v nádrži v konkrétní hodinu
    tank_value_hour = get_option(options, "tank_value_hour")
    tank_value_bonus = get_option(options, "tank_value_bonus")  # Kč/kWh
    tank_value_indexes = [i for i, h in enumerate(hours) if h.hour == tank_value_hour]

    prob += (
        lpSum(
            (g_buy[t] * buy_price[t] - g_sell[t] * sell_price[t] + battery_penalty * b_discharge[t] + fve_unused_penalty * fve_unused[t]
             - water_priority_bonus * h_in[t] + bat_under_penalty * b_soc_under[t]) * dt[t]
            for t in indexes
        )
        - bat_price_above * b_surplus
        + bat_price_below * (threshold - b_short)
        - final_boiler_price * h_soc[t_end]
        - tank_value_bonus * lpSum(h_soc[t] for t in tank_value_indexes)
    )

    for t in indexes:
        prob += (
            fve_pred[t] + g_buy[t] + b_discharge[t] * b_eff_out ==
            load_pred[t] + b_charge[t] / b_eff_in + h_in[t] + g_sell[t] + fve_unused[t]
        )
        prob += h_in[t] <= h_power_max
        prob += g_buy[t] + b_charge[t] + h_in[t] <= grid_limit
        prob += b_discharge[t] + h_in[t] + g_sell[t] <= inverter_limit
        prob += h_out[t] == tuv_demand[t] + (heating_demand[t] if heating_enabled else 0)

        # Parametr pro parazitní ztráty při ohřevu vody (default 0.05 = 5 %)
        parasitic_water_heating = get_option(options, "parasitic_water_heating")
        # Parazitní energie při ohřevu vody (nastavitelný parametr)
        parasitic_energy = parasitic_water_heating * h_in[t]
        # Tato energie se musí dodat z FVE nebo sítě (tj. navýší H_in)
        prob += (
            fve_pred[t] + g_buy[t] + b_discharge[t] * b_eff_out ==
            load_pred[t] + b_charge[t] / b_eff_in + (h_in[t] + parasitic_energy) + g_sell[t] + fve_unused[t]
        )
        loss = estimate_heating_losses(
            (h_soc[t - 1] if t > 0 else soc_boiler_init), h_cap, T_ambient=20, cirk_time=0.3
        )

        if t == 0:
            prob += (
                b_soc[t] == soc_bat_init +
                (b_charge[t] * b_eff_in - b_discharge[t] / b_eff_out) * dt[t]
            )
            prob += h_soc[t] == soc_boiler_init + (h_in[t] - h_out[t]) * dt[t]
        else:
            prob += (
                b_soc[t] == b_soc[t - 1] +
                (b_charge[t] * b_eff_in - b_discharge[t] / b_eff_out) * dt[t]
            )
            prob += (
                h_soc[t] == h_soc[t - 1] + (h_in[t] - h_out[t] - loss) * dt[t]
            )

    # Dynamické omezení SOC baterie podle plánu ohřevu nádrže
    for t in indexes:
        if heating_demand[t] > 0 or tuv_demand[t] > 0:
            prob += b_soc[t] <= b_cap * 0.9
        else:
            prob += b_soc[t] <= b_cap
        prob += b_soc[t] >= b_min
        # Pokud je baterie pod 60 %, neohříváme vodu
        if charge_bat_min:
            prob += h_in[t] <= h_power_max * (b_soc[t] >= b_cap * 0.6)

    prob.solve()

    if prob.status != LpStatusOptimal:
        raise RuntimeError("Optimal solution not found – model infeasible")

    outputs = {
        "b_power": [b_power[t].varValue for t in indexes],
        "b_charge": [b_charge[t].varValue for t in indexes],
        "b_discharge": [b_discharge[t].varValue for t in indexes],
        "b_soc": [b_soc[t].varValue for t in indexes],
        "b_soc_percent": [int(100 * b_soc[t].varValue / b_cap) for t in indexes],
        "h_soc": [h_soc[t].varValue for t in indexes],
        "h_soc_percent": [100 * h_soc[t].varValue / h_cap for t in indexes],
        "h_in": [h_in[t].varValue for t in indexes],
        "h_out": [h_out[t].varValue for t in indexes],
        "g_buy": [g_buy[t].varValue for t in indexes],
        "g_sell": [g_sell[t].varValue for t in indexes],
        "buy_cost": [g_buy[t].varValue * buy_price[t] for t in indexes],
        "sell_income": [g_sell[t].varValue * sell_price[t] for t in indexes],
        "net_step_cost": [g_buy[t].varValue * buy_price[t] - g_sell[t].varValue * sell_price[t] for t in indexes],
        "fve_unused": [fve_unused[t].varValue for t in indexes],
    }

    results = {k: v[0] for k, v in outputs.items() if isinstance(v, list)}
    results["total_buy_cost"] = sum(outputs["buy_cost"])
    results["total_sell_income"] = sum(outputs["sell_income"])
    results["net_bilance"] = sum(outputs["net_step_cost"])
    results["total_charged"] = sum(outputs["b_charge"])  # Total energy charged to the battery
    results["total_discharged"] = sum(outputs["b_discharge"])  # Total energy discharged from the battery
    results["total_battery_penalty"] = sum(b_discharge[t].varValue * battery_penalty * dt[t] for t in indexes)
    results["total_fve_unused_penalty"] = sum(fve_unused[t].varValue * fve_unused_penalty * dt[t] for t in indexes)
    results["total_bat_price_above"] = bat_price_above * (b_surplus.varValue if hasattr(b_surplus, 'varValue') else 0)
    results["total_bat_price_below"] = bat_price_below * (threshold - (b_short.varValue if hasattr(b_short, 'varValue') else 0))
    results["total_final_boiler_value"] = final_boiler_price * (h_soc[t_end].varValue if hasattr(h_soc[t_end], 'varValue') else 0)
    results["total_fve_unused"] = sum(fve_unused[t].varValue * dt[t] for t in indexes)
    results["total_water_priority_bonus"] = sum(water_priority_bonus * h_in[t].varValue * dt[t] for t in indexes)
    results["total_battery_under_penalty"] = sum(b_soc_under[t].varValue * bat_under_penalty * dt[t] for t in indexes)
    results["tank_value_bonus"] = sum(h_soc[t].varValue * tank_value_bonus for t in tank_value_indexes)
    results["objective_value"] = prob.objective.value() if prob.objective is not None else None

    debug(f"b_cap: {b_cap}, b_min: {b_min}, b_max: {b_max}, h_cap: {h_cap}")
    debug(f"outputs keys: {list(outputs.keys())}")
    debug(f"results: {results}")

    # Výpočet celkové parazitní energie při ohřevu vody a její rozdělení podle SOC baterie (ex-post)
    total_parasitic_energy = 0.0
    total_parasitic_to_battery = 0.0
    total_parasitic_to_grid = 0.0
    for t in indexes:
        parasitic_water_heating = get_option(options, "parasitic_water_heating")
        pe = parasitic_water_heating * outputs["h_in"][t] * dt[t]
        total_parasitic_energy += pe
        # Rozdělení podle skutečného SOC baterie
        if outputs["b_soc"][t] < b_cap:
            total_parasitic_to_battery += pe
        else:
            total_parasitic_to_grid += pe
    results["total_parasitic_energy"] = total_parasitic_energy
    results["total_parasitic_to_battery"] = total_parasitic_to_battery
    results["total_parasitic_to_grid"] = total_parasitic_to_grid

    return {
        "generated_at": datetime.now().isoformat(),
        "times": [h.isoformat() for h in hours],
        "inputs": series,
        "outputs": outputs,
        "results": results,
        "options": options,
    }
