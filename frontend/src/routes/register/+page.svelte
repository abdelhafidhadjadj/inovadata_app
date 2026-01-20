<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';
  
  let { form }: { form: ActionData } = $props();
  let loading = $state(false);
</script>

<svelte:head>
  <title>Register - Data Mining Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4 py-8">
  <div class="max-w-md w-full">
    <!-- Logo & Title -->
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
        <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </div>
      <h1 class="text-3xl font-bold text-gray-900">Create Account</h1>
      <p class="text-gray-600 mt-2">Join the Data Mining Platform today</p>
    </div>

    <!-- Register Form -->
    <div class="card">
      {#if form?.error}
        <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-sm text-red-800">{form.error}</p>
        </div>
      {/if}

      <form method="POST" use:enhance={() => {
        loading = true;
        return async ({ update }) => {
          await update();
          loading = false;
        };
      }}>
        <div class="space-y-4">
          <!-- Full Name -->
          <div>
            <label for="full_name" class="block text-sm font-medium text-gray-700 mb-1">
              Full Name (Optional)
            </label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={form?.fullName || ''}
              class="input-field"
              placeholder="Enter your full name"
              disabled={loading}
            />
          </div>

          <!-- Username -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={form?.username || ''}
              required
              pattern="[a-zA-Z0-9_]+"
              minlength="3"
              class="input-field"
              placeholder="Choose a username"
              disabled={loading}
            />
            <p class="mt-1 text-xs text-gray-500">
              At least 3 characters, letters, numbers, and underscores only
            </p>
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={form?.email || ''}
              required
              class="input-field"
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              required
              minlength="8"
              class="input-field"
              placeholder="Create a strong password"
              disabled={loading}
            />
            <p class="mt-1 text-xs text-gray-500">
              At least 8 characters
            </p>
          </div>

          <!-- Confirm Password -->
          <div>
            <label for="confirm_password" class="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              required
              minlength="8"
              class="input-field"
              placeholder="Confirm your password"
              disabled={loading}
            />
          </div>

          <!-- Terms & Conditions -->
          <div class="flex items-start">
            <input
              type="checkbox"
              id="terms"
              required
              class="w-4 h-4 mt-1 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <label for="terms" class="ml-2 text-sm text-gray-600">
              I agree to the <a href="/terms" class="text-primary-600 hover:text-primary-700">Terms of Service</a> and <a href="/privacy" class="text-primary-600 hover:text-primary-700">Privacy Policy</a>
            </label>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            disabled={loading}
            class="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {#if loading}
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating account...
            {:else}
              Create Account
            {/if}
          </button>
        </div>
      </form>

      <!-- Login Link -->
      <div class="mt-6 text-center">
        <p class="text-sm text-gray-600">
          Already have an account?
          <a href="/login" class="text-primary-600 hover:text-primary-700 font-medium">
            Sign in instead
          </a>
        </p>
      </div>
    </div>
  </div>
</div>