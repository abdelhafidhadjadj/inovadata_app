<script lang="ts">
  import type { ColumnAnalysis } from '../../routes/dashboard/projects/[id]/datasets/[datasetId]/preprocess/preprocess-helpers';
  
  interface Props {
    column: ColumnAnalysis;
  }
  
  let { column }: Props = $props();
</script>

<div class="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
  <div>
    <p class="text-xs text-gray-600">Total Missing</p>
    <p class="text-2xl font-bold text-orange-600">{column.total_missing_count}</p>
    <p class="text-xs text-gray-500">{column.missing_percentage}%</p>
  </div>
  <div>
    <p class="text-xs text-gray-600">Standard Missing</p>
    <p class="text-2xl font-bold">{column.standard_missing_count}</p>
    <p class="text-xs text-gray-500">NULL, NaN</p>
  </div>
  <div>
    <p class="text-xs text-gray-600">Custom Missing</p>
    <p class="text-2xl font-bold text-red-600">{column.custom_missing_count}</p>
    <p class="text-xs text-gray-500">?, -, etc.</p>
  </div>
</div>