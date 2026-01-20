<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  let { column }: { column: any } = $props();
  let chartDiv: HTMLDivElement;
  
  function isValueOutlier(value: number, col: any) {
    if (!col.outliers?.iqr || isNaN(value)) return false;
    const { lower_bound, upper_bound } = col.outliers.iqr;
    return value < lower_bound || value > upper_bound;
  }
  
  onMount(async () => {
    if (!browser || !column.value_frequencies) return;
    
    const Plotly = (await import('plotly.js-dist-min')).default;
    
    const data = Object.entries(column.value_frequencies)
      .map(([value, count]) => ({
        value: parseFloat(value) || value,
        count: count as number,
        isOutlier: isValueOutlier(parseFloat(value), column)
      }))
      .sort((a, b) => {
        if (typeof a.value === 'number' && typeof b.value === 'number') {
          return a.value - b.value;
        }
        return 0;
      });
    
    const trace = {
      type: 'bar',
      x: data.map(d => d.value),
      y: data.map(d => d.count),
      marker: {
        color: data.map(d => d.isOutlier ? '#f97316' : '#3b82f6')
      },
      text: data.map(d => d.isOutlier ? '⚠️' : ''),
      textposition: 'outside',
      hovertemplate: '<b>Value:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
    };
    
    const layout: any = {
      title: `${column.name} - Distribution`,
      xaxis: { title: 'Value' },
      yaxis: { title: 'Frequency' },
      showlegend: false,
      height: 350,
      margin: { l: 50, r: 30, t: 50, b: 50 }
    };
    
    if (column.outliers?.iqr) {
      layout.shapes = [
        {
          type: 'line',
          x0: column.outliers.iqr.lower_bound,
          x1: column.outliers.iqr.lower_bound,
          y0: 0,
          y1: 1,
          yref: 'paper',
          line: { color: 'orange', width: 2, dash: 'dash' }
        },
        {
          type: 'line',
          x0: column.outliers.iqr.upper_bound,
          x1: column.outliers.iqr.upper_bound,
          y0: 0,
          y1: 1,
          yref: 'paper',
          line: { color: 'orange', width: 2, dash: 'dash' }
        }
      ];
    }
    
    Plotly.newPlot(chartDiv, [trace], layout, { responsive: true });
  });
</script>

<div class="bg-white p-4 rounded-lg border border-gray-200">
  <!-- AJOUTÉ: Titre externe -->
  <h3 class="text-lg font-semibold mb-4">{column.name} - Distribution</h3>
  
  <div bind:this={chartDiv} class="min-h-[350px]"></div>
  
  <div class="mt-4 flex items-center gap-4 text-sm">
    <div class="flex items-center gap-2">
      <div class="w-4 h-4 bg-blue-500 rounded"></div>
      <span>Normal values</span>
    </div>
    <div class="flex items-center gap-2">
      <div class="w-4 h-4 bg-orange-500 rounded"></div>
      <span>Outliers</span>
    </div>
  </div>
</div>