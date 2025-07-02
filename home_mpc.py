#!/usr/bin/env python3

from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatusOptimal
import pandas as pd
import matplotlib.pyplot as plt

def run_mpc_optimizer(
    tuv_demand,
    heating_demand,
    fve,
    buy,
    sell,
    base_load,
    soc_bat_init,
    soc_boiler_init,
    hours
):
    load = [base_load[t] + tuv_demand[t] for t in hours]

    # --- Parametry systému ---
    B_CAP = 17.4
    B_MIN = B_CAP * 0.10
    B_MAX = B_CAP
    H_CAP = 81.0
    B_POWER = 9
    H_POWER_TOP = 4
    H_POWER_BOTTOM = 8
    GRID_LIMIT = 18
    INVERTER_LIMIT = 15
    B_EFF_IN = 0.94
    B_EFF_OUT = 0.94

    prob = LpProblem("EnergyMPC", LpMinimize)

    # --- Proměnné ---
    # Kladný výkon: nabíjení, záporný: vybíjení
    B_power = LpVariable.dicts("B_power", hours, -B_POWER, B_POWER)
    B_SOC = LpVariable.dicts("B_SOC", hours, B_MIN, B_MAX)
    H_store_top = LpVariable.dicts("H_store_top", hours, 0, H_POWER_TOP)
    H_store_bottom = LpVariable.dicts("H_store_bottom", hours, 0, H_POWER_BOTTOM)
    G_buy = LpVariable.dicts("G_buy", hours, 0)
    G_sell = LpVariable.dicts("G_sell", hours, 0)
    H_SOC = LpVariable.dicts("H_SOC", hours, 0, H_CAP)
    H_out = LpVariable.dicts("H_out", hours, 0)

    # Pomocné proměnné pro LP rozdělení nabíjení/vybíjení:
    B_charge = LpVariable.dicts("B_charge", hours, 0, B_POWER)
    B_discharge = LpVariable.dicts("B_discharge", hours, 0, B_POWER)
    for t in hours:
        # V každé hodině: B_power = B_charge - B_discharge
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    # --- Cílová funkce ---
    prob += lpSum([G_buy[t]*buy[t] - G_sell[t]*sell[t] for t in hours])

    prob += H_SOC[max(hours)] >= 0.8 * H_CAP

    # --- Omezující podmínky ---
    for t in hours:
        h_total = H_store_top[t] + H_store_bottom[t]
        
        # Energetická bilance
        prob += (
            fve[t] + G_buy[t] + B_discharge[t]*B_EFF_OUT
            >= load[t] + B_charge[t]/B_EFF_IN + h_total + G_sell[t]
        )

        # SOC baterie - vždy v povoleném rozsahu (už je v deklaraci B_SOC)
        # Příkon hlavního jističe
        prob += G_buy[t] + B_charge[t] + h_total <= GRID_LIMIT

        # Výkon střídače
        prob += B_discharge[t] + h_total + G_sell[t] <= INVERTER_LIMIT

        # Výdej tepla z nádrže = požadavek na vytápění
        prob += H_out[t] == heating_demand[t]

        # Bilance baterie a nádrže
        if t == 0:
            prob += B_SOC[t] == soc_bat_init + B_charge[t]*B_EFF_IN - B_discharge[t]/B_EFF_OUT
            prob += H_SOC[t] == soc_boiler_init + H_store_top[t] + H_store_bottom[t] - H_out[t]
        else:
            prob += B_SOC[t] == B_SOC[t-1] + B_charge[t]*B_EFF_IN - B_discharge[t]/B_EFF_OUT
            prob += H_SOC[t] == H_SOC[t-1] + H_store_top[t] + H_store_bottom[t] - H_out[t]


    # --- Řešení modelu ---
    prob.solve()

    # Pokud se model nepodaří vyřešit, vypíšeme porušení constraintů
    if prob.status != LpStatusOptimal:
        print(prob)
        print("Model není řešitelný! Výpis všech constraintů a jejich hodnot:")
        for name, c in prob.constraints.items():
            lhs = c.value()  # aktuální hodnota LHS constraintu po řešení
            rhs = c.constant  # pravá strana
            # V pulp je směr c.sense: -1 je <=, 0 je ==, 1 je >=
            sense = { -1: "<=", 0: "==", 1: ">=" }[c.sense]
            print(f"{name}: {lhs:.2f} {sense} {rhs:.2f} | violation = {lhs - rhs:.2f}")
        # Navíc můžeš seřadit podle největšího porušení:
        print("\nTop 10 constraintů s největším porušením:")
        constraint_violations = sorted(
            [(name, abs(c.value() - c.constant), c) for name, c in prob.constraints.items()],
            key=lambda x: -x[1]
        )
        for name, violation, c in constraint_violations[:10]:
            sense = { -1: "<=", 0: "==", 1: ">=" }[c.sense]
            print(f"{name}: {c.value():.2f} {sense} {c.constant:.2f} | violation = {c.value() - c.constant:.2f}")

    min_soc_battery = min([B_SOC[t].varValue for t in hours])
    max_boiler_energy = max([H_SOC[t].varValue for t in hours])

    def energy_to_temp(kwh, portion):
        return 45 + (kwh / (portion * 4.18 * 1)) * 3600 / 1000

    target_temp_top = min(90, energy_to_temp(max_boiler_energy * 0.33, 333))
    target_temp_rest = min(65, energy_to_temp(max_boiler_energy * 0.67, 667))

    force_discharge_power = max([G_sell[t].varValue - fve[t] for t in hours])
    allow_grid_heating = any([G_buy[t].varValue > 0.2 and (H_store_top[t].varValue + H_store_bottom[t].varValue) > 0.2 for t in hours])
    allow_grid_export = any([G_sell[t].varValue > 0.2 for t in hours])

    results = {
        "B_power": [B_power[t].varValue for t in hours],
        "B_SOC": [B_SOC[t].varValue for t in hours],
        "B_SOC_percent": [100 * B_SOC[t].varValue / B_MAX for t in hours],
        "H_SOC": [H_SOC[t].varValue for t in hours],
        "H_SOC_percent": [100 * H_SOC[t].varValue / H_CAP for t in hours],
        "H_store_top": [H_store_top[t].varValue for t in hours],
        "H_store_bottom": [H_store_bottom[t].varValue for t in hours],
        "H_out": [H_out[t].varValue for t in hours],
        "G_buy": [G_buy[t].varValue for t in hours],
        "G_sell": [G_sell[t].varValue for t in hours],
        "load": load,
        "fve": fve,
        "buy_price": buy,
        "sell_price": sell,
        "heating_demand": heating_demand,
    }

    return {
        "min_soc_battery": round(min_soc_battery, 2),
        "target_temp_top": round(target_temp_top, 1),
        "target_temp_rest": round(target_temp_rest, 1),
        "allow_grid_export": allow_grid_export,
        "force_discharge_to_grid_power": round(force_discharge_power, 2),
        "allow_grid_heating": allow_grid_heating,
        "time_series": results
    }


