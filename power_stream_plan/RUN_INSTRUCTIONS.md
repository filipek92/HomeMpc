# Příkazy pro spuštění PowerStreamPlan

## Produkční prostředí (Home Assistant Addon)

Hlavní skript pro addon:
```bash
./run.sh
```

## Místní testování (s Gunicorn)

```bash
./run_local.sh
```

## Vývojové prostředí (Flask dev server)

```bash
./run_dev.sh
```

### Přímé spuštění

Produkční Gunicorn server:
```bash
gunicorn --config gunicorn.conf.py powerplan_server:app
```

Vývojový Flask server:
```bash
python3 powerplan_server.py
```

## Poznámky k produkčnímu nasazení

- Gunicorn je nakonfigurován pro použití pouze 1 worker procesu kvůli APScheduler
- Server běží na portu stanoveném proměnnou PORT (default: 26781)
- Logy se zapisují do stdout/stderr
- Aplikace se restartuje po 1000 requestech pro předcházení memory leaks
- Graceful shutdown timeout je 30 sekund

## Rozdíly mezi skripty

- `run.sh` - **Produkční prostředí pro Home Assistant addon** s publikováním do HA
- `run_local.sh` - Místní testování s Gunicorn, bez publikování do HA
- `run_dev.sh` - Vývojový režim s Flask dev serverem, bez publikování do HA

## Úspěšné přeřešení varování

Aplikace nyní používá produkční WSGI server (Gunicorn) místo vývojového Flask serveru. Varování o "development server" by se již nemělo objevovat.
