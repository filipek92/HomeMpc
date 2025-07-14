import type { Data } from "plotly.js";
import type { DashboardData } from "@/types/dashboard";

export function useChartGenerator() {
  const generateOverviewChart = (data: DashboardData): Data[] => {
    if (!data.chart_data?.outputs) return [];
    
    const { outputs, inputs, timestamps } = data.chart_data;
    const timeline = data.solution?.actions_timeline || {};
    
    return [
      {
        x: timestamps,
        y: timeline.battery_target_soc || [],
        type: "scatter",
        mode: "lines+markers",
        name: "SoC baterie (%)",
        line: { width: 3, color: "#4db6ac" },
        marker: { size: 4 },
      },
      {
        x: timestamps,
        y: inputs.fve_pred || [],
        type: "scatter",
        mode: "lines",
        name: "FVE predikce",
        line: { width: 2, color: "#ff9800" },
      },
      {
        x: timestamps,
        y: timeline.fve_surplus || [],
        type: "scatter",
        mode: "lines",
        name: "FVE přebytek",
        line: { width: 2, color: "#ffc107" },
      },
      {
        x: timestamps,
        y: inputs.load_pred || [],
        type: "scatter",
        mode: "lines",
        name: "Spotřeba predikce",
        line: { width: 2, color: "#9c27b0" },
      },
      {
        x: timestamps,
        y: outputs.g_buy || [],
        type: "bar",
        name: "Nákup ze sítě",
        marker: { color: "#488fc2" },
        opacity: 0.7,
      },
      {
        x: timestamps,
        y: (outputs.g_sell || []).map((val: number) => -val),
        type: "bar",
        name: "Prodej do sítě",
        marker: { color: "#8353d1" },
        opacity: 0.7,
      },
    ];
  };

  const generateStatesChart = (data: DashboardData): Data[] => {
    if (!data.chart_data?.outputs) return [];
    
    const { timestamps } = data.chart_data;
    const timeline = data.solution?.actions_timeline || {};
    
    return [
      {
        x: timestamps,
        y: timeline.battery_target_soc || [],
        type: "scatter",
        mode: "lines+markers",
        name: "SoC baterie (%)",
        line: { width: 3, color: "#4db6ac" },
        marker: { size: 4 },
      },
      {
        x: timestamps,
        y: timeline.temp_lower || [],
        type: "scatter",
        mode: "lines",
        name: "Teplota dolní zóny",
        line: { width: 2, color: "#ff8f00" },
      },
      {
        x: timestamps,
        y: timeline.temp_upper || [],
        type: "scatter",
        mode: "lines",
        name: "Teplota horní zóny",
        line: { width: 2, color: "#ffc107" },
      },
    ];
  };

  const generatePowerChart = (data: DashboardData): Data[] => {
    if (!data.chart_data?.outputs) return [];
    
    const { outputs, inputs, timestamps } = data.chart_data;
    const timeline = data.solution?.actions_timeline || {};
    
    return [
      {
        x: timestamps,
        y: inputs.fve_pred || [],
        type: "scatter",
        mode: "lines",
        name: "FVE predikce",
        line: { width: 3, color: "#ff9800" },
      },
      {
        x: timestamps,
        y: timeline.fve_surplus || [],
        type: "scatter",
        mode: "lines",
        name: "FVE přebytek",
        line: { width: 2, color: "#ffc107" },
      },
      {
        x: timestamps,
        y: inputs.load_pred || [],
        type: "scatter",
        mode: "lines",
        name: "Spotřeba predikce",
        line: { width: 2, color: "#9c27b0" },
      },
      {
        x: timestamps,
        y: outputs.h_in_lower || [],
        type: "bar",
        name: "Ohřev dolní zóny",
        marker: { color: "#c2185b" },
        opacity: 0.7,
      },
      {
        x: timestamps,
        y: outputs.h_in_upper || [],
        type: "bar",
        name: "Ohřev horní zóny",
        marker: { color: "#e91e63" },
        opacity: 0.7,
      },
      {
        x: timestamps,
        y: outputs.g_buy || [],
        type: "bar",
        name: "Nákup ze sítě",
        marker: { color: "#488fc2" },
        opacity: 0.7,
      },
      {
        x: timestamps,
        y: (outputs.g_sell || []).map((val: number) => -val),
        type: "bar",
        name: "Prodej do sítě",
        marker: { color: "#8353d1" },
        opacity: 0.7,
      },
    ];
  };

  const generatePricesChart = (data: DashboardData): Data[] => {
    if (!data.chart_data?.inputs) return [];
    
    const { inputs, timestamps } = data.chart_data;
    
    return [
      {
        x: timestamps,
        y: inputs.buy_price || [],
        type: "scatter",
        mode: "lines+markers",
        name: "Cena nákup",
        line: { shape: "hv", width: 3, color: "#488fc2" },
        marker: { size: 6 },
      },
      {
        x: timestamps,
        y: inputs.sell_price || [],
        type: "scatter",
        mode: "lines+markers",
        name: "Cena prodej",
        line: { shape: "hv", width: 3, color: "#8353d1" },
        marker: { size: 6 },
      },
    ];
  };

  const generateHeatingChart = (data: DashboardData): Data[] => {
    if (!data.chart_data?.outputs) return [];
    
    const { outputs, timestamps } = data.chart_data;
    const timeline = data.solution?.actions_timeline || {};
    
    return [
      {
        x: timestamps,
        y: timeline.temp_lower || [],
        type: "scatter",
        mode: "lines",
        name: "Teplota dolní zóny",
        line: { width: 2, color: "#ff8f00" },
      },
      {
        x: timestamps,
        y: timeline.temp_upper || [],
        type: "scatter",
        mode: "lines",
        name: "Teplota horní zóny",
        line: { width: 2, color: "#ffc107" },
      },
      {
        x: timestamps,
        y: outputs.h_in_lower || [],
        type: "bar",
        name: "Ohřev dolní zóny",
        marker: { color: "#c2185b" },
        opacity: 0.7,
        yaxis: "y2",
      },
      {
        x: timestamps,
        y: outputs.h_in_upper || [],
        type: "bar",
        name: "Ohřev horní zóny",
        marker: { color: "#e91e63" },
        opacity: 0.7,
        yaxis: "y2",
      },
    ];
  };

  const getChartLayout = (
    title: string,
    yAxisTitle: string,
    hasSecondaryAxis = false,
  ) => {
    const layout: any = {
      title: {
        text: title,
        x: 0.5,
        font: { size: 16 },
      },
      xaxis: {
        title: { text: "Čas" },
      },
      yaxis: {
        title: { text: yAxisTitle },
      },
      showlegend: true,
      autosize: true,
      height: 400,
    };

    if (hasSecondaryAxis) {
      layout.yaxis2 = {
        title: { text: "Výkon [kW]" },
        overlaying: "y",
        side: "right",
      };
    }

    return layout;
  };

  return {
    generateOverviewChart,
    generateStatesChart,
    generatePowerChart,
    generatePricesChart,
    generateHeatingChart,
    getChartLayout,
  };
}
