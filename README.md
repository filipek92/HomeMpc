# PowerStreamPlan

PowerStreamPlan – inteligentní optimalizátor spotřeby a výroby energie v domácnosti pomocí MPC (Model Predictive Control) pro Home Assistant.

## Popis

Tento projekt implementuje pokročilý systém pro optimalizaci řízení domácí energetiky. Využívá Model Predictive Control (MPC) k minimalizaci nákladů na energii a efektivnímu využívání baterie, dvouzónového bojleru, fotovoltaiky a síťového připojení.

## Hlavní funkce

- **Optimalizace spotřeby energie** pomocí lineárního MPC algoritmu
- **Dvouzónový model bojleru** pro efektivní řízení ohřevu vody
- **Predikce výroby FVE** a spotřeby domácnosti
- **Automatické řízení režimů** střídače a akumulačních systémů
- **Webové rozhraní** pro monitorování a konfiguraci
- **Integrace s Home Assistant** pro publikování dat a ovládání

## Instalace

Projekt je určen pro instalaci jako Home Assistant Add-on.

### Automatická instalace

1. V Home Assistant přejděte do **Nastavení** > **Doplňky** > **Obchod s doplňky**
2. Klikněte na tři tečky v pravém horním rohu a vyberte **Repozitáře**
3. Přidejte URL tohoto repozitáře: `https://github.com/filipek92/PowerStreamPlan`
4. Najděte **PowerStreamPlan** v seznamu doplňků a klikněte na **Instalovat**

## Dokumentace

**[→ Detailní dokumentace addonu](power_stream_plan/README.md)**

Kompletní dokumentace včetně:
- Instalačního průvodce
- Popisu hlavních komponent
- Konfiguračních možností
- Detailních technických informací

## Licence

Projekt je určen pro osobní a výukové účely.

## Autor

Filip Krčma (filipek92)
