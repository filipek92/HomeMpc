#!/usr/bin/env python3

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
    hours
):
    indexes = range(len(hours))

    # --- Parametry systému ---
    B_CAP = 17.4
    B_MIN = B_CAP * 0.30
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
    B_power = LpVariable.dicts("B_power", indexes, -B_POWER, B_POWER)
    B_SOC = LpVariable.dicts("B_SOC", indexes, B_MIN, B_MAX)
    H_store_top = LpVariable.dicts("H_store_top", indexes, 0, H_POWER_TOP)
    H_store_bottom = LpVariable.dicts("H_store_bottom", indexes, 0, H_POWER_BOTTOM)
    G_buy = LpVariable.dicts("G_buy", indexes, 0)
    G_sell = LpVariable.dicts("G_sell", indexes, 0)
    H_SOC = LpVariable.dicts("H_SOC", indexes, 0, H_CAP)
    H_out = LpVariable.dicts("H_out", indexes, 0)

    # Pomocné proměnné pro LP rozdělení nabíjení/vybíjení:
    B_charge = LpVariable.dicts("B_charge", indexes, 0, B_POWER)
    B_discharge = LpVariable.dicts("B_discharge", indexes, 0, B_POWER)
    for t in indexes:
        # V každé hodině: B_power = B_charge - B_discharge
        prob += B_power[t] == B_charge[t] - B_discharge[t]

    # --- Cílová funkce ---
    final_boiler_price = min(buy) - 1.5 # Cena za jednotku energie v SOC bojleru
    final_bat_price = min(buy) - 2 # Cena za jednotku energie v SOC bojleru
    prob += lpSum([G_buy[t]*buy[t] - G_sell[t]*sell[t] for t in indexes])  - final_bat_price * H_SOC[max(indexes)] - final_boiler_price * H_SOC[max(indexes)]

    #prob += H_SOC[max(indexes)] >= 0.8 * H_CAP

    # --- Omezující podmínky ---
    for t in indexes:
        h_total = H_store_top[t] + H_store_bottom[t]
        
        # Energetická bilance
        prob += (
            fve[t] + G_buy[t] + B_discharge[t]*B_EFF_OUT == load[t] + B_charge[t]/B_EFF_IN + h_total + G_sell[t]
        )

        # SOC baterie - vždy v povoleném rozsahu (už je v deklaraci B_SOC)
        # Příkon hlavního jističe
        prob += G_buy[t] + B_charge[t] + h_total <= GRID_LIMIT

        # Výkon střídače
        prob += B_discharge[t] + h_total + G_sell[t] <= INVERTER_LIMIT

        # Výdej tepla z nádrže = požadavek na vytápění
        prob += H_out[t] == tuv_demand[t] + (heating_demand[t] * (1 if heating_enabled else 0))

        print(f"t={t}, H_SOC[t]={H_SOC[t]}, H_CAP={H_CAP}, H_store_top[t]={H_store_top[t]}, H_store_bottom[t]={H_store_bottom[t]}, H_out[t]={H_out[t]}")

        # Před výpočtem bilance pro nádrž
        loss = estimate_heating_losses(
            H_SOC[t-1] if t > 0 else soc_boiler_init,
            H_CAP,
            T_ambient=20,
            cirk_time=0.3
        )

        # Bilance baterie a nádrže
        if t == 0:
            prob += B_SOC[t] == soc_bat_init + B_charge[t]*B_EFF_IN - B_discharge[t]/B_EFF_OUT
            prob += H_SOC[t] == soc_boiler_init + H_store_top[t] + H_store_bottom[t] - H_out[t]
        else:
            prob += B_SOC[t] == B_SOC[t-1] + B_charge[t]*B_EFF_IN - B_discharge[t]/B_EFF_OUT
            prob += H_SOC[t] == H_SOC[t-1] + H_store_top[t] + H_store_bottom[t] - H_out[t] - loss


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

    min_soc_battery = min([B_SOC[t].varValue for t in indexes])
    max_boiler_energy = max([H_SOC[t].varValue for t in indexes])

    def energy_to_temp(kwh, portion):
        return 45 + (kwh / (portion * 4.18 * 1)) * 3600 / 1000

    target_temp_top = min(90, energy_to_temp(max_boiler_energy * 0.33, 333))
    target_temp_rest = min(65, energy_to_temp(max_boiler_energy * 0.67, 667))

    force_discharge_power = max([G_sell[t].varValue - fve[t] for t in indexes])
    allow_grid_heating = any([G_buy[t].varValue > 0.2 and (H_store_top[t].varValue + H_store_bottom[t].varValue) > 0.2 for t in indexes])
    allow_grid_export = any([G_sell[t].varValue > 0.2 for t in indexes])

    results = {
        "B_power": [B_power[t].varValue for t in indexes],
        "B_SOC": [B_SOC[t].varValue for t in indexes],
        "B_SOC_percent": [100 * B_SOC[t].varValue / B_MAX for t in indexes],
        "H_SOC": [H_SOC[t].varValue for t in indexes],
        "H_SOC_percent": [100 * H_SOC[t].varValue / H_CAP for t in indexes],
        "H_store_top": [H_store_top[t].varValue for t in indexes],
        "H_store_bottom": [H_store_bottom[t].varValue for t in indexes],
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
        "min_soc_battery": round(min_soc_battery, 2),
        "target_temp_top": round(target_temp_top, 1),
        "target_temp_rest": round(target_temp_rest, 1),
        "allow_grid_export": allow_grid_export,
        "force_discharge_to_grid_power": round(force_discharge_power, 2),
        "allow_grid_heating": allow_grid_heating,
        "time_series": results
    }


