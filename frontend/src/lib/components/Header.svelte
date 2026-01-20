<script lang="ts">
  import type { User } from '$lib/server/auth';
  
  let { user }: { user?: User } = $props();
  let showUserMenu = $state(false);
</script>

<header class="bg-white border-b sticky top-0 z-40">
  <div class="container mx-auto px-4">
    <div class="flex items-center justify-between h-16">
      <!-- Logo -->
      <a href={user ? '/dashboard' : '/'} class="flex items-center space-x-2">
        <div class="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <span class="text-xl font-bold text-gray-900">DataMine</span>
      </a>

      <!-- Navigation -->
      {#if user}
        <nav class="hidden md:flex items-center space-x-6">
          <a href="/dashboard" class="text-gray-600 hover:text-gray-900 font-medium transition-colors">
            Dashboard
          </a>
          <a href="/dashboard/projects" class="text-gray-600 hover:text-gray-900 font-medium transition-colors">
            All Projects
          </a>
        </nav>
      {/if}

      <!-- User Menu -->
      <div class="flex items-center space-x-4">
        {#if user}
          <div class="relative">
            <button
              onclick={() => showUserMenu = !showUserMenu}
              class="flex items-center space-x-2 hover:bg-gray-50 rounded-lg px-3 py-2 transition-colors"
            >
              <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <span class="text-sm font-medium text-white">
                  {user.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <span class="hidden md:block text-sm font-medium text-gray-700">
                {user.username}
              </span>
              <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {#if showUserMenu}
              <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                <div class="px-4 py-2 border-b border-gray-100">
                  <p class="text-sm font-medium text-gray-900">{user.username}</p>
                  <p class="text-xs text-gray-500">{user.email}</p>
                </div>
                
                <a href="/dashboard/profile" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Profile
                </a>
                
                <a href="/dashboard/settings" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Settings
                </a>
                
                <div class="border-t border-gray-100 mt-1"></div>
                
                <a href="/logout" class="block px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                  <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Logout
                </a>
              </div>
            {/if}
          </div>
        {:else}
          <a href="/login" class="text-gray-600 hover:text-gray-900 font-medium">
            Sign In
          </a>
          <a href="/register" class="btn-primary">
            Get Started
          </a>
        {/if}
      </div>
    </div>
  </div>
</header>

{#if showUserMenu}
  <div class="fixed inset-0 z-30" onclick={() => showUserMenu = false}></div>
{/if}