# Logika řízení akumulační nádrže

## Přehled systému

Systém řídí tepelnou akumulaci v nádrži pomocí 4 elektrických topných patron s různými výkony:
- **RE1**: 1400W (TUV - teplá užitková voda)
- **RE2**: 2800W (TUV - teplá užitková voda)
- **RE3**: 2800W (AKU - akumulace tepla)
- **RE4**: 5600W (AKU - akumulace tepla)

**Celkový maximální výkon**: 12.0 kW

## Fyzické parametry nádrže

### Dvouzónový model
- **Horní zóna**: 300L (střední + horní senzor)
  - Minimální teplota: 45°C
  - Maximální teplota: 90°C
  - Kapacita: ~15.25 kWh
- **Spodní zóna**: 700L (převážně spodní senzor)
  - Minimální teplota: 30°C
  - Maximální teplota: 85°C
  - Kapacita: ~43.23 kWh

### Teplotní senzory
- **Horní senzor**: 0x345a4ed443f76e28
- **Střední senzor**: 0x4e2e32d443f6a328
- **Spodní senzor**: 0x302bf1d443e92028

## Vstupy systému

### Hlavní vstupy
1. **Fotovoltaika**:
   - `power_solar1` + `power_solar2` = celkový solární výkon
   - `power_battery` - výkon baterie (+ nabíjení, - vybíjení)
   - `battery_soc` - stav nabití baterie (%)
   - `power_grid` - výkon sítě (+ odběr, - dodávka)

2. **Teploty nádrže**:
   - `tank_upper_temp` - horní senzor
   - `tank_middle_temp` - střední senzor  
   - `tank_lower_temp` - spodní senzor

3. **Další zdroje tepla**:
   - Krb: `krb_power` (vypočítáno z průtoku a teplotního rozdílu)
   - Fototermika: `ft_power` (vypočítáno z průtoku a teplotního rozdílu)

### Konfigurační parametry
- `bat_min` - minimální stav nabití baterie (%)
- `bat_req` - požadovaný stav nabití baterie (%)
- `bat_discharge` - povolený vybíjecí výkon baterie (W)
- `bat_charge_reserve` - rezervovaný výkon pro dobíjení (W)
- `comfort_temp` - komfortní teplota TUV (°C)
- `accu_temp` - akumulační teplota TUV (°C)
- `min_temp` - minimální teplota TUV (°C)
- `accu_maxtemp` - maximální teplota akumulace (°C)

### Řídící přepínače
- `accu_tuv_en` - povolení horní akumulace
- `accu_en` - povolení spodní akumulace
- `comfort_heat_en` - povolení komfortního ohřevu
- `auto_en` - povolení automatiky
- `block_force` - blokování nuceného ohřevu
- `full_power` - maximální ohřev ze sítě

## Logické stavy (binary_sensor)

### Požadavky na ohřev
- `primary_heat` - primární ohřev (kritický)
- `comfort_tuv_heat` - komfortní ohřev TUV
- `accu_tuv_heat` - akumulace TUV (horní zóna)
- `accu_heat` - akumulace tepla (spodní zóna)
- `force_heat` - nucený ohřev (`accu_heat` AND `full_power`)
- `block_upper_part` - blokace horního ohřevu
- `bat_prio` - priorita nabití baterie (`battery_soc` < `bat_min`)

## Klíčové vypočítané hodnoty

### Dostupný výkon (`available_power`)
```cpp
float available = power_grid + power_solar;

// Zahrnutí baterie (pokud není priorita nabíjení)
if (!bat_prio) {
    available += power_battery;
    // Rezervace pro nabíjení baterie
    if (bat_charge_reserve > 0 && battery_soc <= bat_req && !comfort_tuv_heat) {
        available -= bat_charge_reserve;
    }
} else {
    available -= 100; // Rezerva pro nabíjení
}

// Zahrnutí aktuálního ohřevu
if (heat_power > 0) available += heat_power;

// Omezení na solární výkon
if (available > solar) available = solar;

// Přidání optimálního odběru z baterie
if (bat_opt > 0) available += bat_opt;
```

