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

## Detailní dokumentace modelu MPC

### Přehled

Model v `home_mpc.py` implementuje lineární optimalizaci pro řízení domácí energetiky (MPC – Model Predictive Control). Cílem je minimalizovat náklady na energii a efektivně využívat baterii, bojler, fotovoltaiku a síť v rámci zadaného časového horizontu.

### Vstupy modelu

Vstupy jsou rozděleny do tří skupin:

- **series** (časové řady, vektory pro každý krok):
  - `tuv_demand` – spotřeba TUV [kWh]
  - `heating_demand` – spotřeba na vytápění [kWh]
  - `fve_pred` – predikce výroby FVE [kW]
  - `buy_price` – cena nákupu elektřiny [Kč/kWh]
  - `sell_price` – výkupní cena [Kč/kWh]
  - `load_pred` – základní spotřeba domácnosti [kW]

- **initials** (počáteční stavy, skaláry):
  - `bat_soc` – počáteční stav nabití baterie [%]
  - `boiler_E` – počáteční energie v bojleru [kWh]

- **options** (volitelné přepínače a parametry):
  - `heating_enabled` – zapnutí vytápění (bool, default: False)
  - Přepsání parametrů systému (viz níže)

### Parametry systému (lze přepsat v `options`)

- `B_CAP` – kapacita baterie [kWh] (default: 17.4)
- `B_MIN` – minimální SOC baterie [kWh] (default: 15 % z kapacity)
- `B_MAX` – maximální SOC baterie [kWh] (default: kapacita)
- `B_POWER` – max. výkon baterie [kW] (default: 9)
- `B_EFF_IN` – účinnost nabíjení (default: 0.94)
- `B_EFF_OUT` – účinnost vybíjení (default: 0.94)
- `H_CAP` – kapacita bojleru [kWh] (default: 81.0)
- `H_POWER` – max. příkon ohřevu [kW] (default: 12)
- `GRID_LIMIT` – hlavní jistič [kW] (default: 18)
- `INVERTER_LIMIT` – limit měniče [kW] (default: 15)
- `battery_penalty` – penalizace za vybíjení baterie [Kč/kWh] (default: 0)
- `upper_zone_priority` – bonus za ohřev horní části nádrže [Kč/kWh] (default: 0.5)
- `BAT_THRESHOLD_PCT` – práh pro rozdělení SOC (default: 0.40)
- `BAT_PRICE_BELOW`, `BAT_PRICE_ABOVE` – ceny pro penalizaci/odměnu koncového SOC
- `final_boler_price` – cena pro penalizaci/odměnu zbylé energie v bojleru

### Kritéria (Cílová funkce)

Model minimalizuje celkové náklady:

- **Nákup elektřiny**: součet `G_buy[t] * buy_price[t]`
- **Prodej elektřiny**: odečtení `G_sell[t] * sell_price[t]`
- **Penalizace baterie**: penalizace za vybíjení (degradace)
- **Odměna/penalizace za koncový SOC baterie**:
  - Odměna za energii NAD práh (např. 60 % SOC)
  - Penalizace za energii POD prahem
- **Odměna/penalizace za zbylou energii v bojleru** (motivace k využití levné energie)

### Podmínky (Constraints)

#### Bilance výkonu (v každém kroku):

```
fve_pred[t] + G_buy[t] + B_discharge[t] * B_EFF_OUT
= load_pred[t] + B_charge[t] / B_EFF_IN + H_in[t] + G_sell[t]
```

#### Technologická omezení:

- Výkonové limity baterie, bojleru, sítě, měniče
- SOC baterie a bojleru v povoleném rozsahu
- Omezena možnost nabíjení/vybíjení a ohřevu v jednom kroku

#### Tepelná bilance bojleru:

- Zohledňuje spotřebu TUV, případně vytápění, a tepelné ztráty (modelováno funkcí `estimate_heating_losses`)

#### Dynamika zásobníků:

- SOC baterie a bojleru se aktualizuje podle předchozího stavu, nabíjení/vybíjení a ztrát

#### Dvoudílné rozdělení koncového SOC baterie:

- Práh (např. 60 % SOC) rozděluje koncový stav na „short“ a „surplus“ pro účely penalizace/odměny

### Výstupy modelu

- Časové řady optimalizovaných veličin (výkony, SOC, proudy, nákupy/prodeje, ohřev)
- Souhrnné výsledky pro první krok (pro převod na akce)
- Metadata o vstupu a nastavení
