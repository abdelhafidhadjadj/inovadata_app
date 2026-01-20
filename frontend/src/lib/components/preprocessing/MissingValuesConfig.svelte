<script lang="ts">
  import { goto } from '$app/navigation';
  
  let { column, value, onUpdate }: {
    column: any;
    value: string;
    onUpdate: (val: string) => void;
  } = $props();
  
  let isApplying = $state(false);
  
  function handleApplyConfig() {
    if (!value.trim()) {
      alert('Please enter custom missing values first');
      return;
    }
    
    isApplying = true;
    
    // Construire l'URL avec les paramètres
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('column', column.name);
    currentUrl.searchParams.set(`${column.name}_missing`, value);
    
    // Rediriger pour recharger l'analyse
    window.location.href = currentUrl.toString();
  }
</script>

<div class="mb-6 p-4 bg-white border border-gray-200 rounded-lg">
  <h5 class="text-sm font-semibold text-gray-900 mb-4 flex items-center">
    <svg class="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
    </svg>
    Custom Missing Values Configuration
  </h5>
  
  <!-- Custom Missing Values Input -->
  <div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      Custom Missing Values (comma-separated)
    </label>
    <input
      type="text"
      value={value}
      oninput={(e) => onUpdate(e.currentTarget.value)}
      placeholder="?, ??, !!, -, N/A, ..."
      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
    />
    <p class="mt-1 text-xs text-gray-500">
      Enter values that should be treated as missing (e.g., ?, ??, !!, N/A)
    </p>
  </div>
  
  <!-- Warning Message -->
  <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
    <div class="flex items-start gap-3">
      <svg class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1 text-sm text-blue-800">
        <strong>How it works:</strong>
        <ol class="list-decimal ml-4 mt-2 space-y-1">
          <li>Enter the values you want to treat as missing (e.g., "!!", "?")</li>
          <li>Click "Apply Configuration" below to refresh the analysis</li>
          <li>The missing value counts will update to include these custom values</li>
          <li>Then use the treatment actions to fill or remove the missing values</li>
        </ol>
      </div>
    </div>
  </div>
  
  <!-- Apply Button -->
  <button
    type="button"
    onclick={handleApplyConfig}
    disabled={isApplying || !value.trim()}
    class="w-full px-4 py-2.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
  >
    {#if isApplying}
      <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Applying Configuration...
    {:else}
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Apply Configuration & Refresh Analysis
    {/if}
  </button>
</div>