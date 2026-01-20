<script lang="ts">
  import { enhance } from '$app/forms';
  import type { PageData, ActionData } from './$types';
  import Header from '$lib/components/Header.svelte';
  
  let { data, form }: { data: PageData; form: ActionData } = $props();
  
  let loading = $state(false);
  let dragActive = $state(false);
  let fileInputRef: HTMLInputElement;
  let hasFile = $state(false); // Trigger for reactivity
  
  // File info derived from input
  let fileInfo = $derived.by(() => {
    if (!hasFile || !fileInputRef?.files?.[0]) return null;
    const file = fileInputRef.files[0];
    return {
      name: file.name,
      size: (file.size / 1024).toFixed(2) + ' KB',
      type: file.type || 'Unknown',
      extension: '.' + file.name.split('.').pop()?.toLowerCase()
    };
  });

  function handleDrag(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      dragActive = true;
    } else if (e.type === "dragleave") {
      dragActive = false;
    }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    dragActive = false;

    if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      // Create a new DataTransfer to set files
      const dt = new DataTransfer();
      dt.items.add(e.dataTransfer.files[0]);
      fileInputRef.files = dt.files;
      hasFile = true;
    }
  }

  function handleFileChange() {
    hasFile = fileInputRef?.files?.length > 0;
  }

  function removeFile() {
    if (fileInputRef) {
      fileInputRef.value = '';
      hasFile = false;
    }
  }

  function openFileDialog() {
    fileInputRef?.click();
  }
</script>

<svelte:head>
  <title>Upload Dataset - {data.project.name}</title>
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
      <span class="text-gray-900 font-medium">Upload Dataset</span>
    </nav>

    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Upload Dataset</h1>
      <p class="text-gray-600">
        Upload a CSV, JSON, or ARFF file to analyze in this project
      </p>
    </div>

    <!-- Upload Form -->
    <div class="max-w-3xl">
      {#if form?.error}
        <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div class="flex items-start">
            <svg class="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="text-sm font-medium text-red-800">Upload Error</h3>
              <p class="text-sm text-red-700 mt-1">{form.error}</p>
            </div>
          </div>
        </div>
      {/if}

      <form method="POST" action="?/upload" enctype="multipart/form-data" use:enhance={() => {
        loading = true;
        return async ({ update }) => {
          await update();
          loading = false;
        };
      }}>
        <div class="space-y-6">
          <!-- File Upload Area -->
          <div class="card">
            <h3 class="text-lg font-bold text-gray-900 mb-4">Select File</h3>
            
            {#if !fileInfo}
              <!-- Drag and Drop Zone -->
              <div
                class="border-2 border-dashed rounded-lg p-8 text-center transition-colors {dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'}"
                ondragenter={handleDrag}
                ondragover={handleDrag}
                ondragleave={handleDrag}
                ondrop={handleDrop}
              >
                <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                
                <p class="text-lg font-medium text-gray-900 mb-2">
                  Drop your file here, or <button type="button" onclick={openFileDialog} class="text-primary-600 hover:text-primary-700 underline">browse</button>
                </p>
                
                <p class="text-sm text-gray-500 mb-4">
                  Supported formats: CSV, JSON, ARFF (Max 100MB)
                </p>
              </div>
            {:else}
              <!-- Selected File Info -->
              <div class="border-2 border-primary-300 bg-primary-50 rounded-lg p-6">
                <div class="flex items-start justify-between">
                  <div class="flex items-start gap-4 flex-1">
                    <div class="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center flex-shrink-0">
                      <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-lg font-semibold text-gray-900 truncate">{fileInfo.name}</p>
                      <div class="flex items-center gap-4 mt-1 text-sm text-gray-600">
                        <span>{fileInfo.size}</span>
                        <span class="badge badge-info">{fileInfo.extension.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onclick={removeFile}
                    class="text-gray-400 hover:text-gray-600 ml-4"
                    disabled={loading}
                  >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            {/if}
            
            <!-- File input (always present, hidden) -->
            <input
              bind:this={fileInputRef}
              type="file"
              name="file"
              accept=".csv,.json,.arff"
              class="hidden"
              onchange={handleFileChange}
              required
            />
          </div>

          <!-- Dataset Information -->
          <div class="card">
            <h3 class="text-lg font-bold text-gray-900 mb-4">Dataset Information</h3>
            
            <div class="space-y-4">
              <div>
                <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
                  Dataset Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={form?.name || fileInfo?.name.split('.')[0] || ''}
                  required
                  class="input-field"
                  placeholder="My Dataset"
                  disabled={loading}
                />
                <p class="mt-1 text-xs text-gray-500">
                  A descriptive name for your dataset
                </p>
              </div>

              <div>
                <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows="3"
                  class="input-field resize-none"
                  placeholder="Brief description of the dataset..."
                  disabled={loading}
                >{form?.description || ''}</textarea>
              </div>
            </div>
          </div>

          <!-- Supported Features Info -->
          <div class="card bg-blue-50 border-blue-200">
            <div class="flex items-start gap-3">
              <svg class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 class="text-sm font-medium text-blue-900 mb-1">What happens next?</h4>
                <ul class="text-sm text-blue-800 space-y-1">
                  <li>• Automatic metadata extraction (rows, columns, data types)</li>
                  <li>• Missing values detection</li>
                  <li>• Statistical analysis</li>
                  <li>• Data preview and validation</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-between pt-4">
            <a
              href="/dashboard/projects/{data.project.id}"
              class="btn-secondary"
            >
              Cancel
            </a>
            
            <button
              type="submit"
              disabled={loading || !hasFile}
              class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {#if loading}
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              {:else}
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Dataset
              {/if}
            </button>
          </div>
        </div>
      </form>
    </div>
  </main>
</div>