<template>
  <q-card class="action-section">
    <q-card-section class="action-content">
      <div class="generated-info">
        <q-icon name="fas fa-clock" size="sm" />
        Vygenerováno: {{ generatedAt }}
      </div>
      
      <div class="action-buttons">
        <q-btn
          color="info"
          icon="fas fa-download"
          label="Stáhnout CSV"
          @click="handleDownloadCSV"
          :loading="downloadLoading"
          class="action-btn"
        />
        <q-btn
          color="positive"
          icon="fas fa-sync-alt"
          label="Znovu vygenerovat optimalizaci"
          @click="handleRegenerate"
          :loading="loading"
          class="action-btn"
        />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useQuasar } from 'quasar'

interface Props {
  generatedAt: string
}

defineProps<Props>()

const $q = useQuasar()
const dashboardStore = useDashboardStore()

const downloadLoading = ref(false)
const { loading } = dashboardStore

async function handleDownloadCSV() {
  downloadLoading.value = true
  try {
    await dashboardStore.downloadCSV()
    $q.notify({
      type: 'positive',
      message: 'CSV soubor byl úspěšně stažen',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Chyba při stahování CSV souboru',
      position: 'top'
    })
  } finally {
    downloadLoading.value = false
  }
}

async function handleRegenerate() {
  try {
    await dashboardStore.regenerateOptimization()
    $q.notify({
      type: 'positive',
      message: 'Optimalizace byla úspěšně aktualizována',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Chyba při aktualizaci optimalizace',
      position: 'top'
    })
  }
}
</script>

<style lang="scss" scoped>
.action-section {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.5rem 2rem;
}

.generated-info {
  font-size: 0.875rem;
  color: var(--q-grey-6);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.action-btn {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease-in-out;
}

.action-btn:hover {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .action-content {
    flex-direction: column;
    text-align: center;
  }

  .action-buttons {
    justify-content: center;
    width: 100%;
    
    .action-btn {
      flex: 1;
    }
  }
}
</style>
