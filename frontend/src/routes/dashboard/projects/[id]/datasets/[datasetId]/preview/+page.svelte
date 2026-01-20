<script lang="ts">
  import type { PageData } from './$types';
  import Header from '$lib/components/Header.svelte';
  import { goto } from '$app/navigation';
  
  let { data }: { data: PageData } = $props();
  
  function goToPage(page: number) {
    goto(`?page=${page}`);
  }
</script>

<svelte:head>
  <title>Preview: {data.dataset.name} - DataMine</title>
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
      <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}" class="hover:text-gray-900">{data.dataset.name}</a>
      <svg class="w-4 h-4 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <span class="text-gray-900 font-medium">Preview</span>
    </nav>

    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Data Preview</h1>
        <p class="text-gray-600">
          Showing {data.preview.length} of {data.totalRows.toLocaleString()} rows
        </p>
      </div>
      <a href="/dashboard/projects/{data.project.id}/datasets/{data.dataset.id}" class="btn-secondary">
        Back to Dataset
      </a>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50">
                #
              </th>
              {#each data.columns as column}
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  {column}
                </th>
              {/each}
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            {#each data.preview as row, idx}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white">
                  {(data.currentPage - 1) * data.limit + idx + 1}
                </td>
                {#each data.columns as column}
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row[column] !== null && row[column] !== undefined ? row[column] : '—'}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div class="mt-6 flex items-center justify-between">
      <div class="text-sm text-gray-600">
        Page {data.currentPage} of {data.totalPages}
      </div>
      <div class="flex gap-2">
        <button
          onclick={() => goToPage(data.currentPage - 1)}
          disabled={data.currentPage === 1}
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <!-- Page numbers -->
        <div class="flex gap-1">
          {#each Array.from({length: Math.min(5, data.totalPages)}, (_, i) => {
            const start = Math.max(1, data.currentPage - 2);
            return start + i;
          }).filter(p => p <= data.totalPages) as page}
            <button
              onclick={() => goToPage(page)}
              class="px-4 py-2 rounded-lg {page === data.currentPage ? 'bg-primary-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}"
            >
              {page}
            </button>
          {/each}
        </div>
        
        <button
          onclick={() => goToPage(data.currentPage + 1)}
          disabled={data.currentPage === data.totalPages}
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  </main>
</div>