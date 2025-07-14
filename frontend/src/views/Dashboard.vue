<template>
  <q-layout view="hHh lpR fFf">
    <DashboardHeader 
      :version="data?.version || 'N/A'"
      @toggle-controls="controlsVisible = !controlsVisible"
    />

    <q-page-container>
      <q-page class="dashboard-page">
        <div class="dashboard-container">
          <!-- Loading overlay -->
          <q-inner-loading :showing="loading">
            <q-spinner-grid size="50px" color="primary" />
          </q-inner-loading>

          <!-- Error state -->
          <q-banner v-if="error" class="text-white bg-red">
            <template v-slot:avatar>
              <q-icon name="error" />
            </template>
            {{ error }}
            <template v-slot:action>
              <q-btn flat label="Zkusit znovu" @click="fetchDashboardData()" />
            </template>
          </q-banner>

          <!-- Controls -->
          <DashboardControls
            v-if="data"
            :visible="controlsVisible"
            :available-days="data.available_days || []"
            :available-times="data.available_times || []"
            :available-times-display="data.available_times_display || []"
            :current-day="data.day || ''"
            :current-time="data.compare_time || ''"
            :current-view-type="data.view_type || 'tabs'"
            @update-filters="handleUpdateFilters"
          />

          <!-- Status Cards -->
          <StatusCards
            v-if="data"
            :cards="statusCards"
          />

          <!-- Charts -->
          <ChartsContainer v-if="data" />

          <!-- Main Content -->
          <div v-if="data && data.solution" class="main-content">
            <ActionPlan
              :current-actions="data.solution.actions || {}"
              :timeline="data.solution.actions_timeline"
            />

            <DashboardSidebar
              :key-metrics="keyMetrics"
              :results="data.solution.results || {}"
              :version="data.version || 'N/A'"
              :generated-at="data.generated_at || ''"
              :solve-time="0"
              :options="{}"
            />
          </div>

          <!-- Action Section -->
          <ActionSection v-if="data" :generated-at="data.generated_at || ''" />
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { storeToRefs } from "pinia";
import { useDashboardStore } from "@/stores/dashboard";
import type { ControlsForm } from "@/types/dashboard";

// Components
import DashboardHeader from "@/components/DashboardHeader.vue";
import DashboardControls from "@/components/DashboardControls.vue";
import StatusCards from "@/components/StatusCards.vue";
import ChartsContainer from "@/components/ChartsContainer.vue";
import ActionPlan from "@/components/ActionPlan.vue";
import DashboardSidebar from "@/components/DashboardSidebar.vue";
import ActionSection from "@/components/ActionSection.vue";

const dashboardStore = useDashboardStore();
const { data, loading, error, statusCards, keyMetrics } =
  storeToRefs(dashboardStore);

const controlsVisible = ref(false);

onMounted(async () => {
  await dashboardStore.fetchDashboardData();
  dashboardStore.startAutoRefresh();

  // Handle visibility change
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  dashboardStore.stopAutoRefresh();
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    dashboardStore.startAutoRefresh();
  } else {
    dashboardStore.stopAutoRefresh();
  }
}

async function handleUpdateFilters(filters: Partial<ControlsForm>) {
  await dashboardStore.fetchDashboardData(filters);
}
</script>

<style lang="scss" scoped>
.dashboard-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 0;
}

.dashboard-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
  width: 100%;
  min-height: calc(100vh - 80px);
  position: relative;
}

.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1rem 0.5rem;
  }
}
</style>
