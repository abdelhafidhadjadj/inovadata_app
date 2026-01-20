<script lang="ts">
  let { columns, dataset, onTransform }: { 
    columns: any[]; 
    dataset: any;
    onTransform: () => void;
  } = $props();
  
  let selectedColumns = $state<string[]>([]);
  let method = $state<'zscore' | 'minmax' | 'robust'>('zscore');
  let featureRangeMin = $state(0);
  let featureRangeMax = $state(1);
  let isLoading = $state(false);
  let previewData = $state<any>(null);
  let showPreview = $state(false);
  let createNewVersion = $state(true);
  
  let numericalColumns = $derived(
    columns.filter(col => col.data_type === 'numerical')
  );

  function toggleColumn(columnName: string) {
    if (selectedColumns.includes(columnName)) {
      selectedColumns = selectedColumns.filter(c => c !== columnName);
    } else {
      selectedColumns = [...selectedColumns, columnName];
    }
  }
  
  async function handlePreview() {
    console.log('=== 🎯 PREVIEW NORMALIZE ===');
    
    if (selectedColumns.length === 0) {
      alert('Please select at least one column');
      return;
    }
    
    isLoading = true;
    showPreview = false;
    
    try {
      const formData = new FormData();
      formData.append('file_path', dataset.file_path);
      formData.append('file_format', dataset.file_format);
      formData.append('columns', JSON.stringify(selectedColumns));
      formData.append('method', method);
      
      console.log('📤 Sending preview request...');
      
      const response = await fetch('http://localhost:8001/transform-preview-normalize', {
        method: 'POST',
        body: formData
      });
      
      console.log('📥 Response:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error:', errorText);
        throw new Error(`Preview failed: ${response.status}`);
      }
      
      previewData = await response.json();
      console.log('✅ Preview data:', previewData);
      showPreview = true;
    } catch (error) {
      console.error('❌ Preview error:', error);
      alert('Failed to generate preview: ' + error);
    } finally {
      isLoading = false;
    }
  }
  
  async function handleApply() {
    if (selectedColumns.length === 0) {
      alert('Please select at least one column');
      return;
    }
    
    const confirmMessage = createNewVersion 
      ? `Create new version with ${method} normalization on ${selectedColumns.length} column(s)?`
      : `Overwrite dataset with ${method} normalization on ${selectedColumns.length} column(s)?`;
    
    if (!confirm(confirmMessage)) {
      return;
    }
    
    isLoading = true;
    
    try {
      const formData = new FormData();
      formData.append('file_path', dataset.file_path);
      formData.append('file_format', dataset.file_format);
      formData.append('columns', JSON.stringify(selectedColumns));
      formData.append('method', method);
      formData.append('dataset_id', dataset.id.toString());
      formData.append('create_new_version', createNewVersion.toString());
      formData.append('feature_range_min', featureRangeMin.toString());
      formData.append('feature_range_max', featureRangeMax.toString());
      
      console.log('📤 Applying normalization...');
      
      const response = await fetch('http://localhost:8001/transform-normalize', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Normalization failed: ${errorText}`);
      }
      
      const result = await response.json();
      console.log('✅ Normalization result:', result);
      
      // ✅ CORRECTION : Ne pas recharger la page, juste afficher un message
      alert(result.message);
      
      // ✅ Appeler onTransform pour notifier le parent
      onTransform();
      
      // ✅ Reset les sélections
      selectedColumns = [];
      showPreview = false;
      previewData = null;
      
    } catch (error) {
      console.error('❌ Normalization error:', error);
      alert('Failed to apply normalization: ' + error);
    } finally {
      isLoading = false;
    }
  }
</script>

<!-- Le reste du template reste identique -->
<div class="card space-y-6">
  <div>
    <h3 class="text-lg font-semibold mb-2">Normalization</h3>
    <p class="text-sm text-gray-600">Scale numerical features to a standard range</p>
  </div>
  
  <!-- Method Selection -->
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Method</label>
    <div class="grid grid-cols-3 gap-3">
      <button
        type="button"
        onclick={() => method = 'zscore'}
        class="px-4 py-2 rounded border transition-colors {method === 'zscore' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
      >
        Z-Score
      </button>
      <button
        type="button"
        onclick={() => method = 'minmax'}
        class="px-4 py-2 rounded border transition-colors {method === 'minmax' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
      >
        Min-Max
      </button>
      <button
        type="button"
        onclick={() => method = 'robust'}
        class="px-4 py-2 rounded border transition-colors {method === 'robust' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
      >
        Robust
      </button>
    </div>
    
    <div class="mt-2 p-3 bg-blue-50 rounded text-sm text-blue-800">
      {#if method === 'zscore'}
        <strong>Z-Score:</strong> Standardizes features to mean=0, std=1. Best for normally distributed data.
      {:else if method === 'minmax'}
        <strong>Min-Max:</strong> Scales features to a specific range (default 0-1). Preserves original distribution shape.
      {:else if method === 'robust'}
        <strong>Robust:</strong> Uses median and IQR. Resistant to outliers.
      {/if}
    </div>
  </div>
  
  {#if method === 'minmax'}
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-2">Target Range</label>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Min</label>
          <input
            type="number"
            step="0.1"
            bind:value={featureRangeMin}
            class="w-full px-3 py-2 border border-gray-300 rounded"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">Max</label>
          <input
            type="number"
            step="0.1"
            bind:value={featureRangeMax}
            class="w-full px-3 py-2 border border-gray-300 rounded"
          />
        </div>
      </div>
    </div>
  {/if}
  
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">
      Select Numerical Columns ({selectedColumns.length} selected)
    </label>
    <div class="border border-gray-200 rounded max-h-64 overflow-y-auto">
      {#each numericalColumns as column}
        <label class="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0">
          <input
            type="checkbox"
            checked={selectedColumns.includes(column.name)}
            onchange={() => toggleColumn(column.name)}
            class="mr-3"
          />
          <div class="flex-1">
            <div class="font-medium">{column.name}</div>
            <div class="text-xs text-gray-500">
              Range: [{column.statistics?.min?.toFixed(2)}, {column.statistics?.max?.toFixed(2)}]
            </div>
          </div>
        </label>
      {/each}
    </div>
  </div>
  
  {#if showPreview && previewData}
    <div class="border border-gray-200 rounded p-4 bg-gray-50">
      <h4 class="font-semibold mb-3 text-gray-900">Preview Statistics</h4>
      <div class="space-y-4">
        {#each selectedColumns as colName}
          {@const original = previewData.original_stats?.[colName]}
          {@const preview = previewData.preview_stats?.[colName]}
          {#if original && preview}
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="bg-white p-3 rounded border border-gray-200">
                <div class="font-medium text-gray-700 mb-2">{colName} - Original</div>
                <div class="space-y-1 text-gray-600">
                  <div>Mean: {original.mean.toFixed(3)}</div>
                  <div>Std: {original.std.toFixed(3)}</div>
                  <div>Min: {original.min.toFixed(3)}</div>
                  <div>Max: {original.max.toFixed(3)}</div>
                </div>
              </div>
              <div class="bg-green-50 p-3 rounded border border-green-200">
                <div class="font-medium text-green-700 mb-2">{colName} - After {method}</div>
                <div class="space-y-1 text-green-900">
                  <div>Mean: {preview.mean.toFixed(3)}</div>
                  <div>Std: {preview.std.toFixed(3)}</div>
                  <div>Min: {preview.min.toFixed(3)}</div>
                  <div>Max: {preview.max.toFixed(3)}</div>
                </div>
              </div>
            </div>
          {/if}
        {/each}
      </div>
    </div>
  {/if}
  
  <div>
    <label class="flex items-center">
      <input
        type="checkbox"
        bind:checked={createNewVersion}
        class="mr-2"
      />
      <span class="text-sm">Create new version (recommended)</span>
    </label>
    <p class="text-xs text-gray-500 mt-1">
      {createNewVersion ? 'Will create a new version and keep the original' : 'Will overwrite the current dataset'}
    </p>
  </div>
  
  <div class="flex gap-3">
    <button
      type="button"
      onclick={handlePreview}
      disabled={isLoading || selectedColumns.length === 0}
      class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      {isLoading ? 'Loading...' : 'Preview'}
    </button>
    <button
      type="button"
      onclick={handleApply}
      disabled={isLoading || selectedColumns.length === 0}
      class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      {isLoading ? 'Applying...' : 'Apply Normalization'}
    </button>
  </div>
</div>