# Chování a režimy provozu Solax X3 G4

Solax X3 G4 je hybridní střídač podporující širokou škálu provozních režimů, které lze v Home Assistant ovládat a sledovat pomocí HTTP API a Modbus integrace.

## 1. Stav Invertoru
`sensor.solax_run_mode` ukazuje aktuální stav invertoru: **Normal Mode**, **Off-Grid**, **Waiting**, **Checking**, **Idle**
- **Normal Mode**: standardní grid-tie provoz, export přebytků do sítě
- **Off-Grid**: provoz mimo síť (EPS), zásobování připojených spotřebičů z baterie
- **Waiting**: vyčkávací stav při přepínání nebo před spouštěním režimu
- **Checking**: interní kontrola a diagnostika invertoru před přechodem do provozu
- **Idle**: inaktivní stav bez výroby ani spotřeby

## 2. Režimy provozu
`select.solax_charger_use_mode` určuje, jak se invertor chová při rozdělení výroby mezi domácnost, baterie a síť:

### a) Backup Mode (Zálohovací režim)
- Invertor udržuje v baterii rezervu energie pro případ výpadku sítě.
- Priorita zdrojů: Domácí spotřeba → Baterie → Prodej do sítě.
- Při poklesu SOC na hodnotu `number.solax_backup_discharge_min_soc` invertor přestává vybíjet přes síť a zůstává připraven k zajištění EPS.
- Noční dobíjení ze sítě probíhá do úrovně `number.solax_backup_nightcharge_upper_soc` podle plánu (pokud je aktivní).

### b) Self-Use Mode (Režim vlastní spotřeby)
- Cílem je maximalizovat okamžitou domácí spotřebu solární energie.
- Priorita zdrojů: Domácí spotřeba → Baterie → Prodej do sítě.
- Při vyčerpání rezervy (pod `number.solax_selfuse_discharge_min_soc`) invertor přejde do stavu Idle a přestane vybíjet.

### c) Feed-In Priority (Režim preferovaného exportu)
- Upřednostňuje prodej přebytků do sítě před ukládáním do baterie.
- Priorita zdrojů: Domácí spotřeba → Prodej do sítě → Baterie.
- Pokud dosáhne uživatelského limitu exportu (`number.solax_export_control_user_limit`), zbylá energie je ukládána do baterie.

### d) Manual Mode (Ruční režim)
- Uživatel může ručně přepnout invertor do nabíjení nebo vybíjení bez ohledu na automatiku.
- Volba přes `select.solax_manual_mode_select`: **Stop Charge and Discharge** / **Force Charge** / **Force Discharge**.
- **Stop Charge and Discharge** - baterie v klidu.
- **Force Charge** – invertor nabíjí baterii z FV a/nebo sítě až do hranice `number.solax_battery_charge_max_current`.
- **Force Discharge** – invertor vybíjí baterii pro napájení domu a/nebo sítě až do hranice `number.solax_battery_discharge_max_current`.

## 3. EPS (Emergency Power Supply)
- Automatický nouzový provoz mimo síť při výpadku veřejné distribuční sítě.
- Aktivuje se, pokud `sensor.solax_grid_status` = OffGrid a invertor není v režimu Idle.
- Napájí zálohovanou část domu výstupem EPS.
- Parametry a stav:
  - `select.solax_eps_mode_without_battery` – umožňuje EPS režim i bez nainstalované baterie (může být nestabilní)
  - `select.solax_eps_mute` – potlačuje pípání invertoru v EPS režimu
  - Statistiky provozu: `sensor.solax_eps_mode_runtime`, `sensor.solax_eps_yield_total`.

## 4. Konfigurace
Nastavení chování invertoru lze měnit přímo z Home Assistant:

- `select.solax_charger_use_mode` – výběr režimu provozu (Backup, Self-Use, Feed-In)
- `number.solax_backup_discharge_min_soc` – min. SOC pro zálohovací režim [%]
- `number.solax_backup_nightcharge_upper_soc` – max. SOC pro noční dobíjení v Backup Mode [%]
- `number.solax_selfuse_discharge_min_soc` – min. SOC pro režim vlastní spotřeby [%]
- `number.solax_export_control_user_limit` – max. vývozní výkon do sítě [W] (doporučeno nastavit nižší než limit distributora)
- `number.solax_battery_charge_max_current` – max. proud pro nabíjení baterie [A] (neměnit bez konzultace)
- `number.solax_battery_discharge_max_current` – max. proud pro vybíjení baterie [A] (neměnit bez konzultace)
- `select.solax_manual_mode_control` – aktivuje/deaktivuje manuální režim
- `select.solax_manual_mode_select` – chování manuálního režimu (Auto/Force Charge/Force Discharge)
- `select.solax_pgrid_bias` – nastavení preference: Inverter (menší přetok do sítě) / Grid (menší odběr ze sítě)
- `select.solax_phase_power_balance_x3` – vyrovnávání výkonu mezi fázemi podle zatížení
- `select.solax_selfuse_mode_backup` – zapne zálohovací režim v Self-Use módu
- `number.solax_selfuse_nightcharge_upper_soc` – horní SOC pro noční dobíjení v Self-Use módu
- `select.solax_selfuse_night_charge_enable` – povoluje noční dobíjení v Self-Use módu

