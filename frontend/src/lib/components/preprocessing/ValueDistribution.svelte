<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  
  interface Props {
    column: ColumnAnalysis;
  }
  
  let { column }: Props = $props();
</script>

{#if column.value_frequencies}
  <div class="mb-6">
    <h4 class="text-sm font-semibold text-gray-900 mb-3">Value Distribution (Top 20)</h4>
    <div class="space-y-2 max-h-64 overflow-y-auto">
      {#each Object.entries(column.value_frequencies) as [value, count]}
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="text-sm font-mono text-gray-700 truncate max-w-xs">"{value}"</span>
          <div class="flex items-center gap-2">
            <div class="w-32 bg-gray-200 rounded-full h-2">
              <div
                class="bg-primary-600 h-2 rounded-full"
                style="width: {(count / column.total_count) * 100}%"
              ></div>
            </div>
            <span class="text-sm text-gray-600 w-16 text-right">{count}</span>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}