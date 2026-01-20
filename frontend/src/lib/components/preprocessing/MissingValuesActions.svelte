<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  import ReplacementMethodSelector from './ReplacementMethodSelector.svelte';
  
  interface Props {
    column: ColumnAnalysis;
    selectedMethod: 'mean' | 'median' | 'mode' | 'min' | 'max';
    isLoading: boolean;
    onMethodChange: (method: 'mean' | 'median' | 'mode' | 'min' | 'max') => void;
    onFill: () => void;
    onForwardFill: () => void;
    onRemove: () => void;
  }
  
  let { column, selectedMethod, isLoading, onMethodChange, onFill, onForwardFill, onRemove }: Props = $props();
  
  // ✅ Méthodes disponibles selon le type de colonne
  const availableMethods = $derived(
    column.data_type === 'numerical' 
      ? ['mean', 'median', 'mode', 'min', 'max'] as const
      : ['mode'] as const  // Pour catégoriel : uniquement mode
  );
</script>

{#if column.total_missing_count > 0}
  <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <h5 class="text-sm font-semibold text-blue-900 mb-3 flex items-center">
      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Missing Values Treatment ({column.total_missing_count} values)
    </h5>
    
    <!-- ✅ Sélecteur de méthode -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Replacement Method
      </label>
      
      {#if column.data_type === 'numerical'}
        <!-- Toutes les méthodes pour numérique -->
        <div class="grid grid-cols-5 gap-2">
          <button
            type="button"
            onclick={() => onMethodChange('mean')}
            class="px-3 py-2 text-sm rounded border transition-colors {selectedMethod === 'mean' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
            title="Average value"
          >
            Mean
          </button>
          <button
            type="button"
            onclick={() => onMethodChange('median')}
            class="px-3 py-2 text-sm rounded border transition-colors {selectedMethod === 'median' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
            title="Middle value"
          >
            Median
          </button>
          <button
            type="button"
            onclick={() => onMethodChange('mode')}
            class="px-3 py-2 text-sm rounded border transition-colors {selectedMethod === 'mode' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
            title="Most frequent value"
          >
            Mode
          </button>
          <button
            type="button"
            onclick={() => onMethodChange('min')}
            class="px-3 py-2 text-sm rounded border transition-colors {selectedMethod === 'min' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
            title="Minimum value"
          >
            Min
          </button>
          <button
            type="button"
            onclick={() => onMethodChange('max')}
            class="px-3 py-2 text-sm rounded border transition-colors {selectedMethod === 'max' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
            title="Maximum value"
          >
            Max
          </button>
        </div>
      {:else}
        <!-- Mode uniquement pour catégoriel -->
        <div class="px-4 py-3 bg-gray-100 border border-gray-300 rounded text-sm text-gray-700">
          <strong>Mode</strong> - Most frequent value (only valid method for categorical data)
        </div>
      {/if}
    </div>
    
    <div class="flex flex-wrap gap-2">
      <button 
        onclick={onFill}
        disabled={isLoading}
        class="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        {#if isLoading}
          <svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        {/if}
        Fill with {selectedMethod.charAt(0).toUpperCase() + selectedMethod.slice(1)}
      </button>
      
      <button 
        onclick={onForwardFill}
        disabled={isLoading}
        class="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        {#if isLoading}
          <svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        {/if}
        Forward Fill
      </button>
      
      <button 
        onclick={onRemove}
        disabled={isLoading}
        class="btn-danger text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        {#if isLoading}
          <svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        {/if}
        Remove Rows
      </button>
    </div>
  </div>
{:else}
  <div class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
    <div class="flex items-start gap-3">
      <svg class="w-6 h-6 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1">
        <div class="font-semibold text-green-900">No Missing Values Detected</div>
        <p class="text-sm text-green-700 mt-1">
          This column has no standard missing values (NULL, NaN, empty).
        </p>
        <p class="text-sm text-green-700 mt-2">
          💡 <strong>Tip:</strong> If your dataset has custom missing values like "!!" or "?", 
          enter them in the "Custom Missing Values" section above and click "Apply Configuration".
        </p>
      </div>
    </div>
  </div>
{/if}