<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import MetricsComparison from '$lib/components/ml/MetricsComparison.svelte';

	const projectId = $page.params.id;
	const datasetId = $page.params.datasetId;

	let experiments = $state<any[]>([]);
	let selectedExperiments = $state<number[]>([]);
	let loading = $state(true);

	onMount(async () => {
		await loadExperiments();
	});

	async function loadExperiments() {
		try {
			const res = await fetch(`http://localhost:8001/ml/experiments/list/${datasetId}`);
			if (res.ok) {
				const data = await res.json();
				// Filtrer seulement les expériences complètes
				experiments = data.experiments.filter((exp: any) => exp.status === 'completed');
			}
		} catch (error) {
			console.error('Error loading experiments:', error);
		} finally {
			loading = false;
		}
	}

	function toggleExperiment(id: number) {
		if (selectedExperiments.includes(id)) {
			selectedExperiments = selectedExperiments.filter((expId) => expId !== id);
		} else {
			selectedExperiments = [...selectedExperiments, id];
		}
	}

	function selectAll() {
		selectedExperiments = experiments.map((exp) => exp.id);
	}

	function deselectAll() {
		selectedExperiments = [];
	}

	let selectedExperimentsData = $derived(
		experiments.filter((exp) => selectedExperiments.includes(exp.id))
	);

	function getAlgorithmName(algo: string) {
		const names: any = {
			knn: 'K-Nearest Neighbors',
			decision_tree: 'Decision Tree (CART)',
			c45: 'C4.5 Decision Tree',
			chaid: 'CHAID Decision Tree',
			naive_bayes: 'Naive Bayes',
			neural_network: 'Neural Network (MLP)'
		};
		return names[algo] || algo;
	}
</script>

<svelte:head>
	<title>Compare Experiments - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-7xl mx-auto">
		<!-- Header -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml`)}
				class="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
			>
				← Back to experiments
			</button>

			<h1 class="text-3xl font-bold text-gray-900">Compare Experiments</h1>
			<p class="text-gray-600 mt-1">Select experiments to compare their performance</p>
		</div>

		{#if loading}
			<div class="text-center py-12">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
				<p class="mt-4 text-gray-600">Loading experiments...</p>
			</div>
		{:else if experiments.length === 0}
			<div class="bg-white rounded-lg shadow-sm p-12 text-center">
				<div class="text-gray-400 text-6xl mb-4">📊</div>
				<h3 class="text-xl font-semibold text-gray-900 mb-2">No Completed Experiments</h3>
				<p class="text-gray-600 mb-6">You need at least 2 completed experiments to compare</p>
				<button
					on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/create`)}
					class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
				>
					Create New Experiment
				</button>
			</div>
		{:else}
			<!-- Selection Controls -->
			<div class="bg-white rounded-lg shadow-sm p-4 mb-6">
				<div class="flex justify-between items-center">
					<p class="text-sm text-gray-600">
						{selectedExperiments.length} experiment(s) selected
					</p>
					<div class="space-x-2">
						<button
							on:click={selectAll}
							class="text-sm text-blue-600 hover:text-blue-800 font-medium"
						>
							Select All
						</button>
						<button
							on:click={deselectAll}
							class="text-sm text-gray-600 hover:text-gray-800 font-medium"
						>
							Deselect All
						</button>
					</div>
				</div>
			</div>

			<!-- Experiments List -->
			<div class="bg-white rounded-lg shadow-sm overflow-hidden mb-6">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left">
								<input
									type="checkbox"
									checked={selectedExperiments.length === experiments.length && experiments.length > 0}
									on:change={(e) => (e.currentTarget.checked ? selectAll() : deselectAll())}
									class="w-4 h-4 text-blue-600 rounded"
								/>
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Name
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Algorithm
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Accuracy
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								F1-Score
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Training Time
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each experiments as exp}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4">
									<input
										type="checkbox"
										checked={selectedExperiments.includes(exp.id)}
										on:change={() => toggleExperiment(exp.id)}
										class="w-4 h-4 text-blue-600 rounded"
									/>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
									{exp.name}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{getAlgorithmName(exp.algorithm)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{exp.metrics?.accuracy
										? `${(exp.metrics.accuracy * 100).toFixed(2)}%`
										: '—'}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{exp.metrics?.f1_score
										? `${(exp.metrics.f1_score * 100).toFixed(2)}%`
										: '—'}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{exp.training_time ? `${exp.training_time.toFixed(4)}s` : '—'}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Comparison Chart -->
			{#if selectedExperimentsData.length > 0}
				<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
					<h2 class="text-xl font-bold text-gray-900 mb-4">Performance Comparison</h2>
					<MetricsComparison experiments={selectedExperimentsData} />
				</div>

				<!-- Detailed Comparison Table -->
				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-bold text-gray-900 mb-4">Detailed Metrics</h2>
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Experiment
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Algorithm
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Accuracy
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Precision
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Recall
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										F1-Score
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
										Training Time
									</th>
								</tr>
							</thead>
							<tbody class="bg-white divide-y divide-gray-200">
								{#each selectedExperimentsData as exp}
									<tr class="hover:bg-gray-50">
										<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
											{exp.name}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
											{getAlgorithmName(exp.algorithm)}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
											{(exp.metrics.accuracy * 100).toFixed(2)}%
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm">
											{(exp.metrics.precision * 100).toFixed(2)}%
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm">
											{(exp.metrics.recall * 100).toFixed(2)}%
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm">
											{(exp.metrics.f1_score * 100).toFixed(2)}%
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm">
											{exp.training_time.toFixed(4)}s
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="bg-white rounded-lg shadow-sm p-12 text-center">
					<div class="text-gray-400 text-6xl mb-4">📊</div>
					<h3 class="text-xl font-semibold text-gray-900 mb-2">Select Experiments to Compare</h3>
					<p class="text-gray-600">Check the boxes above to select experiments for comparison</p>
				</div>
			{/if}
		{/if}
	</div>
</div>