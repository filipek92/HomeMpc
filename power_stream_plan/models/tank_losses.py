def estimate_heating_losses(H_SOC_var, H_CAP, T_ambient=20, cirk_time=0.3):
    # Vše jsou LpVariable nebo konstanty!
    # Předpokládejme H_SOC_var [kWh], H_CAP [kWh]
    # Výstupem je LpAffineExpression!
    T_tank = 45 + (H_SOC_var / H_CAP) * (80 - 45)
    k_tank = 0.002   # kW/°C
    k_circ = 0.006   # kW/°C
    loss_tank = k_tank * (T_tank - T_ambient)
    loss_circ = k_circ * (T_tank - T_ambient) * cirk_time
    return loss_tank + loss_circ
