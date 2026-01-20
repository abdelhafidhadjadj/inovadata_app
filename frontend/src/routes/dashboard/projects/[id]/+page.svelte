<script lang="ts">
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import type { PageData, ActionData } from './$types';
  import Header from '$lib/components/Header.svelte';
  
  let { data, form }: { data: PageData; form: ActionData } = $props();
  
  let showEditModal = $state(false);
  let showAddMemberModal = $state(false);
  let showDeleteConfirm = $state(false);
  let loading = $state(false);
  let activeTab = $state<'overview' | 'datasets' | 'experiments' | 'members'>('overview');
</script>

<svelte:head>
  <title>{data.project.name} - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <Header user={data.user} />
  
  <main class="container mx-auto px-4 py-8">
    <!-- Project Header -->
    <div class="card mb-6">
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-3xl font-bold text-gray-900">{data.project.name}</h1>
            <span class="badge badge-{data.project.member_role === 'owner' ? 'success' : 'info'}">
              {data.project.member_role}
            </span>
            {#if data.project.is_public}
              <span class="badge bg-purple-100 text-purple-800">Public</span>
            {/if}
          </div>
          {#if data.project.description}
            <p class="text-gray-600">{data.project.description}</p>
          {/if}
          <p class="text-sm text-gray-500 mt-2">
            Created by {data.project.owner_username} on {new Date(data.project.created_at).toLocaleDateString()}
          </p>
        </div>
        
        {#if data.project.member_role === 'owner' || data.project.member_role === 'editor'}
          <div class="flex gap-2">
            <button onclick={() => showEditModal = true} class="btn-secondary">
              <svg class="w-5 h-5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </button>
            {#if data.project.member_role === 'owner'}
              <button onclick={() => showDeleteConfirm = true} class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                <svg class="w-5 h-5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 gap-4 pt-4 border-t">
        <div>
          <p class="text-sm text-gray-600">Datasets</p>
          <p class="text-2xl font-bold text-gray-900">{data.datasets.length}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Experiments</p>
          <p class="text-2xl font-bold text-gray-900">{data.experiments.length}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Members</p>
          <p class="text-2xl font-bold text-gray-900">{data.members.length}</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mb-6 border-b border-gray-200">
      <nav class="flex space-x-8">
        <button
          onclick={() => activeTab = 'overview'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'overview' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        >
          Overview
        </button>
        <button
          onclick={() => activeTab = 'datasets'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'datasets' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        >
          Datasets ({data.datasets.length})
        </button>
        <button
          onclick={() => activeTab = 'experiments'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'experiments' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        >
          Experiments ({data.experiments.length})
        </button>
        <button
          onclick={() => activeTab = 'members'}
          class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'members' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        >
          Members ({data.members.length})
        </button>
      </nav>
    </div>

    <!-- Tab Content -->
    {#if activeTab === 'overview'}
      <div class="grid md:grid-cols-2 gap-6">
        <!-- Recent Datasets -->
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-gray-900">Recent Datasets</h3>
            <a href="/dashboard/projects/{data.project.id}/datasets" class="text-sm text-primary-600 hover:text-primary-700">
              View all →
            </a>
          </div>
          {#if data.datasets.length === 0}
            <p class="text-gray-500 text-center py-8">No datasets yet</p>
          {:else}
            <div class="space-y-3">
              {#each data.datasets.slice(0, 5) as dataset}
                <a href="/dashboard/projects/{data.project.id}/datasets/{dataset.id}" class="block p-3 hover:bg-gray-50 rounded-lg transition-colors">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-gray-900">{dataset.name}</p>
                      <p class="text-sm text-gray-500">{dataset.rows_count} rows × {dataset.columns_count} cols</p>
                    </div>
                    <span class="text-xs text-gray-400">{dataset.file_format?.toUpperCase()}</span>
                  </div>
                </a>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Recent Experiments -->
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-gray-900">Recent Experiments</h3>
            <a href="/dashboard/projects/{data.project.id}/experiments" class="text-sm text-primary-600 hover:text-primary-700">
              View all →
            </a>
          </div>
          {#if data.experiments.length === 0}
            <p class="text-gray-500 text-center py-8">No experiments yet</p>
          {:else}
            <div class="space-y-3">
              {#each data.experiments.slice(0, 5) as experiment}
                <a href="/dashboard/projects/{data.project.id}/experiments/{experiment.id}" class="block p-3 hover:bg-gray-50 rounded-lg transition-colors">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-gray-900">{experiment.name || experiment.algorithm}</p>
                      <p class="text-sm text-gray-500">{experiment.model_type} - {experiment.algorithm}</p>
                    </div>
                    <span class="badge badge-{experiment.status === 'completed' ? 'success' : experiment.status === 'failed' ? 'error' : 'warning'}">
                      {experiment.status}
                    </span>
                  </div>
                </a>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {:else if activeTab === 'datasets'}
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-gray-900">Datasets</h3>
          <a href="/dashboard/projects/{data.project.id}/datasets/upload" class="btn-primary">
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload Dataset
          </a>
        </div>
        
{#if data.datasets.length === 0}
  <div class="card text-center py-12">
    <p class="text-gray-500">No datasets in this project</p>
  </div>
{:else}
  <div class="grid gap-4">
    {#each data.datasets as dataset}
      <a href="/dashboard/projects/{data.project.id}/datasets/{dataset.id}" class="card hover:shadow-lg transition-shadow">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h4 class="font-bold text-gray-900">{dataset.name}</h4>
              
              <!-- NOUVEAU: Badge de statut -->
              {#if dataset.processing_status === 'completed'}
                <span class="badge badge-success">Ready</span>
              {:else if dataset.processing_status === 'processing'}
                <span class="badge bg-blue-100 text-blue-800">
                  <svg class="animate-spin w-3 h-3 inline mr-1" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing
                </span>
              {:else if dataset.processing_status === 'failed'}
                <span class="badge bg-red-100 text-red-800">Failed</span>
              {:else}
                <span class="badge bg-gray-100 text-gray-800">Pending</span>
              {/if}
            </div>
            
            <p class="text-sm text-gray-600 mb-2">{dataset.filename}</p>
            
            <!-- Stats (seulement si traité) -->
            {#if dataset.processing_status === 'completed' && dataset.rows_count}
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span>{dataset.rows_count.toLocaleString()} rows</span>
                <span>{dataset.columns_count} columns</span>
                <span>{(dataset.file_size / 1024).toFixed(2)} KB</span>
                <span>{dataset.file_format?.toUpperCase()}</span>
                {#if dataset.memory_usage}
                  <span>{dataset.memory_usage.toFixed(2)} MB</span>
                {/if}
              </div>
            {:else}
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span>{(dataset.file_size / 1024).toFixed(2)} KB</span>
                <span>{dataset.file_format?.toUpperCase()}</span>
              </div>
            {/if}
          </div>
          
          <span class="text-xs text-gray-400">
            {new Date(dataset.upload_date).toLocaleDateString()}
          </span>
        </div>
      </a>
    {/each}
  </div>
{/if}
      </div>
    {:else if activeTab === 'experiments'}
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-gray-900">Experiments</h3>
          <a href="/dashboard/projects/{data.project.id}/experiments/new" class="btn-primary">
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            New Experiment
          </a>
        </div>
        
        {#if data.experiments.length === 0}
          <div class="card text-center py-12">
            <p class="text-gray-500">No experiments in this project</p>
          </div>
        {:else}
          <div class="grid gap-4">
            {#each data.experiments as experiment}
              <a href="/dashboard/projects/{data.project.id}/experiments/{experiment.id}" class="card hover:shadow-lg transition-shadow">
                <div class="flex items-start justify-between mb-3">
                  <div class="flex-1">
                    <h4 class="font-bold text-gray-900 mb-1">{experiment.name || `${experiment.algorithm} Experiment`}</h4>
                    <p class="text-sm text-gray-600">{experiment.model_type} - {experiment.algorithm}</p>
                  </div>
                  <span class="badge badge-{experiment.status === 'completed' ? 'success' : experiment.status === 'failed' ? 'error' : 'warning'}">
                    {experiment.status}
                  </span>
                </div>
                <div class="flex items-center justify-between text-sm text-gray-500">
                  <span>Dataset: {experiment.dataset_name}</span>
                  <span>{new Date(experiment.created_at).toLocaleDateString()}</span>
                </div>
              </a>
            {/each}
          </div>
        {/if}
      </div>
    {:else if activeTab === 'members'}
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-gray-900">Project Members</h3>
          {#if data.project.member_role === 'owner' || data.project.member_role === 'editor'}
            <button onclick={() => showAddMemberModal = true} class="btn-primary">
              <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Add Member
            </button>
          {/if}
        </div>
        
        <div class="card">
          <div class="space-y-4">
            {#each data.members as member}
              <div class="flex items-center justify-between p-4 hover:bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
                    <span class="text-sm font-medium text-white">
                      {member.username?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p class="font-medium text-gray-900">{member.username}</p>
                    <p class="text-sm text-gray-500">{member.email}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="badge badge-{member.role === 'owner' ? 'success' : 'info'}">
                    {member.role}
                  </span>
                  {#if data.project.member_role === 'owner' && member.role !== 'owner'}
                    <form method="POST" action="?/removeMember" use:enhance>
                      <input type="hidden" name="member_id" value={member.user_id} />
                      <button type="submit" class="text-red-600 hover:text-red-700">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </form>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<!-- Edit Project Modal -->
{#if showEditModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onclick={(e) => {
    if (e.target === e.currentTarget) showEditModal = false;
  }}>
    <div class="card max-w-md w-full" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold text-gray-900">Edit Project</h3>
        <button onclick={() => showEditModal = false} class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {#if form?.error}
        <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-sm text-red-800">{form.error}</p>
        </div>
      {/if}

      <form method="POST" action="?/updateProject" use:enhance={() => {
        loading = true;
        return async ({ result, update }) => {
          await update();
          loading = false;
          if (result.type === 'success') {
            showEditModal = false;
            invalidateAll();
          }
        };
      }}>
        <div class="space-y-4">
          <div>
            <label for="edit_name" class="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
            <input type="text" id="edit_name" name="name" value={data.project.name} required class="input-field" disabled={loading} />
          </div>

          <div>
            <label for="edit_description" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea id="edit_description" name="description" rows="3" class="input-field resize-none" disabled={loading}>{data.project.description || ''}</textarea>
          </div>

          <div class="flex items-center">
            <input type="checkbox" id="edit_is_public" name="is_public" value="true" checked={data.project.is_public} class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500" disabled={loading} />
            <label for="edit_is_public" class="ml-2 text-sm text-gray-600">Make this project public</label>
          </div>

          <div class="flex space-x-3 pt-4">
            <button type="button" onclick={() => showEditModal = false} class="flex-1 btn-secondary" disabled={loading}>Cancel</button>
            <button type="submit" class="flex-1 btn-primary disabled:opacity-50" disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- Add Member Modal -->
{#if showAddMemberModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onclick={(e) => {
    if (e.target === e.currentTarget) showAddMemberModal = false;
  }}>
    <div class="card max-w-md w-full" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold text-gray-900">Add Member</h3>
        <button onclick={() => showAddMemberModal = false} class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form method="POST" action="?/addMember" use:enhance={() => {
        loading = true;
        return async ({ result, update }) => {
          await update();
          loading = false;
          if (result.type === 'success') {
            showAddMemberModal = false;
            invalidateAll();
          }
        };
      }}>
        <div class="space-y-4">
          <div>
            <label for="member_email" class="block text-sm font-medium text-gray-700 mb-1">User Email *</label>
            <input type="email" id="member_email" name="email" required class="input-field" placeholder="user@example.com" disabled={loading} />
          </div>

          <div>
            <label for="member_role" class="block text-sm font-medium text-gray-700 mb-1">Role *</label>
            <select id="member_role" name="role" required class="input-field" disabled={loading}>
              <option value="viewer">Viewer (Read only)</option>
              <option value="editor">Editor (Can edit)</option>
            </select>
          </div>

          <div class="flex space-x-3 pt-4">
            <button type="button" onclick={() => showAddMemberModal = false} class="flex-1 btn-secondary" disabled={loading}>Cancel</button>
            <button type="submit" class="flex-1 btn-primary disabled:opacity-50" disabled={loading}>
              {loading ? 'Adding...' : 'Add Member'}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- Delete Confirmation -->
{#if showDeleteConfirm}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
    <div class="card max-w-md w-full">
      <h3 class="text-xl font-bold text-gray-900 mb-4">Delete Project</h3>
      <p class="text-gray-600 mb-6">Are you sure you want to delete this project? This action cannot be undone and will delete all datasets and experiments.</p>
      
      <form method="POST" action="?/deleteProject" use:enhance>
        <div class="flex space-x-3">
          <button type="button" onclick={() => showDeleteConfirm = false} class="flex-1 btn-secondary">Cancel</button>
          <button type="submit" class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">Delete Project</button>
        </div>
      </form>
    </div>
  </div>
{/if}