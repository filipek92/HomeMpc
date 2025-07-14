<template>
  <q-header elevated class="dashboard-header">
    <q-toolbar class="header-toolbar">
      <div class="header-main">
        <div class="header-title">
          <q-icon name="fas fa-bolt" size="md" color="primary" />
          <div class="title-text">PowerStreamPlan</div>
        </div>
        <div class="header-badges">
          <q-chip
            dense
            color="primary"
            text-color="white"
            :label="`v${version}`"
            class="version-chip"
          />
          <q-chip
            dense
            color="positive"
            text-color="white"
            icon="fas fa-circle"
            label="Online"
            class="status-chip"
          />
        </div>
      </div>

      <q-space />

      <div class="header-actions">
        <q-btn
          flat
          dense
          icon="fas fa-cog"
          label="Nastavení"
          @click="$router.push('/settings')"
          class="header-btn"
        />

        <q-btn
          flat
          dense
          icon="fas fa-download"
          label="Stáhnout CSV"
          @click="handleDownloadCSV"
          :loading="downloadLoading"
          class="header-btn"
        />

        <q-btn
          flat
          dense
          icon="fas fa-sync-alt"
          label="Aktualizovat"
          @click="handleRegenerate"
          :loading="loading"
          class="header-btn"
        />

        <q-btn
          flat
          dense
          icon="fas fa-filter"
          label="Filtry"
          @click="$emit('toggle-controls')"
          class="header-btn"
        />

        <q-btn
          flat
          dense
          icon="fas fa-home"
          label="Aktuální data"
          @click="handleCurrentData"
          class="header-btn"
        />

        <q-btn
          flat
          dense
          :icon="autoRefreshEnabled ? 'fas fa-pause' : 'fas fa-play'"
          :label="autoRefreshEnabled ? 'Zastavit auto-refresh' : 'Spustit auto-refresh'"
          @click="toggleAutoRefresh"
          :color="autoRefreshEnabled ? 'positive' : 'grey'"
          class="header-btn"
        />
      </div>
    </q-toolbar>
  </q-header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useQuasar } from 'quasar'

interface Props {
  version: string
}

defineProps<Props>()
defineEmits<{
  'toggle-controls': []
}>()

const $q = useQuasar()
const dashboardStore = useDashboardStore()

const downloadLoading = ref(false)

const { loading, autoRefreshEnabled } = dashboardStore

async function handleDownloadCSV() {
  downloadLoading.value = true
  try {
    await dashboardStore.downloadCSV()
    $q.notify({
      type: 'positive',
      message: 'CSV soubor byl úspěšně stažen',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Chyba při stahování CSV souboru',
      position: 'top'
    })
  } finally {
    downloadLoading.value = false
  }
}

async function handleRegenerate() {
  try {
    await dashboardStore.regenerateOptimization()
    $q.notify({
      type: 'positive',
      message: 'Optimalizace byla úspěšně aktualizována',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Chyba při aktualizaci optimalizace',
      position: 'top'
    })
  }
}

function handleCurrentData() {
  dashboardStore.fetchDashboardData()
}

function toggleAutoRefresh() {
  dashboardStore.toggleAutoRefresh()
  $q.notify({
    type: 'info',
    message: dashboardStore.autoRefreshEnabled
      ? 'Auto-refresh byl zapnut'
      : 'Auto-refresh byl vypnut',
    position: 'top'
  })
}
</script>

<style lang="scss" scoped>
.dashboard-header {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

.header-toolbar {
  padding: 1rem 2rem;
  min-height: 80px;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-text {
  font-size: 2rem;
  font-weight: 700;
  color: var(--q-dark);
}

.header-badges {
  display: flex;
  gap: 0.5rem;
}

.version-chip {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-chip {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.header-btn {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease-in-out;
}

.header-btn:hover {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .header-toolbar {
    flex-direction: column;
    padding: 1rem;
    text-align: center;
  }

  .title-text {
    font-size: 1.5rem;
  }

  .header-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>
