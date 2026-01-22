<script lang="ts">
  let { columns, dataset, onTransform }: { 
    columns: any[]; 
    dataset: any;
    onTransform: () => void;
  } = $props();
  
  let selectedColumns = $state<string[]>([]);
  let method = $state<'label_encoding' | 'onehot_encoding'>('label_encoding');
  let dropFirst = $state(false);
  let isLoading = $state(false);
  let previewData = $state<any>(null);
  let showPreview = $state(false);
  
  let categoricalColumns = $derived(
    columns.filter(col => col.data_type === 'categorical')
  );
  
  let allSelected = $derived(
    categoricalColumns.length > 0 && selectedColumns.length === categoricalColumns.length
  );
  
  function toggleColumn(columnName: string) {
    if (selectedColumns.includes(columnName)) {
      selectedColumns = selectedColumns.filter(c => c !== columnName);
    } else {
      selectedColumns = [...selectedColumns, columnName];
    }
  }
  
  function toggleSelectAll() {
    if (allSelected) {
      selectedColumns = [];
    } else {
      selectedColumns = categoricalColumns.map(col => col.name);
    }
  }
  
  async function handlePreview() {
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
      
      const response = await fetch('http://localhost:8001/transform-preview-encode', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) throw new Error('Preview failed');
      
      previewData = await response.json();
      showPreview = true;
    } catch (error) {
      console.error('Preview error:', error);
      alert('Failed to generate preview');
    } finally {
      isLoading = false;
    }
  }
  
  async function handleApply() {
    if (selectedColumns.length === 0) {
      alert('Please select at least one column');
      return;
    }
    
    if (!confirm(`Apply ${method} to ${selectedColumns.length} column(s)?`)) {
      return;
    }
    
    isLoading = true;
    
    try {
      const formData = new FormData();
      formData.append('file_path', dataset.file_path);
      formData.append('file_format', dataset.file_format);
      formData.append('columns', JSON.stringify(selectedColumns));
      formData.append('method', method);
      formData.append('drop_first', dropFirst.toString());
      formData.append('dataset_id', dataset.id.toString());
      formData.append('create_new_version', 'true');
      
      console.log('📤 Sending encoding request:', {
        file_path: dataset.file_path,
        file_format: dataset.file_format,
        columns: selectedColumns,
        method,
        drop_first: dropFirst,
        dataset_id: dataset.id,
        create_new_version: true
      });
      
      const response = await fetch('http://localhost:8001/transform-encode', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Encoding failed');
      }
      
      const result = await response.json();
      console.log('✅ Encoding result:', result);
      
      alert(result.message);
      
      await new Promise(resolve => setTimeout(resolve, 500));
      onTransform();
      
    } catch (error: any) {
      console.error('❌ Encoding error:', error);
      alert(`Failed to apply encoding: ${error.message}`);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="card space-y-6">
  <div>
    <h3 class="text-lg font-semibold mb-2">Categorical Encoding</h3>
    <p class="text-sm text-gray-600">Convert categorical variables to numerical format</p>
  </div>
  
  <!-- Method Selection -->
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Method</label>
    <div class="grid grid-cols-2 gap-3">
      <button
        type="button"
        onclick={() => { method = 'label_encoding'; dropFirst = false; }}
        class="px-4 py-2 rounded border transition-colors {method === 'label_encoding' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
      >
        Label Encoding
      </button>
      <button
        type="button"
        onclick={() => method = 'onehot_encoding'}
        class="px-4 py-2 rounded border transition-colors {method === 'onehot_encoding' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
      >
        One-Hot Encoding
      </button>
    </div>
    
    <!-- Method Description -->
    <div class="mt-2 p-3 bg-blue-50 rounded text-sm text-blue-800">
      {#if method === 'label_encoding'}
        <strong>Label Encoding:</strong> Converts categories to integers (0, 1, 2...). Use for ordinal data or tree-based models.
      {:else}
        <strong>One-Hot Encoding:</strong> Creates binary columns for each category. Use when categories have no natural ordering.
      {/if}
    </div>
  </div>
  
  <!-- One-Hot Options -->
  {#if method === 'onehot_encoding'}
    <div>
      <label class="flex items-center">
        <input
          type="checkbox"
          bind:checked={dropFirst}
          class="mr-2 rounded border-gray-300"
        />
        <span class="text-sm">Drop first dummy column (avoid multicollinearity)</span>
      </label>
    </div>
  {/if}
  
  <!-- Column Selection -->
  <div>
    <div class="flex items-center justify-between mb-2">
      <label class="text-sm font-medium text-gray-700">
        Select Categorical Columns ({selectedColumns.length} selected)
      </label>
      {#if categoricalColumns.length > 0}
        <button
          type="button"
          onclick={toggleSelectAll}
          class="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>
      {/if}
    </div>
    
    {#if categoricalColumns.length === 0}
      <div class="border border-gray-200 rounded p-6 text-center text-gray-500">
        <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>No categorical columns found in this dataset</p>
        <p class="text-sm mt-1">Categorical columns are required for encoding</p>
      </div>
    {:else}
      <div class="border border-gray-200 rounded max-h-64 overflow-y-auto">
        {#each categoricalColumns as column}
          <label class="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0">
            <input
              type="checkbox"
              checked={selectedColumns.includes(column.name)}
              onchange={() => toggleColumn(column.name)}
              class="mr-3 rounded border-gray-300"
            />
            <div class="flex-1">
              <div class="font-medium text-gray-900">{column.name}</div>
              <div class="text-xs text-gray-500">
                {column.unique_count} unique values
              </div>
            </div>
          </label>
        {/each}
      </div>
    {/if}
  </div>
  
  <!-- Preview -->
  {#if showPreview && previewData}
    <div class="border border-gray-200 rounded p-4 bg-gray-50">
      <h4 class="font-semibold mb-3">Encoding Preview</h4>
      <div class="space-y-4">
        {#each selectedColumns as colName}
          {@const mapping = previewData.mappings?.[colName]}
          {#if mapping}
            <div class="text-sm bg-white p-3 rounded border border-gray-200">
              <div class="font-medium text-gray-700 mb-2">{colName}</div>
              {#if method === 'label_encoding'}
                <div class="grid grid-cols-2 gap-2 text-xs">
                  {#each Object.entries(mapping) as [value, code]}
                    <div class="flex justify-between p-2 bg-gray-50 rounded">
                      <span class="text-gray-700">{value}</span>
                      <span class="font-mono text-primary-600">{code}</span>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="text-xs">
                  <div class="mb-1 text-gray-600">Will create {mapping.count || 0} new columns:</div>
                  <div class="flex flex-wrap gap-1">
                    {#each (mapping.new_columns || []) as newCol}
                      <span class="px-2 py-1 bg-green-100 text-green-800 rounded">{newCol}</span>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        {/each}
        
        {#if previewData.estimated_new_columns !== undefined}
          <div class="p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div class="text-sm text-yellow-800">
              <strong>Estimated new columns:</strong> {previewData.estimated_new_columns}
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Actions -->
  <div class="flex gap-3">
    <button
      type="button"
      onclick={handlePreview}
      disabled={isLoading || selectedColumns.length === 0}
      class="btn-secondary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {#if isLoading}
        <svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      {/if}
      {isLoading ? 'Loading...' : 'Preview'}
    </button>
    <button
      type="button"
      onclick={handleApply}
      disabled={isLoading || selectedColumns.length === 0}
      class="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {#if isLoading}
        <svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      {/if}
      {isLoading ? 'Applying...' : 'Apply Encoding'}
    </button>
  </div>
</div>