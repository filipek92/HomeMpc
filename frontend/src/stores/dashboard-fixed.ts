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

  // Computed
  const statusCards = computed<StatusCard[]>(() => {
    if (!data.value?.current_state) return [];
    
    const state = data.value.current_state;
    return [
      {
        title: "Baterie",
        value: `${state.battery_level}%`,
        icon: "battery_std",
        color: state.battery_level > 50 ? "positive" : "warning"
      },
      {
        title: "Teplota",
        value: `${state.temperature}°C`,
        icon: "thermostat",
        color: "primary"
      },
      {
        title: "Cena elektřiny",
        value: `${state.price_now} Kč/kWh`,
        icon: "euro",
        color: "info"
      },
      {
        title: "FVE výroba",
        value: `${state.fve_production} W`,
        icon: "wb_sunny",
        color: "orange"
      }
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
    if (!data.value?.solution?.actions) return [];
    return data.value.solution.actions;
  });

  // Actions
  async function fetchDashboardData(params?: Partial<ControlsForm>) {
    loading.value = true;
    error.value = null;

    try {
      // Pro vývoj použijeme mock data pokud API selže
      try {
        data.value = await dashboardService.getDashboardData(params);
      } catch (apiError) {
        console.warn("API nedostupné, používám mock data:", apiError);
        // Použij mock data s malým delay pro simulaci API
        await new Promise((resolve) => setTimeout(resolve, 500));
        data.value = mockDashboardData as DashboardData;
      }
    } catch (err) {
      error.value =
        err instanceof Error ? err.message : "Chyba při načítání dat";
      console.error("Error fetching dashboard data:", err);
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

  return {
    // State
    data,
    loading,
    error,
    // Computed
    statusCards,
    keyMetrics,
    actionPlan,
    // Actions
    fetchDashboardData,
    regenerateOptimization,
    downloadCSV
  };
});
