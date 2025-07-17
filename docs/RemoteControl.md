# Solax RemoteControl - Modbus Power Control

## Úvod

RemoteControl je pokročilá funkce pro Solax Gen4 hybridní střídače, která umožňuje přímé řízení výkonu přes Modbus protokol. Na rozdíl od standardních power control příkazů, které se ukládají do EEPROM, RemoteControl příkazy jsou dočasné a mohou být volány libovolně často bez rizika opotřebení paměti.

## Výhody RemoteControl

### 1. Bez omezení na zápisy
- **Standardní řízení**: Ukládá se do EEPROM → omezený počet zápisů (nevhodné pro automatizace)
- **RemoteControl**: Dočasné příkazy v RAM → neomezený počet zápisů
- **Ideální pro**: Časté změny v automatizacích (každých 5-60 sekund)

### 2. Životní cyklus příkazů
- **Doba platnosti**: Omezená (standardně 20 sekund)
- **Autorepeat**: Automatické obnovování příkazů v definovaných intervalech
- **Flexibilita**: Možnost okamžitého zastavení nebo změny režimu

### 3. Emulace standardních režimů
- **Self Use Mode**: Emulace standardního režimu vlastní spotřeby
- **Feedin Priority**: Emulace režimu preferovaného exportu
- **Grid Control**: Přímé řízení výkonu na síťovém rozhraní
- **Battery Control**: Přímé řízení výkonu na bateriové rozhraní

## Dostupné parametry

### Hlavní ovládací entita
- **`remotecontrol_trigger`**: Tlačítko pro aktivaci nového RemoteControl slotu

### Konfigurace řízení
- **`remotecontrol_power_control`**: Režim řízení výkonu
  - `"Disabled"` - vypnuto
  - `"Enabled Power Control"` - přímé řízení aktivního výkonu
  - `"Enabled Grid Control"` - řízení výkonu na síťovém rozhraní
  - `"Enabled Battery Control"` - řízení výkonu na bateriové rozhraní  
  - `"Enabled Self Use"` - emulace self-use režimu
  - `"Enabled Feedin Priority"` - emulace feedin priority režimu
  - `"Enabled No Discharge"` - zákaz vybíjení baterie

### Výkonové parametry
- **`remotecontrol_active_power`**: Cílový aktivní výkon (W)
  - Kladné hodnoty = nabíjení/import
  - Záporné hodnoty = vybíjení/export
  - Automaticky omezeno na rozsah `active_power_lower` až `active_power_upper`

- **`remotecontrol_reactive_power`**: Reaktivní výkon (doporučeno ponechat 0)

### Časové parametry
- **`remotecontrol_duration`**: Doba platnosti příkazu (sekundy, výchozí 20s)
- **`remotecontrol_autorepeat_duration`**: Doba automatického opakování (sekundy, 0 = vypnuto)

### Limity
- **`remotecontrol_import_limit`**: Maximální import ze sítě (W)
- **`remotecontrol_set_type`**: Typ operace (`"Set"` nebo `"Update"`)

## Principy fungování

### Grid Control vs Battery Control
```
Grid Control (remotecontrol_active_power = 2000W):
- Cíl: Import 2000W ze sítě
- Baterie se přizpůsobí podle dostupnosti FVE a domácí spotřeby

Battery Control (remotecontrol_active_power = 2000W):
- Cíl: Nabíjení baterie 2000W
- Síť se přizpůsobí podle dostupnosti FVE a domácí spotřeby
```

### Aktivní výkon (Active Power)
Solax definuje aktivní výkon jako:
```
Active Power = Grid_Import - House_Load
Active Power = Battery_Charge - PV_Power
```

## Monitorovací senzory

### Stav RemoteControl
- **`modbus_power_control`**: Aktuální stav modbus power control
- **`target_finish_flag`**: Příznak dokončení cíle
- **`remotecontrol_autorepeat_remaining`**: Zbývající čas autoreopakování

### Výkonové hodnoty
- **`active_power_target`**: Cílový aktivní výkon
- **`reactive_power_target`**: Cílový reaktivní výkon
- **`active_power_real`**: Skutečný aktivní výkon
- **`reactive_power_real`**: Skutečný reaktivní výkon

