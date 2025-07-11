# PowerStreamPlan Add-on Repository

PowerStreamPlan – inteligentní optimalizátor spotřeby a výroby energie v domácnosti pomocí MPC (Model Predictive Control) pro Home Assistant.

## Instalace Add-on

### Automatická instalace přes repozitář

1. V Home Assistant, jděte do **Nastavení** > **Doplňky** > **Obchod s doplňky**
2. Klikněte na tři tečky v pravém horním rohu a vyberte **Repozitáře**
3. Přidejte URL tohoto repozitáře: `https://github.com/filipek92/PowerStreamPlan`
4. Najděte **PowerStreamPlan** v seznamu doplňků a klikněte na **Instalovat**
5. Po instalaci klikněte na **Spustit**

### Konfigurace

Po instalaci nakonfigurujte addon:

1. V konfiguraci addonu nastavte:
   - **ha_url**: URL vašeho Home Assistant (obvykle `http://homeassistant:8123`)
   - **token**: Long-lived access token z Home Assistant

2. Spusťte addon

3. Addon bude dostupný v bočním panelu Home Assistant jako **PowerStreamPlan**

## Popis projektu
Tento projekt slouží k optimalizaci řízení domácí energetiky (baterie, dvouzónový bojler, FVE, nákup/prodej elektřiny) s využitím lineárního MPC. Výsledky jsou vizualizovány a lze je publikovat do Home Assistant.

## Hlavní komponenty
- **powerplan_server.py** – Flask server s webovým rozhraním a plánovačem periodických výpočtů.
- **powerplan_optimizer.py** – Lineární MPC optimalizátor (PuLP) s dvouzónovým modelem nádrže.
- **data_connector.py** – Příprava vstupních dat a publikace výsledků do Home Assistant.
- **presentation.py** – Vizualizace výsledků pomocí Plotly.
- **actions.py** – Převod optimalizačních výsledků na konkrétní akce pro Home Assistant.
- **powerplan_settings.py** – Webové rozhraní pro nastavení parametrů optimalizátoru.
- **models/** – Modely pro předpovědi a výpočty (FVE, spotřeba, ceny, tepelné ztráty atd.).

## Webové rozhraní
Po spuštění addonu je dostupné přes Home Assistant ingress nebo přímo na portu 26781.

## Hlavní endpointy
- `/` – Hlavní stránka s vizualizací a možností ručního přegenerování výsledků.
- `/regenerate` – POST endpoint pro ruční spuštění optimalizace.
- `/settings` – Stránka pro nastavení parametrů optimalizátoru.

## Plánování výpočtů
Optimalizace se automaticky spouští každých 5 minut pomocí APScheduleru.

## Konfigurace
- **options.json** – Parametry a nastavení systému (v HOME ASSISTANT data složce).
- **powerplan_settings.json** – Uživatelské nastavení parametrů optimalizátoru.
- **credentials.yaml** – Přihlašovací údaje (fallback pro Home Assistant).

## Výsledky
- **results/** – Výsledky optimalizace (cache) s časovými značkami.
- **results/latest.json** – Symbolická vazba na nejnovější výsledek.
- **results/latest.csv** – CSV export nejnovějšího výsledku.

## Závislosti
- Python 3.10+
- Flask
- Flask-APScheduler
- PuLP
- Plotly

Všechny závislosti jsou uvedeny v `requirements.txt`.

## Licence
Projekt je určen pro osobní a výukové účely.

## Dokumentace

### Detailní dokumentace
- **[MPC Model](docs/MPC_Model.md)** – Detailní popis modelu MPC optimalizátoru
- **[Optimization](docs/Optimization.md)** – Optimalizační kritéria a penalizace
