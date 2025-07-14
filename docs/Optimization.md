# Optimalizační kritéria PowerStreamPlan

Tento dokument popisuje všechna kritéria a penalizace používané v MPC optimalizátoru pro řízení domácího energetického systému.

## Nákladová funkce

Optimalizátor minimalizuje celkovou nákladovou funkci, která se skládá z následujících komponent:

### 1. Základní energetické náklady

#### Nákup elektřiny z gridu (`g_buy`)
- **Jednotka**: Kč/kWh
- **Popis**: Náklady na nákup elektřiny ze sítě podle aktuálních tarifů
- **Výpočet**: `g_buy[t] * buy_price[t]`

#### Prodej elektřiny do gridu (`g_sell`)
- **Jednotka**: Kč/kWh
- **Popis**: Příjem z prodeje elektřiny do sítě (odečítá se od nákladů)
- **Výpočet**: `-g_sell[t] * sell_price[t]`

### 2. Penalizace baterie

#### Penalizace za vybíjení baterie (`battery_penalty`)
- **Jednotka**: Kč/kWh
- **Popis**: Penalizace za každou kWh vybitou z baterie, motivuje k efektivnímu využívání baterie
- **Výpočet**: `battery_penalty * b_discharge[t]`

#### Penalizace za nízký SOC baterie (`bat_under_penalty`)
- **Jednotka**: Kč/kWh
- **Popis**: Penalizace za udržování SOC baterie pod prahem (`bat_threshold_pct`)
- **Výpočet**: `bat_under_penalty * b_soc_under[t]`

### 3. Ohodnocení konečného stavu baterie

#### Cena za energii nad prahem (`bat_price_above`)
- **Jednotka**: Kč/kWh
- **Popis**: Ohodnocení energie v baterii nad prahovým SOC na konci optimalizačního horizontu
- **Výpočet**: `-bat_price_above * b_surplus`

#### Cena za energii pod prahem (`bat_price_below`)
- **Jednotka**: Kč/kWh
- **Popis**: Penalizace za nedostatek energie v baterii pod prahovým SOC na konci horizontu
- **Výpočet**: `+bat_price_below * (threshold - b_short)`

### 4. Kritéria pro fotovoltaiku

#### Penalizace za nevyužitou FV energii (`fve_unused_penalty`)
- **Jednotka**: Kč/kWh
- **Popis**: Penalizace za nevyužitou fotovoltaickou energii, motivuje k maximálnímu využití FV
- **Výpočet**: `fve_unused_penalty * fve_unused[t]`

### 5. Kritéria pro ohřev vody

#### Bonus za ohřev vody (`water_priority_bonus`)
- **Jednotka**: Kč/kWh
- **Popis**: Bonus za ohřev vody v obou zónách nádrže, motivuje k přednostnímu ohřevu
- **Výpočet**: `-water_priority_bonus * (h_in_lower[t] + h_in_upper[t])`

#### Priorita horní zóny (`upper_zone_priority`)
- **Jednotka**: Kč/kWh
- **Popis**: Dodatečný bonus za ohřev horní zóny nádrže (kde se odebírá TUV)
- **Výpočet**: `-upper_zone_priority * h_in_upper[t]`

### 6. Ohodnocení konečného stavu nádrže

#### Hodnota energie v nádrži (`final_boiler_price`)
- **Jednotka**: Kč/kWh
- **Popis**: Ohodnocení celkové energie v obou zónách nádrže na konci optimalizačního horizontu
- **Výpočet**: `-final_boiler_price * (h_soc_lower[t_end] + h_soc_upper[t_end])`

#### Bonus za energii v horní zóně na konci (`upper_zone_priority`)
- **Jednotka**: Kč/kWh
- **Popis**: Dodatečný bonus za energii v horní zóně na konci horizontu
- **Výpočet**: `-upper_zone_priority * h_soc_upper[t_end]`

### 7. Časově specifická kritéria

#### Bonus za hodnotu tepla ve vybraných hodinách (`tank_value_bonus`)
- **Jednotka**: Kč/kWh
- **Parametr**: `tank_value_hour` - hodina, kdy se bonus uplatňuje
- **Popis**: Bonus za energii v horní zóně nádrže ve specifických hodinách (např. ráno před odběrem TUV)
- **Výpočet**: `-tank_value_bonus * h_soc_upper[t]` pro `t` v `tank_value_indexes`

## Fyzikální omezení

### Baterie
- **Kapacita**: `b_cap` (kWh)
- **Minimální SOC**: `b_min` (kWh)
- **Maximální SOC**: `b_max` (kWh)
- **Maximální výkon**: `b_power` (kW)
- **Účinnost nabíjení**: `b_eff_in` (-)
- **Účinnost vybíjení**: `b_eff_out` (-)

### Dvouzónová nádrž
- **Dolní zóna**: objem `h_lower_vol` (m³), výkon `h_lower_power` (kW)
- **Horní zóna**: objem `h_upper_vol` (m³), výkon `h_upper_power` (kW)
- **Teplotní rozsahy**: min/max teploty pro obě zóny
- **Přenos tepla**: koeficient `alpha` pro pasivní přenos mezi zónami

### Síťová omezení
- **Hlavní jistič**: `grid_limit` (kW)
- **Limit střídače**: `inverter_limit` (kW)

## Speciální logika

### Dynamické omezení SOC baterie
- Při výskytu poptávky po ohřevu je SOC baterie omezen na 90% kapacity
- Umožňuje rezervovat místo pro případný přebytek FV energie

### Podmíněný ohřev vody (`charge_bat_min`)
- Pokud je aktivní, ohřev vody je povolen pouze při SOC baterie >= 60%
- Zajišťuje prioritu nabíjení baterie před ohřevem vody

### Parazitní energie (`parasitic_water_heating`)
- Dodatečná energie spotřebovaná při ohřevu vody (ztráty v kabeláži, řízení, atd.)
- Rozděluje se podle SOC baterie mezi nabíjení baterie a odběr ze sítě

## Výstupní metriky

Optimalizátor poskytuje detailní výstupní metriky včetně:
- Celkové náklady/příjmy podle jednotlivých komponent
- Energetické bilance (nabíjení/vybíjení, ohřev, ztráty)
- Rozdělení parazitní energie
- Hodnota objektové funkce

Tato struktura umožňuje jemné ladění chování optimalizátoru podle konkrétních potřeb a preferencí uživatele.
