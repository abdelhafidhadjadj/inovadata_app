<script lang="ts">
  import { goto } from '$app/navigation';
  import type { PageData } from './$types';
  import Header from '$lib/components/Header.svelte';
  import ColumnList from '$lib/components/preprocessing/ColumnList.svelte';
  import ColumnStats from '$lib/components/preprocessing/ColumnStats.svelte';
  import MissingValuesConfig from '$lib/components/preprocessing/MissingValuesConfig.svelte';
  import RangeConfig from '$lib/components/preprocessing/RangeConfig.svelte';
  import ValueDistribution from '$lib/components/preprocessing/ValueDistribution.svelte';
  import OutlierActions from '$lib/components/preprocessing/OutlierActions.svelte';
  import MissingValuesActions from '$lib/components/preprocessing/MissingValuesActions.svelte';
  import NormalizationPanel from '$lib/components/preprocessing/transformations/NormalizationPanel.svelte';
  import EncodingPanel from '$lib/components/preprocessing/transformations/EncodingPanel.svelte';
  import VersionManager from '$lib/components/preprocessing/VersionManager.svelte';
  import BoxPlotChart from '$lib/components/preprocessing/BoxPlotChart.svelte';
  import HistogramChart from '$lib/components/preprocessing/HistogramChart.svelte';
  import ScatterPlotChart from '$lib/components/preprocessing/ScatterPlotChart.svelte';
  import OutliersTable from '$lib/components/preprocessing/OutliersTable.svelte';
  
  import {
    type ColumnAnalysis,
    initializeCustomRanges,
    initializeCustomMissingValues,
    getTotalOutliers,
    ensureRangeExists
  } from './preprocess-helpers';
  
  let { data }: { data: PageData } = $props();
  
  // Onglets
  let activeTab = $state<'missing' | 'outliers' | 'transform' | 'visualizations'>('missing');
  let selectedColumn = $state<ColumnAnalysis | null>(null);
  let isAnalyzing = $state(false);
  let fillLoading = $state(false);
  
  // Configuration
  let customMissingValues = $state(initializeCustomMissingValues(data.analysis));
  let customRanges = $state(initializeCustomRanges(data.analysis));
  let selectedReplacementMethod: Record<string, 'mean' | 'median' | 'mode' | 'min' | 'max'> = $state({});
  
  // Scatter plot
  let scatterColumnXIndex = $state(0);
  let scatterColumnYIndex = $state(1);
  
  // Transformations
  let transformTab = $state<'normalize' | 'encode'>('normalize');
  
  // Filtrer les colonnes numériques
  let numericalColumns = $derived(
    data.analysis.filter((col: ColumnAnalysis) => col.data_type === 'numerical')
  );
  
  // Colonnes scatter plot dérivées des index
  let scatterColumnX = $derived(numericalColumns[scatterColumnXIndex] || null);
  let scatterColumnY = $derived(numericalColumns[scatterColumnYIndex] || null);
  
  // Initialisation
  $effect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const selectedColumnName = params.get('column');
      
      if (selectedColumnName && !selectedColumn) {
        const column = data.analysis.find(c => c.name === selectedColumnName);
        if (column) selectColumn(column);
      }
    }
    
    data.analysis.forEach(col => {
      if (!selectedReplacementMethod[col.name]) {
        selectedReplacementMethod[col.name] = col.data_type === 'numerical' ? 'mean' : 'mode';
      }
    });
  });
  
  function selectColumn(column: ColumnAnalysis) {
    selectedColumn = column;
    if (column.data_type === 'numerical') {
      customRanges = ensureRangeExists(column.name, customRanges);
    }
    
    if (typeof window !== 'undefined') {
      const currentUrl = new URL(window.location.href);
      currentUrl.searchParams.set('column', column.name);
      window.history.replaceState({}, '', currentUrl.toString());
    }
  }
  
  function applyRangeConfig() {
    if (!selectedColumn) return;
    isAnalyzing = true;
    
    const currentUrl = new URL(window.location.href);
    const params = currentUrl.searchParams;
    const range = customRanges[selectedColumn.name];
    
    params.set('column', selectedColumn.name);
    
    if (range?.min !== undefined && range?.min !== null && !isNaN(range.min)) {
      params.set(`${selectedColumn.name}_min`, range.min.toString());
    } else {
      params.delete(`${selectedColumn.name}_min`);
    }
    
    if (range?.max !== undefined && range?.max !== null && !isNaN(range.max)) {
      params.set(`${selectedColumn.name}_max`, range.max.toString());
    } else {
      params.delete(`${selectedColumn.name}_max`);
    }
    
    if (customMissingValues[selectedColumn.name]?.trim()) {
      params.set(`${selectedColumn.name}_missing`, customMissingValues[selectedColumn.name]);
    } else {
      params.delete(`${selectedColumn.name}_missing`);
    }
    
    window.location.href = `${currentUrl.pathname}?${params.toString()}`;
  }
  
  async function replaceOutliers() {
    if (!selectedColumn) return;
    
    const hasRangeOutliers = selectedColumn.outliers?.range?.outliers_count > 0;
    const hasIQROutliers = selectedColumn.outliers?.iqr?.outliers_count > 0;
    
    if (!hasRangeOutliers && !hasIQROutliers) {
      alert('No outliers detected for this column');
      return;
    }
    
    const method = hasRangeOutliers ? 'range' : 'iqr';
    const count = hasRangeOutliers 
      ? selectedColumn.outliers.range.outliers_count 
      : selectedColumn.outliers.iqr.outliers_count;
    const strategy = selectedReplacementMethod[selectedColumn.name] || 'mean';
    
    if (!confirm(`Replace ${count} outliers in ${selectedColumn.name} with ${strategy.toUpperCase()}?`)) return;
    
    fillLoading = true;
    
    const form = new FormData();
    form.append('column_name', selectedColumn.name);
    form.append('action', 'replace_outliers');
    form.append('method', method);
    form.append('replacement_strategy', strategy);
    
    if (method === 'range' && selectedColumn.configured_range) {
      if (selectedColumn.configured_range.min !== null && selectedColumn.configured_range.min !== undefined) {
        form.append('min_value', selectedColumn.configured_range.min.toString());
      }
      if (selectedColumn.configured_range.max !== null && selectedColumn.configured_range.max !== undefined) {
        form.append('max_value', selectedColumn.configured_range.max.toString());
      }
    }
    
    try {
      const response = await fetch('?/fillMissing', { method: 'POST', body: form });
      const result = await response.json();
      
      if (result.type === 'success') {
        // ✅ CORRECTION
        await new Promise(resolve => setTimeout(resolve, 500));
        window.location.reload();
      } else {
        alert('Error: ' + (result.data?.error || 'Failed to replace outliers'));
        fillLoading = false;
      }
    } catch (error) {
      console.error('Replace outliers error:', error);
      alert('Failed to replace outliers');
      fillLoading = false;
    }
  }
  
  async function removeOutliers() {
    if (!selectedColumn) return;
    
    const count = selectedColumn.outliers?.range?.outliers_count 
      || selectedColumn.outliers?.iqr?.outliers_count 
      || 0;
      
    if (!confirm(`Remove ${count} rows with outliers in ${selectedColumn.name}?`)) return;
    
    fillLoading = true;
    
    const form = new FormData();
    form.append('column_name', selectedColumn.name);
    form.append('action', 'remove_outliers');
    form.append('method', selectedColumn.outliers?.range ? 'range' : 'iqr');
    
    if (selectedColumn.configured_range) {
      if (selectedColumn.configured_range.min !== null) {
        form.append('min_value', selectedColumn.configured_range.min.toString());
      }
      if (selectedColumn.configured_range.max !== null) {
        form.append('max_value', selectedColumn.configured_range.max.toString());
      }
    }
    
    try {
      const response = await fetch('?/fillMissing', { method: 'POST', body: form });
      const result = await response.json();
      
      if (result.type === 'success') {
        // ✅ CORRECTION
        await new Promise(resolve => setTimeout(resolve, 500));
        window.location.reload();
      } else {
        alert('Error: ' + (result.data?.error || 'Failed'));
        fillLoading = false;
      }
    } catch (error) {
      alert('Failed');
      fillLoading = false;
    }
  }
  
  async function fillMissingValues() {
    if (!selectedColumn || selectedColumn.total_missing_count === 0) return;
    
    const strategy = selectedReplacementMethod[selectedColumn.name] || 'mean';
    const action = `fill_${strategy}`;
    
    fillLoading = true;
    const form = new FormData();
    form.append('column_name', selectedColumn.name);
    form.append('action', action);
    
    if (customMissingValues[selectedColumn.name]) {
      form.append('custom_missing', customMissingValues[selectedColumn.name]);
    }
    
    try {
      const response = await fetch('?/fillMissing', { method: 'POST', body: form });
      const result = await response.json();
      
      if (result.type === 'success') {
        // ✅ CORRECTION
        await new Promise(resolve => setTimeout(resolve, 500));
        window.location.reload();
      } else {
        alert('Error: ' + (result.data?.error || 'Failed'));
        fillLoading = false;
      }
    } catch (error) {
      alert('Failed');
      fillLoading = false;
    }
  }
  
  async function forwardFill() {
    if (!selectedColumn) return;
    
    fillLoading = true;
    const form = new FormData();
    form.append('column_name', selectedColumn.name);
    form.append('action', 'fill_forward');
    
    if (customMissingValues[selectedColumn.name]) {
      form.append('custom_missing', customMissingValues[selectedColumn.name]);
    }
    
    try {
      const response = await fetch('?/fillMissing', { method: 'POST', body: form });
      const result = await response.json();
      
      if (result.type === 'success') {
        // ✅ CORRECTION
        await new Promise(resolve => setTimeout(resolve, 500));
        window.location.reload();
      } else {
        alert('Error');
        fillLoading = false;
      }
    } catch (error) {
      alert('Failed');
      fillLoading = false;
    }
  }
  
  async function removeRowsWithMissing() {
    if (!selectedColumn) return;
    
    if (!confirm(`Remove all rows with missing values in ${selectedColumn.name}?`)) return;
    
    fillLoading = true;
    const form = new FormData();
    form.append('column_name', selectedColumn.name);
    form.append('action', 'remove_rows');
    
    if (customMissingValues[selectedColumn.name]) {
      form.append('custom_missing', customMissingValues[selectedColumn.name]);
    }
    
    try {
      const response = await fetch('?/fillMissing', { method: 'POST', body: form });
      const result = await response.json();
      
      if (result.type === 'success') {
        // ✅ CORRECTION
        await new Promise(resolve => setTimeout(resolve, 500));
        window.location.reload();
      } else {
        alert('Error');
        fillLoading = false;
      }
    } catch (error) {
      alert('Failed');
      fillLoading = false;
    }
  }
  
  function handleTransformComplete() {
    window.location.reload();
  }
  
  function handleVersionChange() {
    window.location.reload();
  }
