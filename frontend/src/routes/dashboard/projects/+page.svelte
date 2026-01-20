<script lang="ts">
  import { enhance } from '$app/forms';
  import { goto, invalidateAll } from '$app/navigation';
  import type { PageData, ActionData } from './$types';
  import Header from '$lib/components/Header.svelte';
  
  let { data, form }: { data: PageData; form: ActionData } = $props();
  
  let showCreateModal = $state(false);
  let loading = $state(false);
  let searchQuery = $state('');
  let filterRole = $state<'all' | 'owner' | 'shared'>('all');
  let sortBy = $state<'name' | 'date' | 'status'>('date');

  // Filtered and sorted projects
  let filteredProjects = $derived.by(() => {
    let result = data.projects;

    // Filter by role
    if (filterRole === 'owner') {
      result = data.ownedProjects;
    } else if (filterRole === 'shared') {
      result = data.sharedProjects;
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(p => 
        p.name.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query) ||
        p.owner_username.toLowerCase().includes(query)
      );
    }

    // Sort
    result = [...result].sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'date') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else if (sortBy === 'status') {
        return a.status.localeCompare(b.status);
      }
      return 0;
    });

    return result;
  });
</script>

<svelte:head>
  <title>Projects - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <Header user={data.user} />
  
  <main class="container mx-auto px-4 py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Projects</h1>
          <p class="text-gray-600 mt-1">Manage and organize your data mining projects</p>
        </div>
        <button onclick={() => showCreateModal = true} class="btn-primary">
          <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      <!-- Stats Cards -->
      <div class="grid md:grid-cols-4 gap-4 mb-6">
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 mb-1">Total Projects</p>
              <p class="text-2xl font-bold text-gray-900">{data.projects.length}</p>
            </div>
            <div class="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 mb-1">Owned</p>
              <p class="text-2xl font-bold text-gray-900">{data.ownedProjects.length}</p>
            </div>
            <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 mb-1">Shared with me</p>
              <p class="text-2xl font-bold text-gray-900">{data.sharedProjects.length}</p>
            </div>
            <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-600 mb-1">Active</p>
              <p class="text-2xl font-bold text-gray-900">
                {data.projects.filter(p => p.status === 'active').length}
              </p>
            </div>
            <div class="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="card mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <!-- Search -->
        <div class="flex-1">
          <div class="relative">
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Search projects..."
              class="input-field pl-10"
            />
            <svg class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <!-- Filter by Role -->
        <div>
          <select bind:value={filterRole} class="input-field">
            <option value="all">All Projects</option>
            <option value="owner">Owned by me</option>
            <option value="shared">Shared with me</option>
          </select>
        </div>

        <!-- Sort -->
        <div>
          <select bind:value={sortBy} class="input-field">
            <option value="date">Sort by Date</option>
            <option value="name">Sort by Name</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Projects Grid -->
    {#if filteredProjects.length === 0}
      <div class="card text-center py-16">
        <div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">
          {searchQuery ? 'No projects found' : 'No projects yet'}
        </h3>
        <p class="text-gray-600 mb-6">
          {searchQuery ? 'Try adjusting your search or filters' : 'Create your first project to get started'}
        </p>
        {#if !searchQuery}
          <button onclick={() => showCreateModal = true} class="btn-primary">
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Create Project
          </button>
        {/if}
      </div>
    {:else}
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each filteredProjects as project (project.id)}
          <a 
            href="/dashboard/projects/{project.id}" 
            class="card hover:shadow-lg transition-all duration-200 group hover:-translate-y-1"
          >
            <!-- Project Icon & Badge -->
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div class="flex gap-2">
                <span class="badge badge-{project.member_role === 'owner' ? 'success' : 'info'}">
                  {project.member_role}
                </span>
                {#if project.is_public}
                  <span class="badge bg-purple-100 text-purple-800">Public</span>
                {/if}
              </div>
            </div>
            
            <!-- Project Info -->
            <h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
              {project.name}
            </h3>
            
            {#if project.description}
              <p class="text-sm text-gray-600 mb-4 line-clamp-2">
                {project.description}
              </p>
            {:else}
              <p class="text-sm text-gray-400 mb-4 italic">No description</p>
            {/if}
            
            <!-- Project Meta -->
            <div class="pt-4 border-t border-gray-100">
              <div class="flex items-center justify-between text-sm">
                <div class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {project.owner_username}
                </div>
                <div class="text-gray-400">
                  {new Date(project.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </a>
        {/each}
      </div>
    {/if}
  </main>
</div>

<!-- Create Project Modal -->
{#if showCreateModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onclick={(e) => {
    if (e.target === e.currentTarget) showCreateModal = false;
  }}>
    <div class="card max-w-md w-full" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold text-gray-900">Create New Project</h3>
        <button
          onclick={() => showCreateModal = false}
          class="text-gray-400 hover:text-gray-600"
        >
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

      {#if form?.success}
        <div class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p class="text-sm text-green-800">{form.message}</p>
        </div>
      {/if}

      <form method="POST" action="?/createProject" use:enhance={() => {
        loading = true;
        return async ({ result, update }) => {
          await update();
          loading = false;
          if (result.type === 'success') {
            showCreateModal = false;
            await invalidateAll();
            // Navigate to the new project if we have the ID
            if (result.data?.projectId) {
              goto(`/dashboard/projects/${result.data.projectId}`);
            }
          }
        };
      }}>
        <div class="space-y-4">
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              minlength="3"
              class="input-field"
              placeholder="My Data Science Project"
              disabled={loading}
            />
            <p class="mt-1 text-xs text-gray-500">At least 3 characters</p>
          </div>

          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows="3"
              class="input-field resize-none"
              placeholder="What is this project about?"
              disabled={loading}
            ></textarea>
          </div>

          <div class="flex items-center">
            <input
              type="checkbox"
              id="is_public"
              name="is_public"
              value="true"
              class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              disabled={loading}
            />
            <label for="is_public" class="ml-2 text-sm text-gray-600">
              Make this project public
            </label>
          </div>

          <div class="flex space-x-3 pt-4">
            <button
              type="button"
              onclick={() => showCreateModal = false}
              class="flex-1 btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              class="flex-1 btn-primary disabled:opacity-50 flex items-center justify-center"
              disabled={loading}
            >
              {#if loading}
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              {:else}
                Create Project
              {/if}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
{/if}