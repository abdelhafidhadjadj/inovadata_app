<script lang="ts">
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation'; // AJOUTÉ
  import type { PageData, ActionData } from './$types';
  import Header from '$lib/components/Header.svelte';
  
  let { data, form }: { data: PageData; form: ActionData } = $props();
  
  let showDeleteConfirm = $state(false);
  let activeTab = $state<'preview' | 'statistics' | 'metadata'>('statistics');
  
  // Parse metadata
  let metadata = $derived.by(() => {
    try {
      return typeof data.dataset.metadata === 'string' 
        ? JSON.parse(data.dataset.metadata)
        : data.dataset.metadata || {};
    } catch {
      return {};
    }
  });

  // Vérifier le statut de traitement
  let isProcessed = $derived(data.dataset.processing_status === 'completed');
  let isProcessing = $derived(data.dataset.processing_status === 'processing');
  let isFailed = $derived(data.dataset.processing_status === 'failed');
  let isPending = $derived(data.dataset.processing_status === 'pending');
  
  // Parse columns_info
  let columnsInfo = $derived.by(() => {
    if (!data.dataset.columns_info) return [];
    try {
      return typeof data.dataset.columns_info === 'string'
        ? JSON.parse(data.dataset.columns_info)
        : data.dataset.columns_info;
    } catch {
      return [];
    }
  });
  
  // Auto-refresh si en cours de traitement
  $effect(() => {
    if (isProcessing || isPending) {
      const interval = setInterval(() => {
        window.location.reload();
      }, 5000);
      
      return () => clearInterval(interval);
    }
  });
</script>

