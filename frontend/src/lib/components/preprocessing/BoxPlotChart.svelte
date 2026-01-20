<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  let { column, data }: { column: any; data?: any[] } = $props();
  let chartDiv: HTMLDivElement;
  
  onMount(async () => {
    if (!browser) return;
    
    const Plotly = (await import('plotly.js-dist-min')).default;
    
    let values: number[] = [];
    
    if (data && data.length > 0) {
      values = data
        .map(row => {
          const rawValue = row[column.name];
          if (rawValue === null || rawValue === undefined || rawValue === '' || rawValue === '?') {
            return NaN;
          }
          return typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue;
        })
        .filter(v => !isNaN(v) && isFinite(v));
    }
    
    if (values.length === 0) return;
    
    const trace = {
      type: 'box',
      y: values,
      name: column.name,
      boxpoints: 'outliers',
      jitter: 0, // ✅ Pas de jitter = points alignés
      pointpos: 0, // ✅ Position 0 = centrés sur la boîte
      marker: {
        color: '#f97316',
        size: 6,
        line: {
          color: '#c2410c',
          width: 1
        }
      },
      line: { 
        color: '#1e40af',
        width: 2
      },
      fillcolor: '#93c5fd'
    };
    
    const layout: any = {
      yaxis: { 
        title: 'Value',
        zeroline: true,
        gridcolor: '#e5e7eb'
      },
      xaxis: {
        showticklabels: false
      },
      showlegend: false,
      height: 350,
      margin: { l: 60, r: 30, t: 20, b: 50 },
      plot_bgcolor: '#f9fafb',
      paper_bgcolor: 'white'
    };
    
    if (column.outliers?.iqr) {
      layout.shapes = [
        {
          type: 'line',
          x0: -0.5,
          x1: 0.5,
          y0: column.outliers.iqr.lower_bound,
          y1: column.outliers.iqr.lower_bound,
          line: { color: 'orange', width: 2, dash: 'dash' }
        },
        {
          type: 'line',
          x0: -0.5,
          x1: 0.5,
          y0: column.outliers.iqr.upper_bound,
          y1: column.outliers.iqr.upper_bound,
          line: { color: 'orange', width: 2, dash: 'dash' }
        }
      ];
    }
    
    Plotly.newPlot(chartDiv, [trace], layout, { 
      responsive: true,
      displayModeBar: true
    });
  });
</script>

<div class="bg-white p-4 rounded-lg border border-gray-200">
  <h3 class="text-lg font-semibold mb-4">{column.name} - Box Plot</h3>
  
  <div bind:this={chartDiv} class="min-h-[350px]"></div>
  
  {#if column.statistics}
    <div class="mt-4 grid grid-cols-5 gap-2 text-sm">
      <div class="text-center">
        <div class="font-semibold">Min</div>
        <div>{column.statistics.min?.toFixed(2)}</div>
      </div>
      <div class="text-center">
        <div class="font-semibold">Q1</div>
        <div>{column.statistics.q25?.toFixed(2)}</div>
      </div>
      <div class="text-center">
        <div class="font-semibold text-red-600">Median</div>
        <div>{column.statistics.median?.toFixed(2)}</div>
      </div>
      <div class="text-center">
        <div class="font-semibold">Q3</div>
        <div>{column.statistics.q75?.toFixed(2)}</div>
      </div>
      <div class="text-center">
        <div class="font-semibold">Max</div>
        <div>{column.statistics.max?.toFixed(2)}</div>
      </div>
    </div>
    
    {#if column.outliers?.iqr}
      <div class="mt-4 p-3 bg-orange-50 border border-orange-200 rounded">
        <div class="font-semibold text-orange-800">IQR Outliers Detected</div>
        <div class="text-sm text-orange-700 mt-1">
          {column.outliers.iqr.outliers_count} outliers outside [{column.outliers.iqr.lower_bound?.toFixed(2)}, {column.outliers.iqr.upper_bound?.toFixed(2)}]
        </div>
      </div>
    {/if}
  {/if}
</div>