### Limity výkonu
- **`active_power_upper`**: Horní limit aktivního výkonu
- **`active_power_lower`**: Dolní limit aktivního výkonu
- **`reactive_power_upper`**: Horní limit reaktivního výkonu
- **`reactive_power_lower`**: Dolní limit reaktivního výkonu

## Příklad použití

### Základní nabíjení baterie
```yaml
# Nastavení parametrů
- service: select.select_option
  data:
    option: "Enabled Battery Control"
  target:
    entity_id: select.solax_remotecontrol_power_control

- service: number.set_value
  data:
    value: 3000  # 3kW nabíjení
  target:
    entity_id: number.solax_remotecontrol_active_power

- service: number.set_value
  data:
    value: 3600  # 1 hodina autorepeat
  target:
    entity_id: number.solax_remotecontrol_autorepeat_duration

# Aktivace
- service: button.press
  target:
    entity_id: button.solax_remotecontrol_trigger
```

### Řízení importu ze sítě
```yaml
# Grid Control - přesný import 1kW ze sítě
- service: select.select_option
  data:
    option: "Enabled Grid Control"
  target:
    entity_id: select.solax_remotecontrol_power_control

- service: number.set_value
  data:
    value: 1000  # 1kW import
  target:
    entity_id: number.solax_remotecontrol_active_power

- service: number.set_value
  data:
    value: 10000  # Vysoký import limit
  target:
    entity_id: number.solax_remotecontrol_import_limit

- service: button.press
  target:
    entity_id: button.solax_remotecontrol_trigger
```

## Hodnocení užitečnosti pro PowerStreamPlan

### ✅ Výhody pro náš systém

1. **Přesné řízení výkonu**
   - Aktuální systém používá pouze režimy (Manual Charge/Discharge, Feedin Priority)
   - RemoteControl umožňuje přesné nastavení výkonu (např. 2.5kW místo jen "nabíjení")
   - Lépe odpovídá výstupům MPC optimalizátoru

2. **Vysoká frekvence aktualizací**
   - MPC běží každých 5-15 minut
   - RemoteControl může být aktualizován bez omezení
   - Autorepeat zajistí kontinuitu bez zásahu automatizace

3. **Jemnější kontrola**
   - Grid Control: Přesné řízení importu/exportu
   - Battery Control: Přesné řízení nabíjení/vybíjení
   - Import/Export limity pro peak shaving

4. **Lepší integrace s MPC**
   - MPC optimalizátor počítá přesné výkony (b_charge, b_discharge, g_buy, g_sell)
   - RemoteControl může tyto hodnoty přímo použít
   - Eliminuje diskrétní přepínání mezi režimy

### ⚠️ Nevýhody a omezení

1. **Pouze Gen4 střídače**
   - Aktuálně podporuje jen Solax Gen4
   - Gen3 podpora "bude dokumentována později"

2. **Asymetrická distribuce výkonu**
   - **KRITICKÉ**: RemoteControl rozděluje výkon symetricky mezi 3 fáze (výkon/3 na každou fázi)
   - **Problém**: Při asymetrickém zatížení domácnosti může dojít k neočekávanému chování
   - **Dopad**: Může způsobit nevyvážené fáze a problémy s bilancí výkonu
   - **Řešení**: Nutno zohlednit při výpočtech MPC optimalizátoru

   **Analýza dopadu pro ČR:**
   - **Účtování v ČR**: **FÁZOVĚ** - od roku 2011 se v ČR měří elektřina po fázích (vyhláška 359/2020):
     - **Důsledek**: Energie dodaná do sítě na jedné fázi je považována za přetok, energie odebraná ze sítě na jiné fázi za standardní odběr
     - **Příklad**: Pokud z L1 odeberete 3kW a na L2 dodáte 3kW, v Polsku/Německu jste na nule, v ČR platíte distribuční poplatky za 3kW odběr
     - **Evropský kontext**: ČR je jednou z posledních zemí EU s tímto systémem (podobně Portugalsko, část Slovenska)
   - **Novela Lex OZE II (2024)**: Zavedení principu "sdílím sám sobě":
     - **Výhoda**: Energie dodaná do sítě z jedné fáze se započítá do spotřeby i na ostatních fázích
     - **Omezení**: Úspora jen na ceně silové elektřiny (40-50%), regulovanou složku si musíte fakturovat sami sobě
     - **Stále platí**: Fázové měření podle vyhlášky 359/2020, součtové hodnocení jen pro sdílení
   - **Reálný dopad**: Asymetrie má v ČR vždy finanční dopad kvůli fázovému měření:
     - Neoptimální využití FVE při asymetrickém zatížení
     - Možné problémy s jištěním jednotlivých fází
     - Zvýšené ztráty v síti při nevyváženém zatížení
   - **Praktické scénáře**:
     - **Vysoké zatížení L1** (např. indukční deska): RemoteControl dá 1/3 výkonu na L1 → nedostatečné
     - **Nízké zatížení L2,L3**: RemoteControl dá zbytečně výkon i na tyto fáze
     - **Výsledek**: Neoptimální distribuce může vést k importu na L1 a exportu na L2/L3 současně

