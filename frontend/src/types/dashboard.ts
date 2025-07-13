export interface StatusCard {
  title: string
  icon: string
  value: string | number
  unit?: string
  color: string
  subtitle?: string
  progress?: number
}

export interface ModeBadge {
  mode: string
  color: string
  label: string
}

export interface CurrentActions {
  charger_use_mode?: string
  upper_accumulation_on?: boolean
  lower_accumulation_on?: boolean
  max_heat_on?: boolean
  forced_heating_block?: boolean
  battery_target_soc?: number
  reserve_power_charging?: number
}

export interface OptimizationResults {
  net_bilance: number
  grid_consumption: number
  grid_injection: number
  self_consumption_rate: number
  solve_time: number
  [key: string]: any
}

export interface TimelineData {
  times: string[]
  charger_mode: string[]
  battery_target_soc: number[]
  temp_upper?: number[]
  temp_lower?: number[]
  upper_accumulation: boolean[]
  lower_accumulation: boolean[]
  max_heat: boolean[]
  comfort_heating_grid?: boolean[]
  fve_surplus?: number[]
  grid_buy?: number[]
  grid_sell?: number[]
}

export interface Solution {
  actions: CurrentActions;
  results: OptimizationResults;
  actions_timeline: TimelineData;
  options: Record<string, any>;
  solve_time: number;
}

export interface CurrentState {
  battery_level: number;
  temperature: number;
  price_now: number;
  fve_production: number;
}

export interface ForecastData {
  timestamps: string[];
  electricity_prices: number[];
  fve_forecast: number[];
  temperature_forecast: number[];
}

export interface DashboardData {
  solution: Solution;
  current_state: CurrentState;
  forecast_data: ForecastData;
  graphs: {
    overview: string;
    states: string;
    power: string;
    prices: string;
    heating: string;
    actions: string;
  };
  version: string;
  generated_at: string;
  available_days: string[];
  available_times: string[];
  available_times_display: string[];
  day: string;
  compare_time?: string;
  view_type?: string;
}

export interface ControlsForm {
  day: string
  time: string
  view_type: string
}
