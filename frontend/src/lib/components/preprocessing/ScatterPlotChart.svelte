<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  let { columnX, columnY, data }: { columnX: any; columnY: any; data: any[] } = $props();
  let chartDiv: HTMLDivElement;
  let plotlyLoaded = $state(false);
  let plotlyError = $state('');
  
  function isOutlier(value: number, col: any) {
    if (!col?.outliers?.iqr || isNaN(value)) return false;
    const { lower_bound, upper_bound } = col.outliers.iqr;
    return value < lower_bound || value > upper_bound;
  }
  
  // Charger Plotly au montage
  onMount(async () => {
    if (!browser) return;
    
    try {
      const Plotly = (await import('plotly.js-dist-min')).default;
      (window as any).Plotly = Plotly;
      plotlyLoaded = true;
      console.log('✅ Plotly loaded successfully');
    } catch (err) {
      console.error('❌ Failed to load Plotly:', err);
      plotlyError = 'Failed to load visualization library';
    }
  });
  
  // Créer/Mettre à jour le graphique quand les dépendances changent
  $effect(() => {
    if (!plotlyLoaded || !chartDiv || !data || !columnX || !columnY) {
      console.log('Waiting...', { plotlyLoaded, chartDiv: !!chartDiv, data: !!data, columnX: !!columnX, columnY: !!columnY });
      return;
    }
    
    const Plotly = (window as any).Plotly;
    
    console.log('=== 🎨 CREATING SCATTER PLOT ===');
    console.log('X Column:', columnX.name);
    console.log('Y Column:', columnY.name);
    console.log('Data rows:', data.length);
    
    // Préparer les données
    const points = data
      .map((row, idx) => {
        const xRaw = row[columnX.name];
        const yRaw = row[columnY.name];
        
        // Convertir en nombre
        let x = typeof xRaw === 'string' ? parseFloat(xRaw) : Number(xRaw);
        let y = typeof yRaw === 'string' ? parseFloat(yRaw) : Number(yRaw);
        
        // Vérifier validité
        if (xRaw === null || xRaw === undefined || xRaw === '' || xRaw === '?') x = NaN;
        if (yRaw === null || yRaw === undefined || yRaw === '' || yRaw === '?') y = NaN;
        
        return {
          x,
          y,
          idx,
          outlier: isOutlier(x, columnX) || isOutlier(y, columnY)
        };
      })
      .filter(p => !isNaN(p.x) && !isNaN(p.y) && isFinite(p.x) && isFinite(p.y));
    
    console.log('Valid points:', points.length);
    
    if (points.length === 0) {
      console.error('❌ No valid points to plot');
      plotlyError = 'No valid data to display';
      return;
    }
    
    const normal = points.filter(p => !p.outlier);
    const outliers = points.filter(p => p.outlier);
    
    console.log('Normal:', normal.length, 'Outliers:', outliers.length);
    
    // Créer les traces
    const traces = [];
    
    // Trace pour points normaux
    if (normal.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        name: 'Normal',
        x: normal.map(p => p.x),
        y: normal.map(p => p.y),
        marker: {
          color: '#3b82f6',
          size: 6
        },
        hovertemplate: `<b>Normal Point</b><br>${columnX.name}: %{x:.2f}<br>${columnY.name}: %{y:.2f}<extra></extra>`
      });
    }
    
    // Trace pour outliers
    if (outliers.length > 0) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        name: 'Outliers',
        x: outliers.map(p => p.x),
        y: outliers.map(p => p.y),
        marker: {
          color: '#f97316',
          size: 8,
          symbol: 'diamond'
        },
        hovertemplate: `<b>⚠️ Outlier</b><br>${columnX.name}: %{x:.2f}<br>${columnY.name}: %{y:.2f}<extra></extra>`
      });
    }
    
    // Layout
    const layout = {
      xaxis: { 
        title: columnX.name,
        gridcolor: '#e5e7eb'
      },
      yaxis: { 
        title: columnY.name,
        gridcolor: '#e5e7eb'
      },
      height: 450,
      margin: { l: 60, r: 30, t: 20, b: 60 },
      plot_bgcolor: '#f9fafb',
      paper_bgcolor: 'white',
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1,
        xanchor: 'right',
        y: 1
      }
    };
    
    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };
    
    try {
      console.log('📊 Calling Plotly.react...');
      Plotly.react(chartDiv, traces, layout, config);
      console.log('✅ Plot created successfully');
      plotlyError = '';
    } catch (err) {
      console.error('❌ Plotly.react error:', err);
      plotlyError = `Error: ${err}`;
    }
  });
  
  // Calculer les compteurs
  let normalCount = $derived.by(() => {
    if (!data) return 0;
    return data.filter(row => {
      const x = parseFloat(row[columnX.name]);
      const y = parseFloat(row[columnY.name]);
      return !isNaN(x) && !isNaN(y) && !isOutlier(x, columnX) && !isOutlier(y, columnY);
    }).length;
  });
  
  let outlierCount = $derived.by(() => {
    if (!data) return 0;
    return data.filter(row => {
      const x = parseFloat(row[columnX.name]);
      const y = parseFloat(row[columnY.name]);
      return !isNaN(x) && !isNaN(y) && (isOutlier(x, columnX) || isOutlier(y, columnY));
    }).length;
  });
</script>

<div class="bg-white p-4 rounded-lg border border-gray-200">
  <h3 class="text-lg font-semibold mb-4">
    {columnX.name} vs {columnY.name} - Scatter Plot
  </h3>
  
  {#if plotlyError}
    <div class="bg-red-50 border border-red-200 rounded p-4 mb-4 text-red-800">
      {plotlyError}
    </div>
  {/if}
  
  {#if !plotlyLoaded}
    <div class="bg-blue-50 border border-blue-200 rounded p-4 mb-4 text-blue-800">
      Loading visualization library...
    </div>
  {/if}
  
  <div bind:this={chartDiv} class="min-h-[450px]"></div>
  
  <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
    <div class="p-3 bg-blue-50 rounded">
      <div class="font-semibold text-blue-800">Normal Points</div>
      <div class="text-2xl text-blue-600">{normalCount}</div>
    </div>
    <div class="p-3 bg-orange-50 rounded">
      <div class="font-semibold text-orange-800">Outlier Points</div>
      <div class="text-2xl text-orange-600">{outlierCount}</div>
    </div>
  </div>
</div>