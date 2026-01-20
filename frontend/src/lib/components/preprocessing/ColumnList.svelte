<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  
  interface Props {
    columns: ColumnAnalysis[];
    selectedColumn: ColumnAnalysis | null;
    onSelect: (column: ColumnAnalysis) => void;
  }
  
  let { columns, selectedColumn, onSelect }: Props = $props();
</script>

<div class="card">
  <h3 class="text-lg font-bold mb-4">Columns</h3>
  <div class="space-y-2 max-h-[600px] overflow-y-auto">
    {#each columns as column}
      <button
        onclick={() => onSelect(column)}
        class="w-full text-left p-3 rounded-lg transition-colors {selectedColumn?.name === column.name ? 'bg-primary-50 border-primary-200 border-2' : 'hover:bg-gray-50 border-2 border-transparent'}"
      >
        <div class="flex items-center justify-between">
          <span class="font-medium truncate">{column.name}</span>
          {#if column.total_missing_count > 0}
            <span class="badge bg-orange-100 text-orange-800 text-xs">
              {column.missing_percentage}%
            </span>
          {:else}
            <span class="badge badge-success text-xs">Clean</span>
          {/if}
        </div>
        {#if column.custom_missing_count > 0}
          <p class="text-xs text-orange-600 mt-1">
            {column.custom_missing_count} suspicious values
          </p>
        {/if}
      </button>
    {/each}
  </div>
</div>