</script>



<svelte:head>
  <title>Preprocess: {data.dataset.name} - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <Header user={data.user} />
  
  <main class="container mx-auto px-4 py-8">
    <!-- Breadcrumb -->
    <nav class="mb-6 flex items-center text-sm text-gray-600">
      <a href="/dashboard" class="hover:text-gray-900">Dashboard</a>
      <svg class="w-4 h-4 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <a href="/dashboard/projects/{data.project.id}" class="hover:text-gray-900">{data.project.name}</a>
      <svg class="w-4 h-4 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}" class="hover:text-gray-900">{data.dataset.name}</a>
      <svg class="w-4 h-4 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <span class="text-gray-900 font-medium">Preprocess</span>
    </nav>

    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Data Preprocessing</h1>
        <p class="text-gray-600">Clean and prepare your data for analysis</p>
      </div>
      <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}" class="btn-secondary">
        Back to Dataset
      </a>
    </div>
    <VersionManager 
    datasetId={data.dataset.id}
    onVersionChange={() => window.location.reload()}
    />

    <!-- Tabs -->
    <div class="mb-6 border-b border-gray-200">
      <nav class="flex space-x-8">
        <button
          type="button"
          onclick={() => activeTab = 'missing'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'missing' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Missing Values
          {#if data.analysis.some(c => c.total_missing_count > 0)}
            <span class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
              {data.analysis.filter(c => c.total_missing_count > 0).length}
            </span>
          {/if}
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'outliers'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'outliers' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Outliers Detection
          {#if data.analysis.some(c => getTotalOutliers(c) > 0)}
            <span class="ml-2 px-2 py-0.5 text-xs bg-orange-100 text-orange-800 rounded-full">
              {data.analysis.filter(c => getTotalOutliers(c) > 0).length}
            </span>
          {/if}
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'visualizations'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'visualizations' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Visualizations
          {#if numericalColumns.length > 0}
            <span class="ml-2 px-2 py-0.5 text-xs bg-purple-100 text-purple-800 rounded-full">
              {numericalColumns.length}
            </span>
          {/if}
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'transform'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'transform' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Transformations
        </button>
      </nav>
    </div>

    <!-- Tab Content -->
    {#if activeTab === 'missing' || activeTab === 'outliers'}
      <div class="grid md:grid-cols-3 gap-6">
        <ColumnList 
          columns={data.analysis} 
          {selectedColumn} 
          onSelect={selectColumn} 
        />

        <div class="md:col-span-2">
          {#if selectedColumn}
            <div class="card space-y-6">
              <div>
                <h3 class="text-lg font-bold mb-2">{selectedColumn.name}</h3>
                <div class="flex items-center gap-3 text-sm">
                  <span class="px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                    {selectedColumn.data_type}
                  </span>
                  <span class="text-gray-600">{selectedColumn.total_count} values</span>
                  <span class="text-gray-600">{selectedColumn.unique_count} unique</span>
                </div>
              </div>
              
               {#if activeTab === 'missing'}
                 <ColumnStats column={selectedColumn} />
                       
                 <!-- Configuration des valeurs manquantes personnalisées -->
                 <MissingValuesConfig 
                   column={selectedColumn}
                   value={customMissingValues[selectedColumn.name] || ''}
                   onUpdate={(val) => customMissingValues[selectedColumn.name] = val}
                 />
                       
                 <!-- Actions de traitement (affiche un message si aucune missing value) -->
                 <MissingValuesActions 
                   column={selectedColumn}
                   selectedMethod={selectedReplacementMethod[selectedColumn.name] || 'mean'}
                   isLoading={fillLoading}
                   onMethodChange={(method) => selectedReplacementMethod[selectedColumn.name] = method}
                   onFill={fillMissingValues}
                   onForwardFill={forwardFill}
                   onRemove={removeRowsWithMissing}
                 />
                       
               {/if}

              {#if activeTab === 'outliers' && selectedColumn.data_type === 'numerical'}
                {#if selectedColumn.statistics}
                  <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-900 mb-3">Statistics</h4>
                    <div class="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div class="text-gray-500">Mean</div>
                        <div class="font-semibold">{selectedColumn.statistics.mean?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">Median</div>
                        <div class="font-semibold">{selectedColumn.statistics.median?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">Std Dev</div>
                        <div class="font-semibold">{selectedColumn.statistics.std?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">Range</div>
                        <div class="font-semibold">[{selectedColumn.statistics.min?.toFixed(2)}, {selectedColumn.statistics.max?.toFixed(2)}]</div>
                      </div>
                    </div>
                  </div>
                {/if}

                <RangeConfig 
                  column={selectedColumn}
                  min={customRanges[selectedColumn.name]?.min}
                  max={customRanges[selectedColumn.name]?.max}
                  onMinChange={(val) => customRanges[selectedColumn.name] = { ...customRanges[selectedColumn.name], min: val }}
                  onMaxChange={(val) => customRanges[selectedColumn.name] = { ...customRanges[selectedColumn.name], max: val }}
                  onApply={applyRangeConfig}
                  {isAnalyzing}
                />
                
                {#if getTotalOutliers(selectedColumn) > 0}
                  <OutlierActions 
                    column={selectedColumn}
                    selectedMethod={selectedReplacementMethod[selectedColumn.name] || 'mean'}
                    isLoading={fillLoading}
                    onMethodChange={(method) => selectedReplacementMethod[selectedColumn.name] = method}
                    onReplace={replaceOutliers}
                    onRemove={removeOutliers}
                  />
                {/if}
              {/if}
              
              <ValueDistribution column={selectedColumn} />
            </div>
          {:else}
            <div class="card text-center py-12">
              <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
              <p class="text-gray-500">Select a column to configure preprocessing</p>
            </div>
          {/if}
        </div>
      </div>
    {:else if activeTab === 'visualizations'}
  <!-- Visualizations Tab -->
  <div class="space-y-6">
    <OutliersTable columns={data.analysis} />

    {#if numericalColumns.length > 0}
      <!-- Box Plots -->
      <div>
        <h2 class="text-xl font-bold text-gray-900 mb-4">Box Plots</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#each numericalColumns as column}
            <BoxPlotChart column={column} data={data.previewData} />
          {/each}
        </div>
      </div>

      <!-- Histograms -->
      <div>
        <h2 class="text-xl font-bold text-gray-900 mb-4">Distributions</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#each numericalColumns as column}
            <HistogramChart {column} />
          {/each}
        </div>
      </div>

      <!-- Scatter Plot -->
      {#if numericalColumns.length >= 2}
        <div>
          <h2 class="text-xl font-bold text-gray-900 mb-4">Multivariate Outlier Detection</h2>
          
          <div class="card mb-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">X-Axis</label>
                <select 
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                  bind:value={scatterColumnXIndex}
                >
                  {#each numericalColumns as col, index}
                    <option value={index}>{col.name}</option>
                  {/each}
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Y-Axis</label>
                <select 
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                  bind:value={scatterColumnYIndex}
                >
                  {#each numericalColumns as col, index}
                    <option value={index}>{col.name}</option>
                  {/each}
                </select>
              </div>
            </div>
          </div>

          {#if scatterColumnX && scatterColumnY && data.previewData}
            <ScatterPlotChart 
              columnX={scatterColumnX} 
              columnY={scatterColumnY}
              data={data.previewData}
            />
          {/if}
        </div>
      {/if}
    {:else}
      <div class="card text-center py-12">
        <p class="text-gray-500">No numerical columns available for visualization</p>
      </div>
    {/if}
  </div>
    {:else if activeTab === 'transform'}
<div class="space-y-6">
    <!-- Sous-onglets -->
    <div class="border-b border-gray-200">
      <nav class="flex space-x-8">
        <button
          type="button"
          onclick={() => transformTab = 'normalize'}
          class="pb-3 px-1 border-b-2 font-medium text-sm {transformTab === 'normalize' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Normalization
        </button>
        <button
          type="button"
          onclick={() => transformTab = 'encode'}
          class="pb-3 px-1 border-b-2 font-medium text-sm {transformTab === 'encode' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Encoding
        </button>
      </nav>
    </div>
    
    <!-- Panel actif -->
    {#if transformTab === 'normalize'}
          <NormalizationPanel 
            columns={data.analysis}
            dataset={data.dataset}
            onTransform={handleTransformComplete}
          />
        {:else if transformTab === 'encode'}
          <EncodingPanel 
            columns={data.analysis}
            dataset={data.dataset}
            onTransform={handleTransformComplete}
          />
        {/if}
      </div>
    {/if}
  </main>
</div>