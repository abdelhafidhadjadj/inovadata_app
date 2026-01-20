<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';
  
  let { data }: { data: PageData } = $props();
</script>

<svelte:head>
  <title>Data Mining & Machine Learning Platform</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50">
  <!-- Header -->
  <header class="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
    <div class="container mx-auto px-4 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <span class="text-xl font-bold text-gray-900">DataMine</span>
        </div>
        
        <nav class="flex items-center space-x-4">
          {#if data.user}
            <a href="/dashboard" class="btn-primary">
              Go to Dashboard
            </a>
          {:else}
            <a href="/login" class="text-gray-600 hover:text-gray-900 font-medium">
              Sign In
            </a>
            <a href="/register" class="btn-primary">
              Get Started
            </a>
          {/if}
        </nav>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="container mx-auto px-4 py-20">
    <div class="max-w-4xl mx-auto text-center">
      <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
        Data Mining & Machine Learning
        <span class="text-primary-600">Made Simple</span>
      </h1>
      <p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Upload your data, preprocess it, train machine learning models, and visualize results—all in one powerful platform.
      </p>
      <div class="flex items-center justify-center space-x-4">
        {#if data.user}
          <a href="/dashboard" class="btn-primary text-lg px-8 py-3">
            Open Dashboard →
          </a>
        {:else}
          <a href="/register" class="btn-primary text-lg px-8 py-3">
            Start Free →
          </a>
          <a href="/login" class="btn-secondary text-lg px-8 py-3">
            Sign In
          </a>
        {/if}
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="container mx-auto px-4 py-20">
    <div class="max-w-6xl mx-auto">
      <h2 class="text-3xl font-bold text-center text-gray-900 mb-12">
        Everything You Need for Data Science
      </h2>
      
      <div class="grid md:grid-cols-3 gap-8">
        <!-- Feature 1 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Easy Data Upload</h3>
          <p class="text-gray-600">
            Support for CSV, JSON, and ARFF formats with automatic metadata extraction and validation.
          </p>
        </div>

        <!-- Feature 2 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Smart Preprocessing</h3>
          <p class="text-gray-600">
            Handle missing values, normalize data, detect outliers with intelligent preprocessing tools.
          </p>
        </div>

        <!-- Feature 3 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">ML Algorithms</h3>
          <p class="text-gray-600">
            Train models with KNN, Naive Bayes, Decision Trees, Neural Networks, and Linear Regression.
          </p>
        </div>

        <!-- Feature 4 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Rich Visualizations</h3>
          <p class="text-gray-600">
            Create interactive charts, heatmaps, scatter plots, and more with Plotly integration.
          </p>
        </div>

        <!-- Feature 5 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Team Collaboration</h3>
          <p class="text-gray-600">
            Share projects with team members and collaborate in real-time with role-based access.
          </p>
        </div>

        <!-- Feature 6 -->
        <div class="card hover:shadow-lg transition-shadow">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Experiment Tracking</h3>
          <p class="text-gray-600">
            Track and compare multiple experiments with detailed metrics and performance analysis.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="container mx-auto px-4 py-20">
    <div class="max-w-4xl mx-auto text-center card bg-gradient-to-r from-primary-600 to-primary-700 text-white">
      <h2 class="text-3xl font-bold mb-4">Ready to Start?</h2>
      <p class="text-xl mb-8 text-primary-50">
        Join thousands of data scientists using our platform to build better models.
      </p>
      {#if data.user}
        <a href="/dashboard" class="inline-block px-8 py-3 bg-white text-primary-600 rounded-lg font-medium hover:bg-gray-100 transition-colors">
          Go to Dashboard →
        </a>
      {:else}
        <a href="/register" class="inline-block px-8 py-3 bg-white text-primary-600 rounded-lg font-medium hover:bg-gray-100 transition-colors">
          Create Free Account →
        </a>
      {/if}
    </div>
  </section>

  <!-- Footer -->
  <footer class="border-t bg-white">
    <div class="container mx-auto px-4 py-8">
      <div class="text-center text-gray-600">
        <p>&copy; 2024 DataMine Platform. All rights reserved.</p>
      </div>
    </div>
  </footer>
</div>