<svelte:head>
  <title>{data.dataset.name} - DataMine</title>
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
      <span class="text-gray-900 font-medium">{data.dataset.name}</span>
    </nav>

    <!-- Alerte de statut de traitement -->
    {#if isPending || isProcessing}
      <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div class="flex items-start">
          <svg class="animate-spin w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <div>
            <h3 class="text-sm font-medium text-blue-800">
              {isPending ? 'Analysis Pending' : 'Analyzing Dataset'}
            </h3>
            <p class="text-sm text-blue-700 mt-1">
              {isPending 
                ? 'Your dataset is in queue for analysis. This page will refresh automatically.' 
                : 'Extracting metadata, analyzing columns, and calculating statistics...'}
            </p>
          </div>
        </div>
      </div>
    {:else if isFailed}
      <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div class="flex items-start justify-between">
          <div class="flex items-start">
            <svg class="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="text-sm font-medium text-red-800">Analysis Failed</h3>
              <p class="text-sm text-red-700 mt-1">
                {data.dataset.processing_error || 'Unknown error'}
              </p>
            </div>
          </div>
          <form method="POST" action="?/retryProcessing" use:enhance>
            <button type="submit" class="btn-secondary text-sm">
              Retry Analysis
            </button>
          </form>
        </div>
      </div>
    {:else if isProcessed}
      <div class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-green-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="text-sm font-medium text-green-800">Dataset Ready</h3>
            <p class="text-sm text-green-700 mt-1">
              Analysis completed {data.dataset.processed_at ? `on ${new Date(data.dataset.processed_at).toLocaleString()}` : ''}
            </p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Dataset Header -->
    <div class="card mb-6">
      <div class="flex items-start justify-between mb-4">
        
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-3xl font-bold text-gray-900">{data.dataset.name}</h1>
            <span class="badge badge-info">{data.dataset.file_format?.toUpperCase()}</span>
            
            <!-- Badge de statut -->
            {#if isPending}
              <span class="badge bg-blue-100 text-blue-800">Pending</span>
            {:else if isProcessing}
              <span class="badge bg-blue-100 text-blue-800">Processing...</span>
            {:else if isProcessed}
              <span class="badge badge-success">Ready</span>
            {:else if isFailed}
              <span class="badge bg-red-100 text-red-800">Failed</span>
            {/if}
          </div>
          {#if metadata.description}
            <p class="text-gray-600">{metadata.description}</p>
          {/if}
          <div class="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span>Uploaded by {data.dataset.creator_username}</span>
            <span>•</span>
            <span>{new Date(data.dataset.upload_date).toLocaleDateString()}</span>
            {#if data.dataset.memory_usage}
              <span>•</span>
              <span>{data.dataset.memory_usage.toFixed(2)} MB in memory</span>
            {/if}
          </div>
        </div>
        
        <!-- MODIFIÉ: Ajout du bouton ML -->
        <div class="flex gap-2">
          {#if isProcessed}
            <!-- Bouton ML - NOUVEAU -->
            <button 
              onclick={() => goto(`/dashboard/projects/${data.project.id}/datasets/${data.dataset.id}/ml`)}
              class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <span class="text-lg">🤖</span>
              ML Training
            </button>
            
            <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}/preprocess" class="btn-secondary">
              <svg class="w-5 h-5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              Preprocess
            </a>
          {/if}
          <button onclick={() => showDeleteConfirm = true} class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
            <svg class="w-5 h-5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-4 gap-4 pt-4 border-t">
        <div>
          <p class="text-sm text-gray-600">Rows</p>
          <p class="text-2xl font-bold text-gray-900">
            {isProcessed ? data.dataset.rows_count?.toLocaleString() : '—'}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Columns</p>
          <p class="text-2xl font-bold text-gray-900">
            {isProcessed ? data.dataset.columns_count : '—'}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-600">File Size</p>
          <p class="text-2xl font-bold text-gray-900">
            {data.dataset.file_size ? (data.dataset.file_size / 1024).toFixed(2) + ' KB' : 'N/A'}
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Format</p>
          <p class="text-2xl font-bold text-gray-900">{data.dataset.file_format?.toUpperCase() || 'N/A'}</p>
        </div>
      </div>
    </div>

    <!-- Tabs (seulement si traité) -->
    {#if isProcessed}
      <div class="mb-6 border-b border-gray-200">
        <nav class="flex space-x-8">
          <button
            onclick={() => activeTab = 'statistics'}
            class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'statistics' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
          >
            Column Statistics
          </button>
          <button
            onclick={() => activeTab = 'preview'}
            class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'preview' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
          >
            Data Preview
          </button>
          <button
            onclick={() => activeTab = 'metadata'}
            class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'metadata' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
          >
            Metadata
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      {#if activeTab === 'statistics'}
        <!-- Affichage des statistiques par colonne -->
        {#if columnsInfo.length > 0}
          <div class="space-y-4">
            {#each columnsInfo as column}
              <div class="card">
                <div class="flex items-start justify-between mb-3">
                  <div>
                    <h3 class="text-lg font-semibold text-gray-900">{column.name}</h3>
                    <div class="flex gap-2 mt-1">
                      <span class="badge {column.data_type === 'numerical' ? 'badge-info' : column.data_type === 'categorical' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'}">
                        {column.data_type}
                      </span>
                      {#if column.missing_percentage > 0}
                        <span class="badge bg-orange-100 text-orange-800">
                          {column.missing_percentage}% missing
                        </span>
                      {/if}
                    </div>
                  </div>
                  <div class="text-sm text-gray-600">
                    {column.unique_count} unique values
                  </div>
                </div>
                
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {#if column.data_type === 'numerical'}
                    <div>
                      <p class="text-xs text-gray-600">Mean</p>
                      <p class="text-lg font-semibold">{column.mean?.toFixed(2) ?? '—'}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-600">Std Dev</p>
                      <p class="text-lg font-semibold">{column.std?.toFixed(2) ?? '—'}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-600">Min</p>
                      <p class="text-lg font-semibold">{column.min?.toFixed(2) ?? '—'}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-600">Max</p>
                      <p class="text-lg font-semibold">{column.max?.toFixed(2) ?? '—'}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-600">Median</p>
                      <p class="text-lg font-semibold">{column.median?.toFixed(2) ?? '—'}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-600">Q25 - Q75</p>
                      <p class="text-lg font-semibold">{column.q25?.toFixed(2)} - {column.q75?.toFixed(2)}</p>
                    </div>
                  {:else if column.data_type === 'categorical' && column.top_values}
                    <div class="col-span-2 md:col-span-4">
                      <p class="text-xs text-gray-600 mb-2">Top Values</p>
                      <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {#each Object.entries(column.top_values).slice(0, 6) as [value, count]}
                          <div class="flex justify-between text-sm p-2 bg-gray-50 rounded">
                            <span class="text-gray-700 truncate">{value}</span>
                            <span class="text-gray-500 ml-2">{count}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                  
                  <div>
                    <p class="text-xs text-gray-600">Missing</p>
                    <p class="text-lg font-semibold">{column.missing_count}</p>
                  </div>
                </div>
                
                {#if column.sample_values?.length > 0}
                  <div class="mt-3 pt-3 border-t">
                    <p class="text-xs text-gray-600 mb-1">Sample Values</p>
                    <div class="flex flex-wrap gap-2">
                      {#each column.sample_values.slice(0, 5) as value}
                        <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                          {value}
                        </span>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <div class="card text-center py-12">
            <p class="text-gray-500">No statistics available</p>
          </div>
        {/if}
        
        {:else if activeTab === 'preview'}
          <div class="card">
            <div class="mb-4 flex items-center justify-between">
              <h3 class="text-lg font-bold text-gray-900">Data Preview</h3>
              <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}/preview" class="btn-primary">
                View Full Table
              </a>
            </div>

            <p class="text-gray-600 text-center py-8">
              Click "View Full Table" to see your data in a paginated table view
            </p>
          </div>
        
      {:else if activeTab === 'metadata'}
        <div class="card">
          <h3 class="text-lg font-bold text-gray-900 mb-4">Dataset Metadata</h3>
          
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm font-medium text-gray-700">Filename</p>
                <p class="text-gray-900">{data.dataset.filename || 'N/A'}</p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">Format</p>
                <p class="text-gray-900">{data.dataset.file_format?.toUpperCase() || 'N/A'}</p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">Upload Date</p>
                <p class="text-gray-900">{new Date(data.dataset.upload_date).toLocaleString()}</p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">Processed Date</p>
                <p class="text-gray-900">
                  {data.dataset.processed_at ? new Date(data.dataset.processed_at).toLocaleString() : 'N/A'}
                </p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">Uploaded By</p>
                <p class="text-gray-900">{data.dataset.creator_username}</p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">File Size</p>
                <p class="text-gray-900">
                  {data.dataset.file_size ? (data.dataset.file_size / 1024).toFixed(2) + ' KB' : 'N/A'}
                </p>
              </div>
            </div>

            {#if metadata.description}
              <div class="pt-4 border-t">
                <p class="text-sm font-medium text-gray-700 mb-2">Description</p>
                <p class="text-gray-900">{metadata.description}</p>
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- Actions -->
      <div class="mt-6 card bg-blue-50 border-blue-200">
        <h4 class="text-sm font-semibold text-blue-900 mb-3">Next Steps</h4>
        <div class="space-y-2 text-sm text-blue-800">
          <p>• <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}/preprocess" class="text-primary-600 hover:text-primary-700 font-medium">Preprocess this dataset</a> to clean and prepare your data</p>
          <p>• <button onclick={() => goto(`/dashboard/projects/${data.project.id}/datasets/${data.dataset.id}/ml`)} class="text-purple-600 hover:text-purple-700 font-medium">Train ML models</button> on this dataset</p>
          <p>• <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}/visualize" class="text-primary-600 hover:text-primary-700 font-medium">Visualize your data</a> to understand patterns</p>
        </div>
      </div>
    {/if}
  </main>
</div>

<!-- Delete Confirmation -->
{#if showDeleteConfirm}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
    <div class="card max-w-md w-full">
      <h3 class="text-xl font-bold text-gray-900 mb-4">Delete Dataset</h3>
      <p class="text-gray-600 mb-6">
        Are you sure you want to delete "{data.dataset.name}"? This action cannot be undone.
      </p>
      
      <form method="POST" action="?/delete" use:enhance>
        <div class="flex space-x-3">
          <button type="button" onclick={() => showDeleteConfirm = false} class="flex-1 btn-secondary">
            Cancel
          </button>
          <button type="submit" class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
            Delete Dataset
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}