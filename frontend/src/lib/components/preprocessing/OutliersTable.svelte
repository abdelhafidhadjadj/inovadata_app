<script lang="ts">
  let { columns }: { columns: any[] } = $props();
  
  // Filtrer seulement les colonnes avec outliers
  let columnsWithOutliers = $derived(columns.filter(col => {
    return col.outliers && (
      col.outliers.iqr?.outliers_count > 0 ||
      col.outliers.zscore?.outliers_count > 0 ||
      col.outliers.range?.outliers_count > 0
    );
  }));
</script>

<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
  <div class="p-4 bg-gray-50 border-b border-gray-200">
    <h3 class="text-lg font-semibold">Outliers Summary</h3>
    <p class="text-sm text-gray-600 mt-1">
      {columnsWithOutliers.length} columns with detected outliers
    </p>
  </div>
  
  {#if columnsWithOutliers.length > 0}
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Column
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Data Type
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              IQR Outliers
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Z-Score Outliers
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Range Outliers
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Range
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each columnsWithOutliers as column}
            <tr class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="font-medium text-gray-900">{column.name}</div>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                  {column.data_type}
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                {#if column.outliers?.iqr}
                  <span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">
                    {column.outliers.iqr.outliers_count}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                {#if column.outliers?.zscore}
                  <span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">
                    {column.outliers.zscore.outliers_count}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                {#if column.outliers?.range}
                  <span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">
                    {column.outliers.range.outliers_count}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {#if column.statistics}
                  [{column.statistics.min?.toFixed(2)}, {column.statistics.max?.toFixed(2)}]
                {:else}
                  -
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="p-8 text-center text-gray-500">
      No outliers detected in any column
    </div>
  {/if}
</div>