3. **Složitost implementace**
   - Více parametrů k nastavení
   - Nutnost pochopení Active Power konceptu
   - Autorepeat management

4. **Závislost na Home Assistant integraci**
   - Potřeba nejnovější verze homeassistant-solax-modbus
   - Možné problémy s kompatibilitou

### 🔧 Doporučení pro implementaci

1. **Postupná migrace**
   - Zachovat současný systém jako fallback
   - Přidat RemoteControl jako volitelnou funkci
   - Testovat stabilitu před plným nasazením

2. **Konfigurace**
   - Přidat možnost výběru řídícího režimu (Current/RemoteControl)
   - Autodetekce podpory RemoteControl
   - Konfigurovatelné autorepeat interval

3. **Řešení asymetrie fází**
   - **Monitorování**: Sledovat výkon jednotlivých fází
   - **Kompenzace**: Zohlednit symetrické rozdělení ve výpočtech
   - **Limity**: Nastavit konzervativnější limity pro vyhnutí se přetížení fází
   - **Fallback**: Při detekci problémů s asymetrií přepnout na standardní režimy

   **Specifika pro ČR:**
   - **Monitorování fází**: Využít senzory `sensor.solax_phase_a_power`, `sensor.solax_phase_b_power`, `sensor.solax_phase_c_power`
   - **Detekce asymetrie**: Výpočet rozdílu mezi nejvyšší a nejnižší fází
   - **Práh asymetrie**: Pokud rozdíl > 1kW, preferovat standardní režimy (minimalizace distribučních poplatků)
   - **Optimalizace**: RemoteControl používat pouze při symetrickém zatížení (rozdíl fází < 1kW)
   - **Časové okna**: Využít při nočním období (22:00-06:00) kdy je zatížení obvykle symetričtější

