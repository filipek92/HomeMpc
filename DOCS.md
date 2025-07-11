# PowerStreamPlan Add-on Documentation

## Popis

PowerStreamPlan je inteligentní optimalizátor spotřeby a výroby energie v domácnosti pomocí MPC (Model Predictive Control). Addon automaticky optimalizuje řízení domácí energetiky včetně baterií, bojleru, fotovoltaiky a nákupu/prodeje elektřiny.

## Instalace

1. Přidejte repozitář do Home Assistant
2. Najděte PowerStreamPlan v seznamu doplňků
3. Klikněte na "Instalovat"
4. Po instalaci klikněte na "Spustit"

## Konfigurace

### Povinné parametry

- **ha_url**: URL vašeho Home Assistant (obvykle `http://homeassistant:8123`)
- **token**: Long-lived access token z Home Assistant

### Získání Long-lived access token

1. V Home Assistant jděte do **Nastavení** > **Lidé** > **Váš profil**
2. Scrollujte dolů na **Long-lived access tokens**
3. Klikněte na **Vytvořit token**
4. Pojmenujte token (např. "PowerStreamPlan")
5. Zkopírujte token a vložte ho do konfigurace addonu

## Použití

Po spuštění addonu:

1. Addon bude dostupný v bočním panelu Home Assistant
2. Webové rozhraní zobrazuje aktuální optimalizaci a grafy
3. Optimalizace se automaticky spouští každých 5 minut
4. Výsledky jsou automaticky publikovány do Home Assistant jako sensory

## Sensory

Addon vytváří následující sensory v Home Assistant:

- `sensor.powerplan_battery_power` - Optimální výkon baterie
- `sensor.powerplan_grid_power` - Optimální výkon ze sítě
- `sensor.powerplan_boiler_power` - Optimální výkon bojleru
- `sensor.powerplan_status` - Stav optimalizace

## Troubleshooting

### Addon se nespustí

- Zkontrolujte, zda je nastaven správný `ha_url` a `token`
- Zkontrolujte logy addonu v Home Assistant

### Nejsou dostupné sensory

- Zkontrolujte, zda je token platný a má dostatečná oprávnění
- Zkontrolujte logy addonu pro chyby při komunikaci s Home Assistant

## Podpora

Pro hlášení chyb nebo žádosti o funkce použijte GitHub Issues v repozitáři projektu.
