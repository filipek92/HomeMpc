<template>
  <div class="status-overview">
    <q-card
      v-for="card in cards"
      :key="card.title"
      class="status-card"
      @mouseover="handleCardHover"
      @mouseleave="handleCardLeave"
    >
      <q-card-section class="status-card-content">
        <div class="status-card-header">
          <div class="status-card-title">
            <q-icon :name="card.icon" size="sm" />
            {{ card.title }}
          </div>
          <q-avatar
            :color="card.color"
            text-color="white"
            size="40px"
            class="status-card-icon"
          >
            <q-icon :name="getCardMainIcon(card.icon)" size="md" />
          </q-avatar>
        </div>

        <div class="status-card-body">
          <div class="status-card-value">{{ card.value }}</div>
          <div v-if="card.unit" class="status-card-unit">{{ card.unit }}</div>
          
          <q-linear-progress
            v-if="card.progress !== undefined"
            :value="card.progress / 100"
            :color="card.color"
            class="status-card-progress"
            size="6px"
            rounded
          />
          
          <div v-if="card.subtitle" class="status-card-subtitle">
            {{ card.subtitle }}
          </div>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import type { StatusCard } from '@/types/dashboard'

interface Props {
  cards: StatusCard[]
}

defineProps<Props>()

function getCardMainIcon(icon: string): string {
  // Extract the main icon name from FontAwesome classes
  const iconMap: Record<string, string> = {
    'fas fa-battery-three-quarters': 'battery_3_bar',
    'fas fa-cogs': 'settings',
    'fas fa-sun': 'wb_sunny',
    'fas fa-plug': 'electrical_services'
  }
  
  return iconMap[icon] || 'info'
}

function handleCardHover(event: Event) {
  const card = event.currentTarget as HTMLElement
  card.style.transform = 'translateY(-4px) scale(1.02)'
}

function handleCardLeave(event: Event) {
  const card = event.currentTarget as HTMLElement
  card.style.transform = ''
}
</script>

<style lang="scss" scoped>
.status-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.2s ease-in-out;
  position: relative;
  overflow: hidden;
}

.status-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--q-primary), var(--q-secondary), var(--q-positive));
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.status-card:hover::before {
  opacity: 1;
}

.status-card-content {
  padding: 1.5rem;
}

.status-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.status-card-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--q-dark);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-card-icon {
  border-radius: 0.5rem;
}

.status-card-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-card-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--q-dark);
  line-height: 1;
}

.status-card-unit {
  font-size: 0.875rem;
  color: var(--q-grey-6);
  font-weight: 500;
}

.status-card-progress {
  margin-top: 0.75rem;
}

.status-card-subtitle {
  font-size: 0.75rem;
  color: var(--q-grey-5);
  margin-top: 0.5rem;
}

@media (max-width: 768px) {
  .status-overview {
    grid-template-columns: 1fr;
  }
}
</style>