### Optimální odběr z baterie (`bat_opt`)
```cpp
if (battery_soc <= bat_req) return 0;
return bat_discharge * ((battery_soc - bat_req) / (100 - bat_req));
```

## Hlavní řídicí logika (interval: 15s)

### Prioritní řazení topných patron
1. **Nucený ohřev** (`accu_heat` AND `full_power`):
   - Zapne všechny patrony RE1+RE2+RE3+RE4 (12kW)

2. **Primární ohřev** (`primary_heat` AND NOT `block_force`):
   - Zapne RE1+RE2 (4.2kW) - kritický ohřev

3. **Komfortní ohřev** (`comfort_tuv_heat` AND `comfort_heat_en` AND NOT `block_force`):
   - Zapne RE1+RE2 (4.2kW) - komfortní teplota

4. **Akumulace TUV** (`accu_tuv_heat` AND `accu_tuv_en` AND NOT `block_upper_part`):
   - Priorita: RE2, RE1
   - Pouze pokud je dostupný výkon

5. **Akumulace tepla** (`accu_heat`):
   - Priorita: RE3, RE4, RE2, RE1
   - Pouze pokud je dostupný výkon
   - RE3+RE4 pouze pokud `accu_en` = true

### Bezpečnostní omezení
- **Maximální teplota**: Pokud `tank_max_temp` > 88°C → vypne všechny patrony
- **Automatické řízení**: Patrony se zapínají/vypínají pouze pokud `auto_en` = true

## Energetické výpočty

### Energie v zónách
```cpp
// Horní zóna (300L)
accu_top_energy = (accu_top - 45) * 1.163 * 291 / 1000 [kWh]

// Spodní zóna (700L)  
accu_bot_energy = (accu_bot - 30) * 1.163 * 679 / 1000 [kWh]
```

### Stav nabití nádrže
```cpp
accu_soc = accu_energy / accu_capacity * 100 [%]
```

## Monitorování a statistiky

### Výkonové hodnoty
- `heat_power` - aktuální výkon ohřevu
- `acumulation_power` - výkon z dostupných zdrojů
- `priority_power` - výkon nad dostupné zdroje

### Energetické statistiky
- `Spotřebovaná energie` - celková spotřeba
- `Akumulovaná solární energie` - energie z FV
- `Prioritní energie` - energie ze sítě

## Komunikace s vnějšími systémy

### Modbus TCP server
- Připojení k nadřazenému systému (PowerStreamPlan)
- Port: výchozí Modbus TCP
- Umožňuje vzdálené řízení a monitoring

### Home Assistant API
- Šifrované spojení
- Všechny entity exportovány do HA
- Možnost vzdáleného řízení

## Poznámky k implementaci

1. **Autonomní provoz**: Systém funguje nezávisle na připojení k nadřazenému systému
2. **Bezpečnost**: Automatické vypnutí při překročení maximální teploty
3. **Prioritizace**: Jasné pořadí důležitosti požadavků na ohřev
4. **Energetická efektivita**: Využití dostupných zdrojů podle priority
5. **Flexibilita**: Možnost ručního řízení přes webové rozhraní nebo HA

## TODO / Otázky pro doplnění

1. ✅ **Kdy se aktivují logické stavy** - VYŘEŠENO:

### Autonomní aktivace stavů (pouze ESPHome logika)

**`primary_heat`** - Kritický ohřev (nezávislý na FVE):
```cpp
if(tank_middle_temp < min_temp - hyst) status = true;   // 42.5°C - 2.5°C = 40°C
if(tank_middle_temp > min_temp + hyst) status = false;  // 42.5°C + 2.5°C = 45°C
```
- **Účel**: Zabezpečuje minimální teplotu TUV
- **Nezávislý na FVE energii** - topí vždy when needed

**`comfort_tuv_heat`** - Komfortní ohřev (nezávislý na FVE):
```cpp
if(tank_middle_temp < comfort_temp - hyst) status = true;   // 62.5°C - 2.5°C = 60°C  
if(tank_middle_temp > comfort_temp + hyst) status = false;  // 62.5°C + 2.5°C = 65°C
```
- **Účel**: Zajišťuje komfortní teplotu TUV
- **Nezávislý na FVE energii** - aktivuje se podle potřeby
- **Podmíněný**: vyžaduje `comfort_heat_en` = true pro ohřev

