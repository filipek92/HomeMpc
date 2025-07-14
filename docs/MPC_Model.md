# Detailní dokumentace modelu MPC

## Přehled

Model v `powerplan_optimizer.py` implementuje lineární optimalizaci pro řízení domácí energetiky (MPC – Model Predictive Control). Cílem je minimalizovat náklady na energii a efektivně využívat baterii, dvouzónový bojler, fotovoltaiku a síť v rámci zadaného časového horizontu.

## Vstupy modelu

Vstupy jsou rozděleny do tří skupin:

- **series** (časové řady, vektory pro každý krok):
  - `tuv_demand` – spotřeba TUV [kWh]
  - `heating_demand` – spotřeba na vytápění [kWh]
  - `fve_pred` – predikce výroby FVE [kW]
  - `buy_price` – cena nákupu elektřiny [Kč/kWh]
  - `sell_price` – výkupní cena [Kč/kWh]
  - `load_pred` – základní spotřeba domácnosti [kW]
  - `outdoor_temps` – venkovní teploty [°C]

- **initials** (počáteční stavy, skaláry):
  - `bat_soc` – počáteční stav nabití baterie [%]
  - `temp_upper` – počáteční teplota horní zóny nádrže [°C]
  - `temp_lower` – počáteční teplota dolní zóny nádrže [°C]

- **options** (volitelné přepínače a parametry):
  - `heating_enabled` – zapnutí vytápění (bool, default: False)
  - `charge_bat_min` – minimální nabíjení baterie (bool, default: False)
  - Přepsání parametrů systému (viz níže)

## Parametry systému (lze přepsat v `options`)

### Parametry baterie:
- `b_cap` – kapacita baterie [kWh] (default: 17.4)
- `b_min` – minimální SOC baterie [kWh] (default: 15% z kapacity)
- `b_max` – maximální SOC baterie [kWh] (default: kapacita)
- `b_power` – max. výkon baterie [kW] (default: 9)
- `b_eff_in` – účinnost nabíjení (default: 0.94)
- `b_eff_out` – účinnost vybíjení (default: 0.94)

### Parametry dvouzónového bojleru:
- `h_lower_power` – max. příkon dolní patrony [kW] (default: 8.0)
- `h_upper_power` – max. příkon horní patrony [kW] (default: 4.0)
- `h_lower_vol` – objem dolní zóny [m³] (default: 0.7)
- `h_upper_vol` – objem horní zóny [m³] (default: 0.3)
- `h_lower_min_t` – minimální teplota dolní zóny [°C] (default: 30)
- `h_lower_max_t` – maximální teplota dolní zóny [°C] (default: 85)
- `h_upper_min_t` – minimální teplota horní zóny [°C] (default: 45)
- `h_upper_max_t` – maximální teplota horní zóny [°C] (default: 90)
- `alpha` – koeficient přenosu tepla mezi zónami [kW/°C] (default: 0.1)

### Síťová omezení:
- `grid_limit` – hlavní jistič [kW] (default: 18)
- `inverter_limit` – limit měniče [kW] (default: 15)

### Ekonomické parametry:
- `battery_penalty` – penalizace za vybíjení baterie [Kč/kWh] (default: 1.0)
- `bat_threshold_pct` – práh pro rozdělení SOC (default: 0.40)
- `bat_price_below` – cena za energii pod prahem [Kč/kWh] (default: min(buy_price))
- `bat_price_above` – cena za energii nad prahem [Kč/kWh] (default: min(buy_price) - 0.5)
- `final_boiler_price` – cena pro penalizaci/odměnu zbylé energie v bojleru [Kč/kWh] (default: min(buy_price) - 0.5)
- `upper_zone_priority` – bonus za ohřev horní části nádrže [Kč/kWh] (default: 0.5)
- `water_priority_bonus` – bonus za ohřev vody [Kč/kWh] (default: 1.0)
- `fve_unused_penalty` – penalizace za nevyužitou FVE [Kč/kWh] (default: 0.1)
- `bat_under_penalty` – penalizace za SOC pod prahem [Kč/kWh] (default: 0.1)
- `tank_value_hour` – hodina pro oceňování energie v nádrži (default: 18)
- `tank_value_bonus` – bonus za energii v nádrži v danou hodinu [Kč/kWh] (default: 1.0)
- `parasitic_water_heating` – podíl parazitní energie při ohřevu vody (default: 0.05)

