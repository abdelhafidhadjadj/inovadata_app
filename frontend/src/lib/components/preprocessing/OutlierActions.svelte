<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  import ReplacementMethodSelector from './ReplacementMethodSelector.svelte';
  
  interface Props {
    column: ColumnAnalysis;
    selectedMethod: 'mean' | 'median' | 'mode' | 'min' | 'max';
    isLoading: boolean;
    onMethodChange: (method: 'mean' | 'median' | 'mode' | 'min' | 'max') => void;
    onReplace: () => void;
    onRemove: () => void;
  }
  
  let { column, selectedMethod, isLoading, onMethodChange, onReplace, onRemove }: Props = $props();
  
  const outlierCount = column.outliers?.range?.outliers_count || column.outliers?.iqr?.outliers_count || 0;
</script>

{#if column.data_type === 'numerical' && outlierCount > 0}
  <div class="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
    <h5 class="text-sm font-semibold text-orange-900 mb-3 flex items-center">
      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      Outlier Treatment
    </h5>
    
    <ReplacementMethodSelector selectedMethod={selectedMethod} onSelect={onMethodChange} />
    
    <div class="flex flex-wrap gap-2">
      <button 
        onclick={onReplace}
        disabled={isLoading}
        class="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {#if isLoading}
          <svg class="animate-spin w-4 h-4 inline mr-1" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        {/if}
        Replace with {selectedMethod.toUpperCase()} ({outlierCount})
      </button>
      
      <button 
        onclick={onRemove}
        disabled={isLoading}
        class="btn-danger text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {#if isLoading}
          <svg class="animate-spin w-4 h-4 inline mr-1" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        {/if}
        Remove Rows ({outlierCount})
      </button>
    </div>
  </div>
{/if}