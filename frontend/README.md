# PowerStreamPlan Frontend

Vue 3 frontend aplikace pro PowerStreamPlan energetický dashboard s Quasar UI frameworkem.

## 🚀 Technologie

- **Vue 3** - Composition API
- **TypeScript** - Type safety
- **Quasar** - UI komponenty
- **Pinia** - State management
- **Vue Router** - Routing
- **Vite** - Build tool
- **Axios** - HTTP klient

## 📦 Instalace

```bash
cd frontend
npm install
```

## 🛠️ Vývoj

```bash
# Spustit dev server
npm run dev

# Aplikace bude dostupná na http://localhost:3000
# API proxy je nakonfigurována na http://localhost:5000
```

## 🏗️ Build

```bash
# Build pro produkci
npm run build

# Výstup bude v ../power_stream_plan/static/dist/
```

## 📁 Struktura projektu

```
frontend/
├── src/
│   ├── components/          # Vue komponenty
│   │   ├── DashboardHeader.vue
│   │   ├── DashboardControls.vue
│   │   ├── StatusCards.vue
│   │   ├── ChartsContainer.vue
│   │   ├── ActionPlan.vue
│   │   ├── DashboardSidebar.vue
│   │   └── ActionSection.vue
│   ├── views/              # Vue views/stránky
│   │   ├── Dashboard.vue
│   │   └── Settings.vue
│   ├── stores/             # Pinia stores
│   │   └── dashboard.ts
│   ├── services/           # API služby
│   │   └── api.ts
│   ├── types/              # TypeScript typy
│   │   └── dashboard.ts
│   ├── styles/             # Styly
│   │   ├── main.scss
│   │   └── quasar-variables.sass
│   ├── router/             # Vue Router
│   │   └── index.ts
│   ├── App.vue             # Root komponenta
│   └── main.ts             # Entry point
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

## 🔧 Konfigurace

### Vite Config
- **Dev server**: Port 3000
- **API proxy**: `/api` -> `http://localhost:5000`
- **Build output**: `../power_stream_plan/static/dist/`

### API Endpoints
Aplikace očekává následující API endpointy:

- `GET /` - Dashboard data
- `POST /regenerate` - Regenerace optimalizace
- `GET /download_csv` - Stažení CSV
- `GET /settings` - Nastavení
- `POST /settings` - Uložení nastavení

## 🎨 UI Komponenty

### Header
- Logo a název aplikace
- Verze a status badge
- Tlačítka pro akce (nastavení, stažení, aktualizace, filtry)

### Controls
- Filtry pro den, čas a typ zobrazení
- Auto-submit při změně dne

### Status Cards
- SoC baterie s progress barem
- Režim střídače s barevným označením
- FVE přebytek
- Síťové toky

### Charts Container
- Taby pro různé typy grafů
- Plně responzivní design
- LocalStorage pro zapamatování aktivního tabu

### Action Plan
- Tabulka aktuálních akcí
- Timeline plánovaných akcí
- Barevné označení režimů

### Sidebar
- Klíčové metriky s kartami
- Systémové informace
- Konfigurace
- Collapsible sekce s localStorage

### Action Section
- Informace o generování
- Tlačítka pro CSV a regeneraci

## 🔄 State Management

Aplikace používá Pinia store (`useDashboardStore`) pro:

- **Data management**: Načítání a ukládání dat
- **Loading states**: Indikátory načítání
- **Error handling**: Zpracování chyb
- **Auto-refresh**: Automatické obnovování dat
- **Actions**: Regenerace, stažení CSV

## 📱 Responsivní design

- **Desktop**: Grid layout 2+1 sloupce
- **Tablet**: Jednosloupcový layout
- **Mobil**: Kompaktní design s upravenými taby

## 🔧 Vývoj

Pro vývoj spusťte současně:

1. **Backend** (Python Flask server na portu 5000)
2. **Frontend** (Vite dev server na portu 3000)

```bash
# Terminal 1 - Backend
cd power_stream_plan
python powerplan_server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🚀 Produkce

Pro produkční nasazení:

1. Build frontend: `npm run build`
2. Soubory se zkompilují do `../power_stream_plan/static/dist/`
3. Flask server automaticky servíruje statické soubory

## 📄 Licence

Součást PowerStreamPlan projektu.
