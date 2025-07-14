<template>
  <div ref="chartContainer" class="plotly-chart"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import Plotly from 'plotly.js-dist-min';

interface Props {
  data: any[];
  layout?: any;
  config?: any;
}

const props = withDefaults(defineProps<Props>(), {
  layout: () => ({}),
  config: () => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
    responsive: true
  })
});

const chartContainer = ref<HTMLElement>();

const renderChart = async () => {
  if (!chartContainer.value || !props.data.length) return;

  try {
    await Plotly.newPlot(
      chartContainer.value,
      props.data,
      {
        ...props.layout,
        autosize: true,
        margin: { l: 50, r: 50, t: 80, b: 50 }
      },
      props.config
    );
  } catch (error) {
    console.error('Error rendering Plotly chart:', error);
  }
};

// Watch for data changes and re-render
watch(() => props.data, renderChart, { deep: true });
watch(() => props.layout, renderChart, { deep: true });

onMounted(() => {
  nextTick(renderChart);
});
</script>

<style scoped>
.plotly-chart {
  width: 100%;
  height: 400px;
}
</style>
