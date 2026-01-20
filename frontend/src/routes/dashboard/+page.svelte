<script lang="ts">
  import { enhance } from '$app/forms';
  import type { PageData, ActionData } from './$types';
  import Header from '$lib/components/Header.svelte';
  
  let { data, form }: { data: PageData; form: ActionData } = $props();
  let showCreateModal = $state(false);
  let loading = $state(false);
</script>

<svelte:head>
  <title>Dashboard - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
  <Header user={data.user} />
  
  <main class="container mx-auto px-4 py-8">
    <!-- Welcome Section -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Welcome back, {data.user?.full_name || data.user?.username}! 👋
      </h1>
      <p class="text-gray-600">
        Manage your data mining projects and experiments
      </p>
    </div>

    <!-- Stats Cards -->
    <div class="grid md:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">Total Projects</p>
            <p class="text-3xl font-bold text-gray-900">{data.projects?.length || 0}</p>
          </div>
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">Owner</p>
            <p class="text-3xl font-bold text-gray-900">
              {data.projects?.filter(p => p.member_role === 'owner').length || 0}
            </p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">Shared</p>
            <p class="text-3xl font-bold text-gray-900">
              {data.projects?.filter(p => p.member_role !== 'owner').length || 0}
            </p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">Active</p>
            <p class="text-3xl font-bold text-gray-900">
              {data.projects?.filter(p => p.status === 'active').length || 0}
            </p>
          </div>
          <div class="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Projects Section -->
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900">Your Projects</h2>
      <button
        onclick={() => showCreateModal = true}
        class="btn-primary"
      >
        <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Project
      </button>
    </div>

    {#if !data.projects || data.projects.length === 0}
      <div class="card text-center py-12">
        <div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">No projects yet</h3>
        <p class="text-gray-600 mb-6">Create your first project to get started</p>
        <button onclick={() => showCreateModal = true} class="btn-primary">
          Create Project
        </button>
      </div>
    {:else}
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each data.projects || [] as project}
          <a href="/dashboard/projects/{project.id}" class="card hover:shadow-lg transition-shadow group">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <span class="badge badge-{project.member_role === 'owner' ? 'success' : 'info'}">
                {project.member_role}
              </span>
            </div>
            
            <h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
              {project.name}
            </h3>
            
            {#if project.description}
              <p class="text-sm text-gray-600 mb-4 line-clamp-2">
                {project.description}
              </p>
            {/if}
            
            <div class="flex items-center justify-between text-sm text-gray-500">
              <span>By {project.owner_username}</span>
              <span>{new Date(project.created_at).toLocaleDateString()}</span>
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

      <form method="POST" action="?/createProject" use:enhance={() => {
        loading = true;
        return async ({ result, update }) => {
          await update();
          loading = false;
          if (result.type === 'success') {
            showCreateModal = false;
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
              class="input-field"
              placeholder="My Data Science Project"
              disabled={loading}
            />
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
              class="flex-1 btn-primary disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
{/if}