**`accu_tuv_heat`** - Akumulace do horní části (závislý na FVE):
```cpp
if(tank_middle_temp < accu_temp - hyst) status = true;   // 70°C - 2.5°C = 67.5°C
if(tank_middle_temp > accu_temp + hyst) status = false;  // 70°C + 2.5°C = 72.5°C
```
- **Účel**: Akumulace přebytečné FVE energie do horní části nádrže
- **Závislý na dostupné energii** z FVE/baterie
- **Podmíněný**: vyžaduje `accu_tuv_en` = true a NOT `block_upper_part`

**`accu_heat`** - Akumulace do celé nádrže (závislý na FVE):
```cpp
if(tank_max_temp < accu_maxtemp - hyst) status = true;   // 88°C - 2.5°C = 85.5°C
if(tank_max_temp > accu_maxtemp) status = false;         // 88°C (bez hystereze!)
```
- **Účel**: Akumulace velkého přebytku FVE energie do celé nádrže
- **Závislý na dostupné energii** z FVE/baterie  
- **Podmíněný**: vyžaduje `accu_en` = true pro spodní část

### Klíčové pozorování:
- **Autonomní rozhodování**: ESPHome samo vyhodnocuje teplotní podmínky
- **Bez časové logiky**: Časové řízení se očekává z nadřízeného systému (HA)
- **Povolení z HA**: Nadřízený systém řídí pomocí `*_en` přepínačů
- **Energetická závislost**: `primary_heat` a `comfort_tuv_heat` topí nezávisle, akumulační stavy pouze při přebytku

2. **Jaká je logika určování** `block_upper_part` a `block_force`?

**`block_upper_part`** - Ochrana horní části:
```cpp
if(tank_upper_temp > accu_maxtemp - hyst*2) return true;    // 88°C - 5°C = 83°C
if(tank_middle_temp > accu_maxtemp - hyst*2) return true;   // 88°C - 5°C = 83°C
```
- **Účel**: Zabrání přehřátí horní části nádrže
- **Aktivace**: Když horní nebo střední senzor překročí 83°C

**`block_force`** - Řízeno z HA:
- **Template switch** ovládaný uživatelem/nadřízeným systémem
- **Účel**: Umožňuje zablokovat nucený ohřev v kritických situacích
- **Výchozí**: OFF (neblokuje)

3. ✅ **Jak se rozhoduje mezi různými režimy ohřevu?** - VYŘEŠENO:

### Prioritní hierarchie ohřevu (interval: 15s)

**POZOR**: `primary_heat` a `comfort_tuv_heat` jsou v `if/else if` - **nemohou běžet současně!**

```cpp
// 1. NEJVYŠŠÍ PRIORITA: Nucený ohřev (přebíjí vše)
if(accu_heat && full_power) {
    RE1+RE2+RE3+RE4 = 12kW  // Všechny patrony
    current_power = 12000W
}

// 2. KRITICKÝ OHŘEV: Primární minimum
if(primary_heat && !block_force) {
    RE1+RE2 = 4.2kW
    current_power += 4200W
}
// 3. KOMFORTNÍ OHŘEV: Pouze pokud NENÍ primary_heat
else if(comfort_tuv_heat && comfort_heat_en && !block_force) {
    RE1+RE2 = 4.2kW  
    current_power += 4200W
}

// 4. AKUMULACE TUV: Pouze při dostupném výkonu
if(accu_tuv_heat && accu_tuv_en && !block_upper_part) {
    // Priorita: RE2 → RE1
    if(current_power + RE2_power <= avail_power) → RE2 = 2.8kW
    if(current_power + RE1_power <= avail_power) → RE1 = 1.4kW
}

// 5. AKUMULACE TEPLA: Pouze při dostupném výkonu
if(accu_heat && accu_en) {
    // Priorita: RE3 → RE4 → RE2 → RE1 (pokud nejsou už aktivní)
    if(current_power + RE4_power <= avail_power) → RE4 = 5.6kW
    if(current_power + RE3_power <= avail_power) → RE3 = 2.8kW
}
if(accu_heat && accu_tuv_en && !block_upper_part) {
    // Doplnění horní části pokud je místo
    if(current_power + RE2_power <= avail_power) → RE2 = 2.8kW
    if(current_power + RE1_power <= avail_power) → RE1 = 1.4kW
}
```

