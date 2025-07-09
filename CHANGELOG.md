
## 1.11.2 - 2025-07-09
Priorita horní části nádrže a UI zlepšení
- Přidán parametr `upper_zone_priority` pro upřednostnění ohřevu horní části nádrže
- Horní část se nyní ohřívá dříve než dolní část díky bonusu v nákladové funkci
- Parametr oceňuje jak průběžný ohřev tak konečný stav energie v horní zóně
- Zlepšeno zobrazení časů v UI - místo `140000` se zobrazuje `14:00:00`
- V tabulce "Plán akcí" se zobrazuje čas slotu místo čísla slotu

## 1.11.1 - 2025-07-08
Přidá state template, failsafe migrace
- Přidá state template, failsafe migrace


## 1.11.0 - 2025-07-08
Refactor variable names to convention
- message is optional
- name migration


## 1.10.5 - 2025-07-07
Parasitic charging
- feat: parasitic energy storage


## 1.10.4 - 2025-07-07
Resultst into meta
- publish all results into mpc_debug


## 1.10.3 - 2025-07-07
Fixes
- split date and time


## 1.10.2 - 2025-07-07
Fixes
- fix: datetime serialization


## 1.10.1 - 2025-07-07
Fixes
- fix: results dir existency


## 1.10.0 - 2025-07-07
History solution view
- version report in storage


## 1.9.0 - 2025-07-07
TStore results (data folder  if addon)
- store in data folder if addon
- store history of optim tasks


## 1.8.0 - 2025-07-07
Tank value bonus at evening
- tank value bonus
- change scheduler


## 1.7.1 - 2025-07-06
Addon detection, autoreload
- addon detection, autoreload


## 1.7.0 - 2025-07-06
Schript for publishing
- check git cleant
- fix changelog
- publish version script

# Changelog

## [1.6.0] – 2025-07-06
### Added
- Penalty for bat under

## [1.5.0] – 2025-07-05
### Added
- Water bonus added

## [1.4.3] – 2025-07-05
### Added
- report total charge/discharge bat

## [1.4.2] – 2025-07-05
### Added
- Changelog
### Fixed
- Defualt settins

## [1.4.1] – 2025-07-05
### Debug
- Výpis nepoužité FVE energie do diagnostiky
- Přidání detailních debug informací
### Fixed
- Oprava počáteční hodnoty nabití bojleru

## [1.4.0] – 2025-07-05
### Added
- Nastavení pro ladění optimalizace v UI
### Changed
- Parametry a doladění ladicí logiky

## [1.3.1] – 2025-07-05
### Fixed
- Výchozí hodnoty nastavení

## [1.3.0] – 2025-07-05
### Improved
- Úprava vizualizace výstupů (lepší vzhled)

## [1.2.1] – 2025-07-05
### Fixed
- Úprava konfigurace volitelných možností

## [1.2.0] – 2025-07-05
### Added
- Editace parametrů optimalizace přes rozhraní
- Nové možnosti nastavení chování při vytápění
- Omezení maximálního nabití baterie při topení
### Changed
- Refaktoring parametrů a přidání výstupů
- Odstranění duplicitní logiky

## [1.1.0] – 2025-07-04
### Cleaning
- Vyčištění kódu

## [1.0.15] – 2025-07-04
### Fixed
- Stabilizace a úprava konfigurace

## [1.0.14] – 2025-07-04
### Changed
- Korekce výpočtu prvního slotu

## [1.0.13] – 2025-07-04
### Fixed
- Oprava názvů režimů
### Added
- Debugovací režim `mpc_debug`

## [1.0.12] – 2025-07-04
### Added
- Ikony pro doplněk v UI

## [1.0.11] – 2025-07-04
### Changed
- Kompatibilita s Ingress

## [1.0.10] – 2025-07-04
### Changed
- Nastavení Supervisoru

## [1.0.9] – 2025-07-04
### Fixed
- Optimalizace se nespouští automaticky po startu

## [1.0.8] – 2025-07-04
### Changed
- Regenerace s podporou Ingress

## [1.0.7] – 2025-07-04
### Changed
- Překlad názvu panelu v UI

## [1.0.6] – 2025-07-04
### Changed
- Drobné úpravy a ladění

## [1.0.5] – 2025-07-04
### Changed
- Úpravy akčních funkcí a panelu

## [1.0.4] – 2025-07-04
### Added
- Možnost nastavit token a HA URL v konfiguraci

## [1.0.3] – 2025-07-03
### Added
- Povolení `host_network: true`

## [1.0.2] – 2025-07-03
### Debug
- Výpis hlaviček pro ladění

## [1.0.1] – 2025-07-03
### Fixed
- Odebrání `host_network` pro kompatibilitu

## [1.0.0] – 2025-07-03
### Added
- První verze doplňku
- Základní webové rozhraní přes Ingress
- Komunikace s Home Assistant API
