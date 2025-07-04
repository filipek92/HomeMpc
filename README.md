# HomeOptim

Optimalizace spotřeby a výroby energie v domácnosti pomocí MPC (Model Predictive Control).

## Popis projektu
Tento projekt slouží k optimalizaci řízení domácí energetiky (baterie, bojler, FVE, nákup/prodej elektřiny) s využitím lineárního MPC. Výsledky jsou vizualizovány a lze je publikovat do Home Assistant.

## Hlavní komponenty
- **mpc_server.py** – Flask server s webovým rozhraním a plánovačem periodických výpočtů.
- **home_mpc.py** – Lineární MPC optimalizátor (PuLP).
- **data_connector.py** – Příprava vstupních dat a publikace výsledků do Home Assistant.
- **presentation.py** – Vizualizace výsledků pomocí Plotly.
- **actions.py** – Převod optimalizačních výsledků na konkrétní akce pro Home Assistant.
- **models/** – Modely pro předpovědi a výpočty (FVE, spotřeba, ceny, tepelné ztráty atd.).

## Spuštění

1. **Instalace závislostí:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Spuštění serveru:**
   ```bash
   python mpc_server.py
   ```
   Server poběží na portu 26781 (lze změnit proměnnou prostředí `PORT`).

3. **Webové rozhraní:**
   Otevřete prohlížeč na adrese [http://localhost:26781](http://localhost:26781)

## Hlavní endpointy
- `/` – Hlavní stránka s vizualizací a možností ručního přegenerování výsledků.
- `/regenerate` – POST endpoint pro ruční spuštění optimalizace.

## Plánování výpočtů
Optimalizace se automaticky spouští každých 5 minut pomocí APScheduleru.

## Konfigurace
- **config.yaml** – Parametry a nastavení systému.
- **credentials.yaml** – Přihlašovací údaje (např. pro Home Assistant).

## Výsledky
- **mpc_results_cache.json** – Poslední výsledek optimalizace (cache).

## Závislosti
- Python 3.10+
- Flask
- Flask-APScheduler
- PuLP
- Plotly

Všechny závislosti jsou uvedeny v `requirements.txt`.

## Licence
Projekt je určen pro osobní a výukové účely.
