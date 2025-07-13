<template>
  <q-card v-show="visible" class="controls-card">
    <q-card-section>
      <div class="controls-header">
        <div class="controls-title">
          <q-icon name="fas fa-filter" />
          Filtry a nastavení
        </div>
      </div>

      <q-form @submit="handleSubmit" class="controls-form">
        <div class="control-group">
          <q-select
            v-model="form.day"
            :options="dayOptions"
            label="Zobrazený den"
            outlined
            dense
            @update:model-value="handleDayChange"
            class="control-select"
          />
        </div>

        <div class="control-group">
          <q-select
            v-model="form.time"
            :options="timeOptions"
            label="Čas optimalizace"
            outlined
            dense
            class="control-select"
          />
        </div>

        <div class="control-group">
          <q-select
            v-model="form.view_type"
            :options="viewTypeOptions"
            label="Typ zobrazení"
            outlined
            dense
            class="control-select"
          />
        </div>

        <div class="control-actions">
          <q-btn
            type="submit"
            color="primary"
            icon="fas fa-search"
            label="Aplikovat"
            :loading="loading"
          />
          <q-btn
            color="primary"
            outline
            icon="fas fa-home"
            label="Aktuální data"
            @click="handleCurrentData"
          />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { storeToRefs } from "pinia";
import type { ControlsForm } from "@/types/dashboard";
import { useDashboardStore } from "@/stores/dashboard";

interface Props {
  visible: boolean;
  availableDays?: string[];
  availableTimes?: string[];
  availableTimesDisplay?: string[];
  currentDay?: string;
  currentTime?: string;
  currentViewType?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  "update-filters": [filters: Partial<ControlsForm>];
}>();

const dashboardStore = useDashboardStore();
const { loading } = storeToRefs(dashboardStore);

const form = ref<ControlsForm>({
  day: props.currentDay || "",
  time: props.currentTime || "",
  view_type: props.currentViewType || "tabs",
});

const dayOptions = computed(() =>
  (props.availableDays || []).map((day: string) => ({
    label: day,
    value: day,
  })),
);

const timeOptions = computed(() =>
  (props.availableTimes || []).map((time: string, index: number) => ({
    label: (props.availableTimesDisplay || [])[index] || time,
    value: time,
  })),
);

const viewTypeOptions = [
  { label: "Tabulky", value: "tabs" },
  { label: "Jeden graf", value: "single" },
];

// Watch for prop changes
watch(
  () => props.currentDay,
  (newDay: string | undefined) => {
    if (newDay) {
      form.value.day = newDay;
    }
  },
);

watch(
  () => props.currentTime,
  (newTime: string | undefined) => {
    form.value.time = newTime || "";
  },
);

watch(
  () => props.currentViewType,
  (newType: string | undefined) => {
    form.value.view_type = newType || "tabs";
  },
);

function handleSubmit() {
  emit("update-filters", form.value);
}

function handleDayChange() {
  // Auto-submit when day changes
  handleSubmit();
}

function handleCurrentData() {
  // Navigate to current data (no filters)
  emit("update-filters", {});
}
</script>

<style lang="scss" scoped>
.controls-card {
  margin-bottom: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.controls-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.controls-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--q-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.controls-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-actions {
  display: flex;
  gap: 0.5rem;
  justify-self: start;
  flex-wrap: wrap;
}

.control-select {
  min-width: 200px;
}

@media (max-width: 768px) {
  .controls-form {
    grid-template-columns: 1fr;
  }

  .control-actions {
    justify-self: stretch;
  }

  .control-actions .q-btn {
    flex: 1;
  }
}
</style>