### Klíčová zjištění:
- **`primary_heat` vs `comfort_tuv_heat`**: **VZÁJEMNĚ SE VYLUČUJÍ** (if/else if)
- **Důvod**: Oba používají stejné patrony RE1+RE2 pro stejný účel (ohřev horní části)
- **Logika**: Pokud je potřeba kritický ohřev, komfortní se přeskočí
- **Kombinace**: Akumulační režimy **MOHOU** běžet současně s critical/comfort
- **Energetické omezení**: Akumulace pouze při `current_power <= avail_power`

### Návrh zlepšení:
Možná by šlo sloučit podmínky:
```cpp
// Místo if/else if:
if((primary_heat || (comfort_tuv_heat && comfort_heat_en)) && !block_force) {
    RE1+RE2 = 4.2kW
}
```

4. **Jaké jsou časové podmínky** pro komfortní ohřev?

**ODPOVĚĎ**: ESPHome **NEŘEŠÍ** časovou logiku! 
- Časové řízení se očekává z **nadřízeného systému** (Home Assistant nebo PowerStreamPlan)
- Nadřízený systém řídí pomocí přepínačů `comfort_heat_en`, `accu_tuv_en`, `accu_en`
- ESPHome pouze reaguje na aktuální teplotní podmínky

5. **Jak se koordinuje** s PowerStreamPlan MPC optimalizátorem?

**KOORDINACE přes Modbus TCP**:
- ESPHome = **Modbus TCP server** (autonomní řízení)
- PowerStreamPlan = **Modbus TCP client** (nadřízená optimalizace)
- Koordinace pomocí **switch přepínačů**:
  * `accu_tuv_en` - povolení horní akumulace
  * `accu_en` - povolení spodní akumulace  
  * `comfort_heat_en` - povolení komfortního ohřevu
  * `full_power` - maximální ohřev ze sítě
  * `block_force` - blokování nuceného ohřevu

**Autonomie**: ESPHome funguje nezávisle i bez PowerStreamPlan připojení

6. ✅ **Dostupný výkon (`available_power`) - VYŘEŠENO:**

### Logika výpočtu dostupného výkonu

**Dostupný výkon = energie pro ohřev vody nad rámec domácí spotřeby**

```cpp
available = power_grid + power_solar;  // Základní bilance

// Zahrnutí baterie (autonomní součást elektrárny)
if(!bat_prio) {  // Pokud baterie nepotřebuje prioritní nabíjení
    available += power_battery;  // + vybíjení, - nabíjení
    
    // Rezervace pro nabíjení baterie
    if(bat_charge_reserve > 0 && battery_soc <= bat_req && !comfort_tuv_heat) {
        available -= bat_charge_reserve;
    }
} else {
    available -= 100;  // Rezerva pro nabíjení při nízké baterii
}

// Zahrnutí aktuálního ohřevu (může se přepnout)
if(heat_power > 0) available += heat_power;

// Omezení na solární výkon (nákup ze sítě?)
if(available > solar) available = solar;

// Jemné doladění odběru z baterie (linearizace kroků 1.4kW)
if(bat_opt > 0) available += bat_opt;  // bat_opt = f(battery_soc, bat_discharge)
```

### Klíčové prvky:
- **Baterie je autonomní** - sama ukládá přebytek nebo dodává při nedostatku
- **Linearizace pomocí `bat_opt`** - jemné doladění kroků 1.4kW
- **`bat_opt` logika**: Pokud baterie > `bat_req`, lineárně povoluje více odběru
- **Cíl**: Udržet baterii kolem 90% pomocí ohřevu vody
