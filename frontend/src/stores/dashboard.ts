import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { DashboardData, ControlsForm, StatusCard } from "@/types/dashboard";
import { dashboardService } from "@/services/api";
import { mockDashboardData } from "@/mockData";

export const useDashboardStore = defineStore("dashboard", () => {
  // State
  const data = ref<DashboardData | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const autoRefreshEnabled = ref(false);
  
  // Auto-refresh state
  let refreshTimer: NodeJS.Timeout | null = null;

  // Computed
  const statusCards = computed<StatusCard[]>(() => {
    if (!data.value) return [];
    
    // Fallback data from other sources if current_state is empty
    const state = data.value.current_state || {};
    const actions = data.value.solution?.actions || {};
    
    return [
      {
        title: "Baterie",
        value: `${state.battery_level || actions.battery_target_soc || 'N/A'}%`,
        icon: "battery_std",
        color: (state.battery_level || actions.battery_target_soc || 0) > 50 ? "positive" : "warning",
      },
      {
        title: "Režim nabíječky",
        value: `${actions.charger_use_mode || 'N/A'}`,
        icon: "power",
        color: "primary",
      },
      {
        title: "Akumulace",
        value: `${actions.lower_accumulation_on && actions.upper_accumulation_on ? 'Obě zóny' : 
                  actions.lower_accumulation_on ? 'Dolní zóna' : 
                  actions.upper_accumulation_on ? 'Horní zóna' : 'Vypnuto'}`,
        icon: "thermostat",
        color: "info",
      },
      {
        title: "Optimalizace",
        value: data.value.version || 'N/A',
        icon: "settings",
        color: "orange",
      },
    ];
  });

  const keyMetrics = computed(() => {
    if (!data.value?.solution?.results) return null;
    
    const results = data.value.solution.results;
    return {
      temperature_penalty: results.temperature_penalty,
      total_penalty: results.total_penalty,
      runtime_ms: results.runtime_ms,
      solver_status: results.solver_status,
      final_solution: results.final_solution
    };
  });

  const actionPlan = computed(() => {
    if (!data.value?.solution?.actions_timeline) return [];
    return data.value.solution.actions_timeline;
  });

  // Actions
  async function fetchDashboardData(params?: Partial<ControlsForm>) {
    loading.value = true;
    error.value = null;

    try {
      // Volání reálného API
      data.value = await dashboardService.getDashboardData(params);
    } catch (err) {
      error.value =
        err instanceof Error ? err.message : "Chyba při načítání dat";
      console.error("Error fetching dashboard data:", err);
      
      // Fallback na mock data v případě chyby
      console.warn("Používám mock data jako fallback");
      await new Promise((resolve) => setTimeout(resolve, 300));
      data.value = { ...mockDashboardData };
    } finally {
      loading.value = false;
    }
  }

  async function regenerateOptimization() {
    loading.value = true;
    error.value = null;

    try {
      await dashboardService.regenerateOptimization();
      await fetchDashboardData();
    } catch (err) {
      error.value =
        err instanceof Error
          ? err.message
          : "Chyba při regeneraci optimalizace";
      console.error("Error regenerating optimization:", err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function downloadCSV(params?: Partial<ControlsForm>) {
    try {
      const blob = await dashboardService.downloadCSV(params);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `powerplan-data-${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      error.value =
        err instanceof Error ? err.message : "Chyba při stahování CSV";
      console.error("Error downloading CSV:", err);
      throw err;
    }
  }

  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    
    autoRefreshEnabled.value = true;
    refreshTimer = setInterval(async () => {
      await fetchDashboardData();
    }, 300000); // 5 minut
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
    autoRefreshEnabled.value = false;
  }

  function toggleAutoRefresh() {
    if (autoRefreshEnabled.value) {
      stopAutoRefresh();
    } else {
      startAutoRefresh();
    }
  }

  return {
    // State
    data,
    loading,
    error,
    autoRefreshEnabled,
    // Computed
    statusCards,
    keyMetrics,
    actionPlan,
    // Actions
    fetchDashboardData,
    regenerateOptimization,
    downloadCSV,
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
  };
});
