<template>
  <q-card class="charts-container">
    <q-tabs
      v-model="activeTab"
      dense
      class="text-grey-6"
      active-color="primary"
      indicator-color="primary"
      align="left"
      narrow-indicator
    >
      <q-tab name="overview" icon="fas fa-chart-line" label="Přehled" />
      <q-tab name="states" icon="fas fa-battery-half" label="Stavy úložišť" />
      <q-tab name="power" icon="fas fa-bolt" label="Výkony" />
      <q-tab name="prices" icon="fas fa-coins" label="Ceny" />
      <q-tab name="heating" icon="fas fa-thermometer-half" label="Teplo" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="activeTab" animated>
      <q-tab-panel name="overview" class="chart-panel">
        <PlotlyChart
          v-if="dashboardStore.data"
          :data="overviewChartData"
          :layout="overviewLayout"
        />
        <div v-else class="text-center q-pa-xl">
          <q-spinner size="40px" color="primary" />
          <div class="q-mt-md">Načítání dat...</div>
        </div>
      </q-tab-panel>

      <q-tab-panel name="states" class="chart-panel">
        <PlotlyChart
          v-if="dashboardStore.data"
          :data="statesChartData"
          :layout="statesLayout"
        />
        <div v-else class="text-center q-pa-xl">
          <q-spinner size="40px" color="primary" />
          <div class="q-mt-md">Načítání dat...</div>
        </div>
      </q-tab-panel>

      <q-tab-panel name="power" class="chart-panel">
        <PlotlyChart
          v-if="dashboardStore.data"
          :data="powerChartData"
          :layout="powerLayout"
        />
        <div v-else class="text-center q-pa-xl">
          <q-spinner size="40px" color="primary" />
          <div class="q-mt-md">Načítání dat...</div>
        </div>
      </q-tab-panel>

      <q-tab-panel name="prices" class="chart-panel">
        <PlotlyChart
          v-if="dashboardStore.data"
          :data="pricesChartData"
          :layout="pricesLayout"
        />
        <div v-else class="text-center q-pa-xl">
          <q-spinner size="40px" color="primary" />
          <div class="q-mt-md">Načítání dat...</div>
        </div>
      </q-tab-panel>

      <q-tab-panel name="heating" class="chart-panel">
        <PlotlyChart
          v-if="dashboardStore.data"
          :data="heatingChartData"
          :layout="heatingLayout"
        />
        <div v-else class="text-center q-pa-xl">
          <q-spinner size="40px" color="primary" />
          <div class="q-mt-md">Načítání dat...</div>
        </div>
      </q-tab-panel>
    </q-tab-panels>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useDashboardStore } from "../stores/dashboard";
import { useChartGenerator } from "../composables/useChartGenerator";
import PlotlyChart from "./PlotlyChart.vue";

const dashboardStore = useDashboardStore();
const chartGenerator = useChartGenerator();
const activeTab = ref("overview");

// Computed properties for chart data
const overviewChartData = computed(() => {
  if (!dashboardStore.data) return [];
  return chartGenerator.generateOverviewChart(dashboardStore.data);
});

const statesChartData = computed(() => {
  if (!dashboardStore.data) return [];
  return chartGenerator.generateStatesChart(dashboardStore.data);
});

const powerChartData = computed(() => {
  if (!dashboardStore.data) return [];
  return chartGenerator.generatePowerChart(dashboardStore.data);
});

const pricesChartData = computed(() => {
  if (!dashboardStore.data) return [];
  return chartGenerator.generatePricesChart(dashboardStore.data);
});

const heatingChartData = computed(() => {
  if (!dashboardStore.data) return [];
  return chartGenerator.generateHeatingChart(dashboardStore.data);
});

// Computed properties for chart layouts
const overviewLayout = computed(() => {
  return chartGenerator.getChartLayout("Přehled optimalizace", "Hodnota");
});

const statesLayout = computed(() => {
  return chartGenerator.getChartLayout("Stavy úložišť", "Hodnota");
});

const powerLayout = computed(() => {
  return chartGenerator.getChartLayout("Výkony a energie", "Výkon [kW]");
});

const pricesLayout = computed(() => {
  return chartGenerator.getChartLayout("Ceny elektřiny", "Cena [Kč/kWh]");
});

const heatingLayout = computed(() => {
  return chartGenerator.getChartLayout("Ohřev a teploty", "Teplota [°C]", true);
});

// Save active tab to localStorage
const saveActiveTab = (newTab: string) => {
  localStorage.setItem("activeTab", newTab);
};

// Restore active tab from localStorage
onMounted(() => {
  const savedTab = localStorage.getItem("activeTab");
  if (savedTab) {
    activeTab.value = savedTab;
  }
});

// Watch active tab changes
watch(activeTab, (newTab: string) => {
  saveActiveTab(newTab);
});
</script>

<style lang="scss" scoped>
.charts-container {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.chart-panel {
  padding: 0;
}

.chart-container {
  width: 100%;
  min-height: 300px;
  border-radius: 1rem;
  overflow: hidden;
  position: relative;
}

:deep(.q-tabs) {
  background: var(--q-grey-2);
}

:deep(.q-tab) {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease-in-out;
}

:deep(.q-tab:hover) {
  background: rgba(59, 130, 246, 0.05);
}

:deep(.q-tab--active) {
  background: var(--q-grey-1);
  font-weight: 600;
}

@media (max-width: 768px) {
  :deep(.q-tabs) {
    flex-wrap: wrap;
  }

  :deep(.q-tab) {
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
  }
}
</style>
