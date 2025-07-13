// Mock data pro testování Vue aplikace
import type { DashboardData } from "@/types/dashboard";

export const mockDashboardData: DashboardData = {
  solution: {
    results: {
      temperature_penalty: 1.2,
      total_penalty: 2500,
      runtime_ms: 850,
      solver_status: "Optimal",
      final_solution: "Found",
    },
    actions: [
      {
        timestamp: "2024-01-15T10:00:00",
        action: "Zapnout TČ",
        power: 3500,
        description: "Optimální čas pro vytápění",
      },
      {
        timestamp: "2024-01-15T11:00:00",
        action: "Nabíjet baterii",
        power: 2000,
        description: "Levná elektřina z FVE",
      },
      {
        timestamp: "2024-01-15T12:00:00",
        action: "Vypnout TČ",
        power: 0,
        description: "Vysoké ceny elektřiny",
      },
    ],
  },
  current_state: {
    battery_level: 75,
    temperature: 22.5,
    price_now: 1.85,
    fve_production: 1200,
  },
  forecast_data: {
    timestamps: ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
    electricity_prices: [1.85, 1.92, 2.15, 2.08, 1.76, 1.95],
    fve_forecast: [1200, 1800, 2500, 2200, 1500, 800],
    temperature_forecast: [22.5, 23.1, 23.8, 24.2, 23.9, 23.5],
  },
};
