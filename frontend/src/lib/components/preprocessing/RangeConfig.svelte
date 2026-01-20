<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  
  interface Props {
    column: ColumnAnalysis;
    min: number | undefined;
    max: number | undefined;
    onMinChange: (value: number | undefined) => void;
    onMaxChange: (value: number | undefined) => void;
    onApply: () => void;
    isAnalyzing: boolean;
  }
  
  let { column, min, max, onMinChange, onMaxChange, onApply, isAnalyzing }: Props = $props();
</script>

{#if column.data_type === 'numerical'}
  <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <h4 class="text-sm font-semibold text-blue-900 mb-3">
      ✅ Valid Value Range
    </h4>
    <p class="text-xs text-gray-600 mb-3">
      Define the acceptable range for this column. Values outside this range will be detected as outliers.
    </p>
    
    <div class="grid grid-cols-2 gap-4 mb-4">
      <div>
        <label class="block text-xs text-gray-700 mb-1">Minimum Value</label>
        <input
          type="number"
          step="any"
          value={min ?? ''}
          oninput={(e) => {
            const val = (e.target as HTMLInputElement).value;
            onMinChange(val ? parseFloat(val) : undefined);
          }}
          placeholder="No limit"
          class="input-field text-sm"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-700 mb-1">Maximum Value</label>
        <input
          type="number"
          step="any"
          value={max ?? ''}
          oninput={(e) => {
            const val = (e.target as HTMLInputElement).value;
            onMaxChange(val ? parseFloat(val) : undefined);
          }}
          placeholder="No limit"
          class="input-field text-sm"
        />
      </div>
    </div>

    <!-- Current Stats for Reference -->
    {#if column.statistics}
      <div class="grid grid-cols-3 gap-2 text-xs mb-3">
        <div class="p-2 bg-white rounded">
          <span class="text-gray-600">Current Min:</span>
          <span class="font-mono ml-1">{column.statistics.min}</span>
        </div>
        <div class="p-2 bg-white rounded">
          <span class="text-gray-600">Current Max:</span>
          <span class="font-mono ml-1">{column.statistics.max}</span>
        </div>
        <div class="p-2 bg-white rounded">
          <span class="text-gray-600">Median:</span>
          <span class="font-mono ml-1">{column.statistics.median}</span>
        </div>
      </div>
    {/if}

    <!-- Apply Button -->
    <button
      onclick={onApply}
      disabled={isAnalyzing}
      class="w-full btn-primary text-sm {isAnalyzing ? 'opacity-50 cursor-wait' : ''}"
    >
      {#if isAnalyzing}
        <svg class="animate-spin w-4 h-4 inline mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Analyzing...
      {:else}
        Apply Range & Re-analyze
      {/if}
    </button>

    <!-- Range Outliers (if detected) -->
    {#if column.outliers?.range}
      <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded">
        <h5 class="text-xs font-semibold text-red-900 mb-1">
          🚨 Range Outliers Detected
        </h5>
        <p class="text-xs text-red-700">
          {column.outliers.range.outliers_count} values outside configured range
        </p>
        {#if column.configured_range}
          <p class="text-xs text-gray-600 mt-1">
            Valid range: [{column.configured_range.min ?? '−∞'}, {column.configured_range.max ?? '+∞'}]
          </p>
        {/if}
      </div>
    {/if}
  </div>
{/if}