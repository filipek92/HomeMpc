# Integrace Vue 3 Frontend s PowerStreamPlan

Byla vytvořena kompletní Vue 3 aplikace s Quasar UI frameworkem, která nahrazuje původní HTML template.

## 📁 Struktura

```
PowerStreamPlan/
├── frontend/                    # Vue 3 aplikace
│   ├── src/
│   │   ├── components/         # UI komponenty
│   │   ├── views/             # Stránky
│   │   ├── stores/            # Pinia store
│   │   ├── services/          # API služby
│   │   └── types/             # TypeScript typy
│   ├── package.json
│   ├── vite.config.ts
│   └── build.sh               # Build skript
└── power_stream_plan/
    ├── static/
    │   └── dist/              # Build výstup (generovaný)
    └── templates/
        └── index.html         # Původní template (zachován)
```

## 🚀 Instalace a spuštění

### 1. Instalace závislostí

```bash
cd frontend
npm install
```

### 2. Vývoj

```bash
# Terminal 1 - Spustit backend
cd power_stream_plan
python powerplan_server.py

# Terminal 2 - Spustit frontend dev server
cd frontend
npm run dev
```

Frontend bude dostupný na `http://localhost:3000` s proxy na backend `http://localhost:5000`.

### 3. Produkční build

```bash
cd frontend
./build.sh
```

Nebo:

```bash
cd frontend
npm run build
```

Build výstup se automaticky zkopíruje do `power_stream_plan/static/dist/`.

## 🔗 Integrace s Flask backendem

### API Endpointy

Frontend očekává tyto endpointy:

- `GET /` - Dashboard data (JSON)
- `POST /regenerate` - Regenerace optimalizace
- `GET /download_csv` - Stažení CSV souboru
- `GET /settings` - Nastavení aplikace
- `POST /settings` - Uložení nastavení

### Změny v Flask aplikaci

Pro plnou integraci bude potřeba:

1. **Nový endpoint pro JSON data**:
```python
@app.route('/api/')
def api_dashboard():
    # Vrátí data jako JSON místo renderování template
    return jsonify({
        'solution': solution_data,
        'graphs': graphs_data,
        'version': version,
        'generated_at': generated_at,
        # ... další data
    })
```

2. **Servírování statických souborů**:
```python
@app.route('/')
def index():
    # Servíruje Vue aplikaci
    return send_from_directory('static/dist', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    # Servíruje ostatní statické soubory
    return send_from_directory('static/dist', path)
```

3. **CORS konfigurace** (pokud potřeba):
```python
from flask_cors import CORS
CORS(app)
```

## 🎨 Komponenty

### ✅ Implementované komponenty

- **DashboardHeader** - Header s akcemi a badges
- **DashboardControls** - Filtry a ovládání
- **StatusCards** - Přehledové karty s metrikami
- **ChartsContainer** - Taby s grafy
- **ActionPlan** - Tabulky s akcemi a timeline
- **DashboardSidebar** - Sidebar s metrikami a info
- **ActionSection** - Akční tlačítka

### 🔄 State Management

- **Pinia store** pro centrální správu stavu
- **Auto-refresh** každých 5 minut
- **Error handling** s notifikacemi
- **Loading states** pro všechny akce

### 📱 Responsivní design

- **Desktop**: 2+1 sloupcový layout
- **Tablet/Mobile**: Adaptivní jednosloupcový layout
- **Touch-friendly**: Optimalizováno pro dotyková zařízení

## 🔧 Výhody nové implementace

1. **Moderní technologie**: Vue 3, TypeScript, Vite
2. **Komponentová architektura**: Znovupoužitelné komponenty
3. **Type safety**: TypeScript pro bezpečnost typů
4. **Quasar UI**: Profesionální UI komponenty
5. **Responsivní**: Automatická adaptace na všechny zařízení
6. **Performance**: SPA s rychlým načítáním
7. **Maintainability**: Čistá struktura a separace concerns

## 🚀 Další kroky

1. **Upravit Flask backend** pro API endpointy
2. **Testovat integraci** s reálnými daty
3. **Nasadit do produkce** s build skriptem
4. **Rozšířit funkcionalita** podle potřeby

## 📝 Poznámky

- Původní `index.html` template je zachován pro zpětnou kompatibilitu
- Vue aplikace plně nahrazuje funkcionalitu původního HTML
- Všechny styly a logika jsou převedeny do Vue komponent
- API komunikace je centralizovaná v `services/api.ts`