## Cílová funkce

Model minimalizuje celkové náklady:

- **Nákup elektřiny**: součet `g_buy[t] * buy_price[t]`
- **Prodej elektřiny**: odečtení `g_sell[t] * sell_price[t]`
- **Penalizace baterie**: penalizace za vybíjení (degradace)
- **Penalizace/odměna za koncový SOC baterie**:
  - Odměna za energii nad práh (např. 40% SOC)
  - Penalizace za energii pod prahem
- **Penalizace za nevyužitou FVE**
- **Bonus za ohřev vody** (obecně a zvlášť pro horní zónu)
- **Penalizace za SOC pod prahem** v každém kroku
- **Bonus za energii v nádrži** v určitou hodinu
- **Penalizace/odměna za zbylou energii v bojleru**

## Omezení (Constraints)

### Energetická bilance (v každém kroku):
```
fve_pred[t] + g_buy[t] + b_discharge[t] * b_eff_out
= load_pred[t] + b_charge[t] / b_eff_in + (h_in_lower[t] + h_in_upper[t] + parasitic_energy) + g_sell[t] + fve_unused[t]
```

### Technologická omezení:
- Výkonové limity baterie, patrony, sítě, měniče
- SOC baterie a teplotní rozsahy zón v povoleném rozsahu
- Omezení možnosti nabíjení/vybíjení baterie a ohřevu v jednom kroku

### Dvouzónový model nádrže:
- **Dolní zóna**: ohřívána dolní patronou, ztrácí teplo přenosem do horní zóny a odběrem
- **Horní zóna**: ohřívána horní patronou, získává teplo z dolní zóny, ztrácí teplo odběrem
- **Přenos tepla**: řízený koeficientem `alpha` podle rozdílu energií v zónách
- **Tepelné ztráty**: modelovány funkcí `estimate_heating_losses`

### Dynamika zásobníků:
- SOC baterie se aktualizuje podle předchozího stavu, nabíjení/vybíjení a účinnosti
- Energie v zónách se aktualizuje podle ohřevu, odběru, přenosu a ztrát

## Výstupy modelu

### Časové řady optimalizovaných veličin:
- `b_power`, `b_charge`, `b_discharge`, `b_soc`, `b_soc_percent` – baterie
- `g_buy`, `g_sell`, `buy_cost`, `sell_income`, `net_step_cost` – síť
- `h_in_lower`, `h_in_upper`, `h_out_lower`, `h_out_upper` – ohřev a odběr
- `h_soc_lower`, `h_soc_upper`, `h_soc_lower_percent`, `h_soc_upper_percent` – energie v zónách
- `temp_lower`, `temp_upper` – teploty zón
- `h_to_upper` – přenos tepla mezi zónami
- `fve_unused` – nevyužitá FVE

### Souhrnné výsledky:
- Celkové náklady, příjmy, bilance
- Celková spotřeba, výroba, nabíjení, vybíjení
- Komponenty cílové funkce (penalizace, bonusy)
- Metadata o vstupu a nastavení

### Akce pro Home Assistant:
- `charger_use_mode` – režim střídače (Manual/Self Use/Feedin Priority/Back Up)
- `upper_accumulation_on`, `lower_accumulation_on` – řízení patrony
- `max_heat_on`, `forced_heating_block` – speciální režimy ohřevu
- `battery_target_soc`, `minimum_battery_soc` – cílové SOC
- `reserve_power_charging` – rezervovaný výkon pro nabíjení
