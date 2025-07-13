<template>
  <div class="sidebar">
    <!-- Key Metrics Section -->
    <q-card class="sidebar-card">
      <q-expansion-item
        v-model="sectionsExpanded.keyMetrics"
        icon="fas fa-chart-bar"
        label="Klíčové metriky optimalizace"
        header-class="sidebar-header"
        @update:model-value="(val) => saveSectionState('key-metrics', val)"
      >
        <q-card-section>
          <div class="key-metrics" v-if="keyMetrics">
            <q-markup-table class="results-table" dense>
              <tbody>
                <tr v-for="(value, key) in keyMetrics" :key="key">
                  <td class="result-label">{{ formatKey(key) }}</td>
                  <td class="result-value">{{ formatValue(key, value) }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </div>
          <div v-else class="no-data-message">
            Žádná data k zobrazení
          </div>

          <q-markup-table v-if="results" class="results-table" dense>
            <tbody>
              <tr v-for="(value, key) in results" :key="key">
                <td class="result-label">{{ formatKey(key) }}</td>
                <td class="result-value">{{ formatValue(key, value) }}</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>
      </q-expansion-item>
    </q-card>

    <!-- System Info Section -->
    <q-card class="sidebar-card">
      <q-expansion-item
        v-model="sectionsExpanded.systemInfo"
        icon="fas fa-info-circle"
        label="Systémové informace"
        header-class="sidebar-header"
        @update:model-value="(val) => saveSectionState('system-info', val)"
      >
        <q-card-section>
          <q-markup-table class="info-table" dense>
            <tbody>
              <tr>
                <td class="info-label">Verze optimalizátoru</td>
                <td>{{ version }}</td>
              </tr>
              <tr>
                <td class="info-label">Poslední aktualizace</td>
                <td>{{ generatedAt }}</td>
              </tr>
              <tr>
                <td class="info-label">Doba výpočtu</td>
                <td>{{ solveTime?.toFixed(1) }}s</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>
      </q-expansion-item>
    </q-card>

    <!-- Configuration Section -->
    <q-card class="sidebar-card">
      <q-expansion-item
        v-model="sectionsExpanded.configuration"
        icon="fas fa-cog"
        label="Aktivní konfigurace"
        header-class="sidebar-header"
        @update:model-value="(val) => saveSectionState('configuration', val)"
      >
        <q-card-section>
          <q-markup-table class="config-table" dense>
            <tbody>
              <tr v-for="(value, key) in options" :key="key">
                <td class="config-label">{{ formatKey(key) }}</td>
                <td class="config-value">{{ formatValue(key, value) }}</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>
      </q-expansion-item>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

interface Props {
  keyMetrics: Record<string, any> | null;
  results: Record<string, any>;
  version: string;
  generatedAt: string;
  solveTime?: number;
  options: Record<string, any>;
}

defineProps<Props>()

const sectionsExpanded = ref({
  keyMetrics: true,
  systemInfo: true,
  configuration: true
})

onMounted(() => {
  // Restore section states from localStorage
  const keyMetricsState = localStorage.getItem('key-metrics')
  const systemInfoState = localStorage.getItem('system-info')
  const configurationState = localStorage.getItem('configuration')

  if (keyMetricsState) {
    sectionsExpanded.value.keyMetrics = keyMetricsState === 'expanded'
  }
  if (systemInfoState) {
    sectionsExpanded.value.systemInfo = systemInfoState === 'expanded'
  }
  if (configurationState) {
    sectionsExpanded.value.configuration = configurationState === 'expanded'
  }
})

function saveSectionState(sectionId: string, expanded: boolean) {
  localStorage.setItem(sectionId, expanded ? 'expanded' : 'collapsed')
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatValue(key: string, value: any): string {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  
  if (typeof value === 'number') {
    // Format based on key type
    if (key.includes('time') || key.includes('duration')) {
      return `${value.toFixed(1)}s`
    }
    if (key.includes('rate') || key.includes('percentage')) {
      return `${(value * 100).toFixed(1)}%`
    }
    if (key.includes('cost') || key.includes('price') || key.includes('bilance')) {
      return `${value.toFixed(2)} Kč`
    }
    if (key.includes('power') || key.includes('consumption') || key.includes('injection')) {
      return `${value.toFixed(2)} kWh`
    }
    return value.toFixed(2)
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Ano' : 'Ne'
  }
  
  return String(value)
}
</script>

<style lang="scss" scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

:deep(.sidebar-header) {
  background: var(--q-grey-2);
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-bottom: 1px solid var(--q-grey-4);
}

:deep(.sidebar-header:hover) {
  background: var(--q-grey-3);
}

.key-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.metric-item {
  background: var(--q-grey-1);
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
  border: 1px solid var(--q-grey-4);
  transition: all 0.2s ease-in-out;
}

.metric-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--q-dark);
  margin-bottom: 0.25rem;
}

.metric-label {
  font-size: 0.7rem;
  color: var(--q-grey-6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.results-table,
.info-table,
.config-table {
  :deep(tbody tr) {
    border-bottom: 1px solid var(--q-grey-4);
    transition: background-color 0.15s ease-in-out;
  }

  :deep(tbody tr:hover) {
    background: rgba(59, 130, 246, 0.03);
  }

  :deep(td) {
    padding: 0.75rem 0;
    font-size: 0.875rem;
  }
}

.result-label,
.info-label,
.config-label {
  font-weight: 600;
  color: var(--q-dark);
  width: 45%;
}

.result-value,
.config-value {
  color: var(--q-grey-7);
}

@media (max-width: 1200px) {
  .key-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
