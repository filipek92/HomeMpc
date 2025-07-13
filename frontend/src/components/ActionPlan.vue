<template>
  <q-card class="action-plan-card">
    <q-card-section>
      <div class="section-title">
        <q-icon name="fas fa-calendar-alt" size="sm" />
        Plán akcí a aktuální stav
      </div>

      <!-- Current Actions Table -->
      <div class="subsection">
        <h4 class="subsection-title">
          <q-icon name="fas fa-play-circle" size="sm" />
          Aktuální akce
        </h4>
        
        <q-markup-table class="current-actions-table">
          <tbody>
            <tr v-if="currentActions.charger_use_mode">
              <td class="action-label">Režim střídače</td>
              <td>
                <q-chip
                  :color="getModeColor(currentActions.charger_use_mode)"
                  text-color="white"
                  :label="currentActions.charger_use_mode"
                  dense
                />
              </td>
            </tr>
            <tr v-if="currentActions.upper_accumulation_on !== undefined">
              <td class="action-label">Horní akumulace</td>
              <td>
                <q-chip
                  :color="currentActions.upper_accumulation_on ? 'positive' : 'grey'"
                  text-color="white"
                  :label="currentActions.upper_accumulation_on ? 'Zapnuto' : 'Vypnuto'"
                  dense
                />
              </td>
            </tr>
            <tr v-if="currentActions.lower_accumulation_on !== undefined">
              <td class="action-label">Spodní akumulace</td>
              <td>
                <q-chip
                  :color="currentActions.lower_accumulation_on ? 'positive' : 'grey'"
                  text-color="white"
                  :label="currentActions.lower_accumulation_on ? 'Zapnuto' : 'Vypnuto'"
                  dense
                />
              </td>
            </tr>
            <tr v-if="currentActions.max_heat_on !== undefined">
              <td class="action-label">Maximální ohřev</td>
              <td>
                <q-chip
                  :color="currentActions.max_heat_on ? 'positive' : 'grey'"
                  text-color="white"
                  :label="currentActions.max_heat_on ? 'Zapnuto' : 'Vypnuto'"
                  dense
                />
              </td>
            </tr>
            <tr v-if="currentActions.forced_heating_block !== undefined">
              <td class="action-label">Blokování ohřevu</td>
              <td>
                <q-chip
                  :color="currentActions.forced_heating_block ? 'positive' : 'grey'"
                  text-color="white"
                  :label="currentActions.forced_heating_block ? 'Zapnuto' : 'Vypnuto'"
                  dense
                />
              </td>
            </tr>
            <tr v-if="currentActions.battery_target_soc">
              <td class="action-label">Cílový SOC</td>
              <td>{{ currentActions.battery_target_soc.toFixed(1) }}%</td>
            </tr>
            <tr v-if="currentActions.reserve_power_charging">
              <td class="action-label">Rezervní výkon</td>
              <td>{{ currentActions.reserve_power_charging.toFixed(0) }} W</td>
            </tr>
          </tbody>
        </q-markup-table>
      </div>

      <!-- Action Plan Timeline -->
      <div v-if="timeline && timeline.times" class="subsection">
        <h4 class="subsection-title">
          <q-icon name="fas fa-clock" size="sm" />
          Plán akcí
        </h4>
        
        <div class="timeline-container">
          <q-markup-table class="timeline-table" dense>
            <thead>
              <tr>
                <th>Čas</th>
                <th>Režim střídače</th>
                <th><q-icon name="fas fa-battery-half" size="sm" title="SoC baterie" /></th>
                <th><q-icon name="fas fa-thermometer-full" size="sm" title="Horní teplota" /></th>
                <th><q-icon name="fas fa-thermometer-empty" size="sm" title="Spodní teplota" /></th>
                <th><q-icon name="fas fa-arrow-up" size="sm" title="Horní akumulace" /></th>
                <th><q-icon name="fas fa-arrow-down" size="sm" title="Spodní akumulace" /></th>
                <th><q-icon name="fas fa-fire" size="sm" title="Max. ohřev" /></th>
                <th><q-icon name="fas fa-bath" size="sm" title="Komfortní ohřev ze sítě" /></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(time, index) in timeline.times" :key="index">
                <td>{{ time }}</td>
                <td>
                  <q-chip
                    :color="getModeColor(timeline.charger_mode[index])"
                    text-color="white"
                    :label="timeline.charger_mode[index]"
                    dense
                    size="sm"
                  />
                </td>
                <td>{{ timeline.battery_target_soc[index]?.toFixed(0) }}%</td>
                <td>{{ timeline.temp_upper?.[index]?.toFixed(1) || 'N/A' }}°C</td>
                <td>{{ timeline.temp_lower?.[index]?.toFixed(1) || 'N/A' }}°C</td>
                <td>
                  <q-icon
                    v-if="timeline.upper_accumulation[index]"
                    name="fas fa-arrow-up"
                    color="warning"
                    size="sm"
                  />
                </td>
                <td>
                  <q-icon
                    v-if="timeline.lower_accumulation[index]"
                    name="fas fa-arrow-down"
                    color="warning"
                    size="sm"
                  />
                </td>
                <td>
                  <q-icon
                    v-if="timeline.max_heat[index]"
                    name="fas fa-fire"
                    color="warning"
                    size="sm"
                  />
                </td>
                <td>
                  <q-icon
                    v-if="timeline.comfort_heating_grid?.[index]"
                    name="fas fa-bath"
                    color="info"
                    size="sm"
                  />
                </td>
              </tr>
            </tbody>
          </q-markup-table>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import type { CurrentActions, TimelineData } from '@/types/dashboard'

interface Props {
  currentActions: CurrentActions
  timeline?: TimelineData
}

defineProps<Props>()

function getModeColor(mode: string): string {
  const modeColorMap: Record<string, string> = {
    'Manual Charge': 'amber',
    'Manual Discharge': 'deep-orange',
    'Manual Idle': 'grey',
    'Feedin Priority': 'purple',
    'Back Up Mode': 'green'
  }
  
  return modeColorMap[mode] || 'grey'
}
</script>

<style lang="scss" scoped>
.action-plan-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--q-dark);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.subsection {
  margin-bottom: 2rem;
}

.subsection-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--q-dark);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
}

.current-actions-table {
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

  .action-label {
    font-weight: 600;
    color: var(--q-dark);
    width: 45%;
  }
}

.timeline-container {
  overflow-x: auto;
}

.timeline-table {
  font-size: 0.8rem;
  min-width: 800px;

  :deep(th) {
    background: var(--q-grey-2);
    font-weight: 600;
    color: var(--q-dark);
    position: sticky;
    top: 0;
    font-size: 0.75rem;
    padding: 0.5rem 0.25rem;
  }

  :deep(td) {
    padding: 0.5rem 0.25rem;
    text-align: left;
    border-bottom: 1px solid var(--q-grey-4);
  }

  :deep(tbody tr:hover) {
    background: rgba(59, 130, 246, 0.05);
  }
}

@media (max-width: 768px) {
  .timeline-table {
    :deep(th:nth-child(n+5)),
    :deep(td:nth-child(n+5)) {
      display: none;
    }
  }
}
</style>
