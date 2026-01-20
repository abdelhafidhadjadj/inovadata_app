<script lang="ts">
  let { datasetId, onVersionChange }: { 
    datasetId: number;
    onVersionChange: () => void;
  } = $props();
  
  let versions = $state<any[]>([]);
  let isLoading = $state(false);
  let showVersions = $state(false);
  let hasLoaded = $state(false); // ✅ NOUVEAU : Flag pour éviter rechargements multiples
  
  async function loadVersions() {
    // ✅ Éviter le chargement si déjà en cours
    if (isLoading || hasLoaded) return;
    
    isLoading = true;
    try {
      console.log('📊 Loading versions for dataset', datasetId);
      
      const response = await fetch(`http://localhost:8001/dataset-versions/${datasetId}`);
      
      if (response.ok) {
        versions = await response.json();
        hasLoaded = true; // ✅ Marquer comme chargé
        console.log('✅ Loaded', versions.length, 'versions');
      } else {
        console.error('❌ Failed to load versions:', response.status);
      }
    } catch (error) {
      console.error('❌ Failed to load versions:', error);
    } finally {
      isLoading = false;
    }
  }
  
  async function activateVersion(versionId: number) {
    if (!confirm('Switch to this version? This will reload the page.')) return;
    
    try {
      const response = await fetch(`http://localhost:8001/activate-version/${versionId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        onVersionChange();
      } else {
        alert('Failed to activate version');
      }
    } catch (error) {
      console.error('Failed to activate version:', error);
      alert('Failed to activate version');
    }
  }
  
  // ✅ CORRECTION : Charger une seule fois quand on ouvre
  $effect(() => {
    if (showVersions && !hasLoaded) {
      loadVersions();
    }
  });
</script>

<div class="card my-2">
  <button
    type="button"
    onclick={() => {
      showVersions = !showVersions;
      // ✅ Recharger si on rouvre et qu'on veut des données fraîches
      if (showVersions && hasLoaded) {
        hasLoaded = false; // Permet un rechargement
      }
    }}
    class="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
  >
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="font-semibold">Dataset Versions</span>
      {#if versions.length > 0}
        <span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
          {versions.length}
        </span>
      {/if}
    </div>
    <svg 
      class="w-5 h-5 text-gray-400 transition-transform {showVersions ? 'rotate-180' : ''}" 
      fill="none" 
      stroke="currentColor" 
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
    </svg>
  </button>
  
  {#if showVersions}
    <div class="border-t border-gray-200 p-4">
      {#if isLoading}
        <div class="text-center py-4 text-gray-500">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          <div class="mt-2">Loading versions...</div>
        </div>
      {:else if versions.length === 0}
        <div class="text-center py-8">
          <svg class="w-12 h-12 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-gray-500 text-sm">No versions yet</p>
          <p class="text-gray-400 text-xs mt-1">Versions will appear here after transformations</p>
        </div>
      {:else}
        <div class="space-y-2">
          {#each versions as version}
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded hover:border-primary-300 transition-colors {version.is_active ? 'bg-primary-50 border-primary-300' : 'bg-white'}">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-sm">Version {version.version_number}</span>
                  {#if version.is_active}
                    <span class="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full font-medium">Active</span>
                  {/if}
                </div>
                {#if version.description}
                  <div class="text-xs text-gray-600 mt-1">{version.description}</div>
                {/if}
                <div class="text-xs text-gray-400 mt-1">
                  {new Date(version.created_at).toLocaleString()}
                </div>
              </div>
              {#if !version.is_active}
                <button
                  type="button"
                  onclick={() => activateVersion(version.id)}
                  class="px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded transition-colors"
                >
                  Activate
                </button>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>