4. **Vylepšení actions.py**
   ```python
   def use_remotecontrol(sol, slot_index):
       # Převod MPC výstupů na RemoteControl s ohledem na asymetrii
       target_power = 0
       
       if sol["outputs"]["b_charge"][slot_index] > 0.1:
           target_power = sol["outputs"]["b_charge"][slot_index] * 1000
           mode = "Enabled Battery Control"
       elif sol["outputs"]["b_discharge"][slot_index] > 0.1:
           target_power = -sol["outputs"]["b_discharge"][slot_index] * 1000
           mode = "Enabled Battery Control"
       
       # POZOR: RemoteControl rozděluje výkon/3 na každou fázi
       # Při asymetrickém zatížení může dojít k problémům
       max_phase_power = target_power / 3
       
       return {
           "mode": mode,
           "active_power": target_power,
           "duration": 900,  # 15 minut
           "note": f"Výkon {max_phase_power:.0f}W na fázi"
       }
   ```

   **Rozšířený kód pro ČR:**
   ```python
   def use_remotecontrol_cz(sol, slot_index, phase_powers):
       """
       RemoteControl s kontrolou asymetrie fází pro české podmínky
       
       Args:
           sol: MPC řešení
           slot_index: Index časového slotu
           phase_powers: [L1_power, L2_power, L3_power] - aktuální výkony fází
       """
       # Kontrola asymetrie fází
       max_phase = max(phase_powers)
       min_phase = min(phase_powers)
       asymmetry = max_phase - min_phase
       
       # Pokud je asymetrie > 1kW, nepoužívat RemoteControl
       if asymmetry > 1000:  # 1kW práh pro minimalizaci distribučních poplatků
           return {"use_remotecontrol": False, "reason": "Asymetrie způsobí vyšší distribuční poplatky"}
       
       # Výpočet cílového výkonu
       target_power = 0
       if sol["outputs"]["b_charge"][slot_index] > 0.1:
           target_power = sol["outputs"]["b_charge"][slot_index] * 1000
           mode = "Enabled Battery Control"
       elif sol["outputs"]["b_discharge"][slot_index] > 0.1:
           target_power = -sol["outputs"]["b_discharge"][slot_index] * 1000
           mode = "Enabled Battery Control"
       
       # Kontrola, zda nedojde k přetížení fáze
       power_per_phase = target_power / 3
       max_resulting_phase = max(phase_powers) + power_per_phase
       
       if max_resulting_phase > 7000:  # 7kW limit na fázi (30A jistič)
           return {"use_remotecontrol": False, "reason": "Riziko přetížení fáze"}
       
       return {
           "use_remotecontrol": True,
           "mode": mode,
           "active_power": target_power,
           "duration": 900,
           "asymmetry_kw": asymmetry / 1000,
           "power_per_phase": power_per_phase
       }
   ```

## Závěr

RemoteControl je užitečná funkce pro PowerStreamPlan s omezeními, která jsou v českých podmínkách zvladatelná. Hlavní výhody:

- **Přesnost**: Místo diskrétních režimů přesné řízení výkonu
- **Flexibilita**: Častější aktualizace bez omezení EEPROM
- **Integrace**: Lepší využití MPC optimalizátoru výstupů

**Kritické omezení**: Symetrické rozdělení výkonu mezi fáze (výkon/3) může způsobit neoptimální chování při asymetrickém zatížení.

### Hodnocení pro české podmínky:

**✅ Pozitivní aspekty:**
- Novela Lex OZE II zmírňuje problém fázového měření principem "sdílím sám sobě"
- Asymetrie se projeví "jen" ve vyšších distribučních poplatcích, ne v celkových nákladech
- Úspora 40-50% nákladů na elektřinu při asymetrii díky sdílení

**⚠️ Rizika:**
- **Fázové měření**: Vždy vyšší distribuční poplatky při asymetrii (od roku 2011)
- **Finanční dopad**: Při extrémní asymetrii (RemoteControl = výkon/3) platíte distribuční poplatky za "zbytečný" odběr
- **Příklad**: Při 6kW nabíjení baterie RemoteControl dá 2kW na každou fázi, ale pokud L1 potřebuje 5kW, budete platit distribuční poplatky za 3kW odběr ze sítě na L1
- Možné přetížení fáze při kombinaci s asymetrickým zatížením
- Neoptimální využití FVE při koncentrovaném zatížení na jednu fázi
- Nutnost monitorování fází pro bezpečné použití

**🎯 Doporučení:**
- **Potvrzený finanční dopad**: Asymetrie zvyšuje distribuční poplatky (fázové měření od 2011)
- **Priorita: střední** - výhody RemoteControl vs. vyšší distribuční poplatky při asymetrii
- **Implementovat s inteligentní logikou**: Použít pouze při asymetrii < 1kW pro minimalizaci dodatečných nákladů
- **Monitorování fází**: Sledovat nejen bezpečnost, ale i ekonomický dopad asymetrie
- **Časové okna**: Preferovat noční hodiny (22:00-06:00) kdy je zatížení symetričtější
- **Fallback**: Při detekci problémů automaticky přepnout na standardní režimy

**Výsledek**: RemoteControl má potvrzený finanční dopad kvůz fázovému měření v ČR, ale novela Lex OZE II (2024) zmírňuje problém. **Asymetrie způsobuje vyšší distribuční poplatky, ale ne dramatické náklady.**
