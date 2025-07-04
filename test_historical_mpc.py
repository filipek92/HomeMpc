import requests
import pandas as pd
from datetime import datetime, timedelta
from home_mpc import run_mpc_optimizer
from presentation_matplotlib import presentation_matplotlib
import sys

# --- Parametry testu ---
# Zde nastav datum a časový rozsah pro test
START_DATE = "2024-06-01"
END_DATE = "2024-06-02"
EUR_CZK = 25.0  # kurz pro převod

# --- Stažení historických dat z OTE (JSON endpoint) ---
def fetch_ote_prices(start_date, end_date):
    """Stáhne hodinové ceny z OTE ČR (DAM, EUR/MWh) z JSON endpointu a převede na CZK/kWh."""
    prices = []
    hours = []
    d = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    while d < end:
        url = f"https://www.ote-cr.cz/cs/kratkodobe-trhy/elektrina/denni-trh/@@chart-data?report_date={d.strftime('%Y-%m-%d')}&time_resolution=PT60M"
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Chyba při stahování OTE JSON pro {d.date()}: {r.status_code}")
        data = r.json()
        # Ceny jsou v data['dataLine'][1]['point']
        price_points = data["data"]["dataLine"][1]["point"]
        for i, pt in enumerate(price_points):
            eur_mwh = float(pt["y"])
            czk_kwh = eur_mwh * EUR_CZK / 1000  # EUR/MWh -> CZK/kWh
            prices.append(czk_kwh)
            h = datetime(d.year, d.month, d.day, i)
            hours.append(h)
        d += timedelta(days=1)
    return hours, prices

def fetch_weather(hours, lat=50.1, lon=14.4):
    """Stáhne teplotu z open-meteo.com pro dané hodiny."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&start={hours[0].strftime('%Y-%m-%dT%H:%M')}&end={hours[-1].strftime('%Y-%m-%dT%H:%M')}&timezone=Europe%2FBerlin"
    r = requests.get(url)
    data = r.json()
    temps = data["hourly"]["temperature_2m"][:len(hours)]
    return temps

def fetch_fve(hours, lat=50.1, lon=14.4, pv_kwp=10.0, eff=0.18):
    """Stáhne globální solární radiaci a převede na odhad výroby FVE v kW."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=shortwave_radiation&start={hours[0].strftime('%Y-%m-%dT%H:%M')}&end={hours[-1].strftime('%Y-%m-%dT%H:%M')}&timezone=Europe%2FBerlin"
    r = requests.get(url)
    data = r.json()
    # shortwave_radiation je v Wh/m2 za hodinu
    sw = data["hourly"]["shortwave_radiation"][:len(hours)]
    # Výpočet: výkon = radiace * plocha * účinnost / 1000 (kW)
    # Plocha panelů = instalovaný výkon / účinnost
    area = pv_kwp * 1000 / (eff * 1000)  # m2
    fve = [val * area * eff / 1000 for val in sw]  # kW
    return fve

if __name__ == "__main__":
    # Zpracování argumentu pro datum
    if len(sys.argv) > 1:
        datum = sys.argv[1]
        try:
            start_dt = datetime.strptime(datum, "%Y-%m-%d")
        except ValueError:
            print("Použij formát: YYYY-MM-DD")
            sys.exit(1)
    else:
        start_dt = datetime.now() - timedelta(days=1)
    START_DATE = start_dt.strftime("%Y-%m-%d")
    END_DATE = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Stahuji historická data z OTE pro {START_DATE}...")
    hours, buy_price = fetch_ote_prices(START_DATE, END_DATE)
    sell_price = [p - 0.5 for p in buy_price]  # dummy feed-in tarif
    outdoor_temps = fetch_weather(hours)
    fve_pred = fetch_fve(hours)
    load_pred = [1.5 for _ in hours]  # dummy spotřeba
    tuv_demand = [0.2 for _ in hours]  # dummy TUV
    heating_demand = [0.1 for _ in hours]  # dummy vytápění

    series = {
        "tuv_demand": tuv_demand,
        "heating_demand": heating_demand,
        "fve_pred": fve_pred,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "load_pred": load_pred,
        "outdoor_temps": outdoor_temps,
    }
    initials = {"bat_soc": 50, "boiler_E": 20}

    solution = run_mpc_optimizer(series, initials, list(hours))

    # Vizualizace výsledků pomocí matplotlib
    presentation_matplotlib(solution)
