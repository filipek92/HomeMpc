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
      <q-tab name="actions" icon="fas fa-tasks" label="Akce" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="activeTab" animated>
      <q-tab-panel name="overview" class="chart-panel" data-tab="overview">
        <div v-html="graphs.overview" class="chart-container" ref="overviewChart"></div>
      </q-tab-panel>

      <q-tab-panel name="states" class="chart-panel" data-tab="states">
        <div v-html="graphs.states" class="chart-container" ref="statesChart"></div>
      </q-tab-panel>

      <q-tab-panel name="power" class="chart-panel" data-tab="power">
        <div v-html="graphs.power" class="chart-container" ref="powerChart"></div>
      </q-tab-panel>

      <q-tab-panel name="prices" class="chart-panel" data-tab="prices">
        <div v-html="graphs.prices" class="chart-container" ref="pricesChart"></div>
      </q-tab-panel>

      <q-tab-panel name="heating" class="chart-panel" data-tab="heating">
        <div v-html="graphs.heating" class="chart-container" ref="heatingChart"></div>
      </q-tab-panel>

      <q-tab-panel name="actions" class="chart-panel" data-tab="actions">
        <div v-html="graphs.actions" class="chart-container" ref="actionsChart"></div>
      </q-tab-panel>
    </q-tab-panels>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue';

interface Props {
  graphs: {
    overview: string;
    states: string;
    power: string;
    prices: string;
    heating: string;
    actions: string;
  };
}

const props = defineProps<Props>();
const activeTab = ref('overview');

// Function to execute scripts in HTML content
const executeScripts = (element: HTMLElement) => {
  if (!element) return;
  
  const scripts = element.querySelectorAll('script');
  scripts.forEach(script => {
    if (script.innerHTML && script.innerHTML.trim()) {
      try {
        // Execute the script content
        const func = new Function(script.innerHTML);
        func();
      } catch (error) {
        console.error('Error executing Plotly script:', error);
      }
    }
  });
};

// Re-execute scripts when graphs change
watch(
  () => props.graphs,
  () => {
    nextTick(() => {
      // Wait a bit for DOM to update
      setTimeout(() => {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
          executeScripts(container as HTMLElement);
        });
      }, 100);
    });
  },
  { immediate: true }
);

// Re-execute script for active tab when tab changes
watch(activeTab, () => {
  nextTick(() => {
    setTimeout(() => {
      const activeContainer = document.querySelector(`[data-tab="${activeTab.value}"] .chart-container`);
      if (activeContainer) {
        executeScripts(activeContainer as HTMLElement);
      }
    }, 200);
  });
});

// Save active tab to localStorage
watch(activeTab, (newTab) => {
  localStorage.setItem('activeTab', newTab);
});

// Restore active tab from localStorage
onMounted(() => {
  const savedTab = localStorage.getItem('activeTab');
  if (savedTab) {
    activeTab.value = savedTab;
  }
  
  // Execute scripts on mount
  nextTick(() => {
    setTimeout(() => {
      const chartContainers = document.querySelectorAll('.chart-container');
      chartContainers.forEach(container => {
        executeScripts(container as HTMLElement);
      });
    }, 300);
  });
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
