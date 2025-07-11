def get_tuv_demand(time):
    """
    Vrací očekávanou spotřebu TUV (kWh) v dané celé hodině.
    Přiřazuje spotřebu podle scénáře:
      - 6:00–6:59 sprcha (1,2 kWh)
      - 7:00–7:59 čištění zubů (0,05 kWh)
      - 15:00–15:59 sprcha (1,0 kWh)
      - 18:00–18:59 dvě vany (5,0 kWh)
    Jinak 0.0
    """
    hour = time.hour

    if hour == 6:
        return 1.2   # sprcha
    elif hour == 7:
        return 0.05  # čištění zubů
    elif hour == 15:
        return 1.0   # sprcha
    elif hour == 18:
        return 5.0   # dvě vany
    else:
        return 0.0