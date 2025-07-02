#!/usr/bin/env python3

"""Linear MPC optimizer for household energy management

H_in variable limited to 12 kW per timestep.
"""

from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatusOptimal
from models.tank_losses import estimate_heating_losses

heating_enabled = False  # Set to False if heating is not enabled


def run_mpc_optimizer(
    tuv_demand,
    heating_demand,
    fve,
    buy,
    sell,
    load,
    soc_bat_init,
    soc_boiler_init,
    hours,
):
    indexes = range(len(hours))

    # --- System parameters -------------------------------------------------
    B_CAP = 17.4
    B_MIN = B_CAP * 0.15
    B_MAX = B_CAP
    H_CAP = 81.0

    B_POWER = 9           # kW battery charge/discharge limit
    H_POWER = 12          # kW max electric heater power (single store)

    GRID_LIMIT = 18       # kW main breaker limit
    INVERTER_LIMIT = 15   # kW inverter export limit

    B_EFF_IN = 0.94
    B_EFF_OUT = 0.94

    prob = LpProblem("EnergyMPC", LpMinimize)

    # --- Decision variables -----------------------------------------------
    B_power = LpVariable.dicts("B_power", indexes, -B_POWER, B_POWER)
    B_SOC = LpVariable.dicts("B_SOC", indexes, B_MIN, B_MAX)

    H_in = LpVariable.dicts("H_in", indexes, 0, H_POWER)  # single heater

    G_buy = LpVariable.dicts("G_buy", indexes, 0)
    G_sell = LpVariable.dicts("G_sell", indexes, 0)

    H_SOC = LpVariable.dicts("H_SOC", indexes, 0, H_CAP)
    H_out = LpVariable.dicts("H_out", indexes, 0)

    # Helper split for linear charge/discharge power
    B_charge = LpVariable.dicts("B_charge", indexes, 0, B_POWER)
    B_discharge = LpVariable.dicts("B_discharge", indexes, 0, B_POWER)

    for t in indexes:
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    # --- Objective ---------------------------------------------------------
    final_boiler_price = min(buy) - 0.5
    final_bat_price = min(buy) - 1.5
    battery_deg_penalty_kcz = 1.0  # Kč / kWh discharged

    prob += (
        lpSum(
            G_buy[t] * buy[t]
            - G_sell[t] * sell[t]
            + battery_deg_penalty_kcz * B_discharge[t]
            for t in indexes
        )
        - final_bat_price * B_SOC[max(indexes)]
        - final_boiler_price * H_SOC[max(indexes)]
    )

    # --- Constraints -------------------------------------------------------
    for t in indexes:
        # Energy balance
        prob += (
            fve[t]
            + G_buy[t]
            + B_discharge[t] * B_EFF_OUT
            == load[t] + B_charge[t] / B_EFF_IN + H_in[t] + G_sell[t]
        )

        # Electric heater limit (redundant but explicit)
        prob += H_in[t] <= H_POWER

        # Main breaker & inverter limits
        prob += G_buy[t] + B_charge[t] + H_in[t] <= GRID_LIMIT
        prob += B_discharge[t] + H_in[t] + G_sell[t] <= INVERTER_LIMIT

        # Hot‑water / heating demand
        prob += H_out[t] == tuv_demand[t] + (heating_demand[t] if heating_enabled else 0)

        # Thermal losses
        loss = estimate_heating_losses(
            H_SOC[t - 1] if t > 0 else soc_boiler_init,
            H_CAP,
            T_ambient=20,
            cirk_time=0.3,
        )

        # Battery and boiler SOC dynamics
        if t == 0:
            prob += (
                B_SOC[t]
                == soc_bat_init + B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT
            )
            prob += H_SOC[t] == soc_boiler_init + H_in[t] - H_out[t]
        else:
            prob += (
                B_SOC[t]
                == B_SOC[t - 1] + B_charge[t] * B_EFF_IN - B_discharge[t] / B_EFF_OUT
            )
            prob += (
                H_SOC[t]
                == H_SOC[t - 1] + H_in[t] - H_out[t] - loss
            )

    # --- Solve -------------------------------------------------------------
    prob.solve()

    if prob.status != LpStatusOptimal:
        raise RuntimeError("Model není řešitelný")

    # --- Post‑processing ---------------------------------------------------
    total_discharge = sum(B_discharge[t].varValue for t in indexes)
    max_boiler_energy = max(H_SOC[t].varValue for t in indexes)

    def energy_to_temp(kwh: float, portion: float) -> float:
        """Rough conversion kWh → °C for given water volume portion (l)."""
        return 45 + (kwh / (portion * 4.18)) * 3600 / 1000

    target_temp_top = min(90, energy_to_temp(max_boiler_energy * 0.33, 333))
    target_temp_rest = min(65, energy_to_temp(max_boiler_energy * 0.67, 667))

    force_discharge_power = max(G_sell[t].varValue - fve[t] for t in indexes)
    allow_grid_heating = any(
        G_buy[t].varValue > 0.2 and H_in[t].varValue > 0.2 for t in indexes
    )
    allow_grid_export = any(G_sell[t].varValue > 0.2 for t in indexes)

    results = {
        "B_power": [B_power[t].varValue for t in indexes],
        "B_charge": [B_charge[t].varValue for t in indexes],
        "B_discharge": [B_discharge[t].varValue for t in indexes],
        "B_SOC": [B_SOC[t].varValue for t in indexes],
        "B_SOC_percent": [100 * B_SOC[t].varValue / B_MAX for t in indexes],
        "H_SOC": [H_SOC[t].varValue for t in indexes],
        "H_SOC_percent": [100 * H_SOC[t].varValue / H_CAP for t in indexes],
        "H_in": [H_in[t].varValue for t in indexes],
        "H_out": [H_out[t].varValue for t in indexes],
        "G_buy": [G_buy[t].varValue for t in indexes],
        "G_sell": [G_sell[t].varValue for t in indexes],
        "load": load,
        "fve": fve,
        "buy_price": buy,
        "sell_price": sell,
        "heating_demand": heating_demand,
    }

    return {
        "time_series": results
    }
