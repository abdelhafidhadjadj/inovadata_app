<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const projectId = $page.params.id;
	const datasetId = $page.params.datasetId;

	let experiments: any[] = [];
	let loading = true;
	let dataset: any = null;

	onMount(async () => {
		await loadDataset();
		await loadExperiments();
	});

	async function loadDataset() {
		try {
			const res = await fetch(`http://localhost:8001/datasets/${datasetId}`);
			if (res.ok) {
				dataset = await res.json();
			}
		} catch (error) {
			console.error('Erreur chargement dataset:', error);
		}
	}

	async function loadExperiments() {
		try {
			const res = await fetch(`http://localhost:8001/ml/experiments/list/${datasetId}`);
			if (res.ok) {
				const data = await res.json();
				experiments = data.experiments || [];
			}
		} catch (error) {
			console.error('Erreur chargement expériences:', error);
		} finally {
			loading = false;
		}
	}

	function getStatusBadge(status: string) {
		const badges: any = {
			pending: 'bg-gray-100 text-gray-800',
			training: 'bg-blue-100 text-blue-800',
			completed: 'bg-green-100 text-green-800',
			failed: 'bg-red-100 text-red-800'
		};
		return badges[status] || 'bg-gray-100 text-gray-800';
	}

	function getStatusText(status: string) {
		const texts: any = {
			pending: 'En attente',
			training: 'Entraînement...',
			completed: 'Terminé',
			failed: 'Échoué'
		};
		return texts[status] || status;
	}
</script>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-7xl mx-auto">
		<!-- Header -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}`)}
				class="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
			>
				← Retour au dataset
			</button>

			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Expériences ML</h1>
					{#if dataset}
						<p class="text-gray-600 mt-1">Dataset: {dataset.name}</p>
					{/if}
				</div>
                	{#if experiments.filter((exp) => exp.status === 'completed').length > 1}
                	<button
                		on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/compare`)}
                		class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                	>
                		📊 Compare Experiments
                	</button>
                {/if}
				<button
					on:click={() =>
						goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/create`)}
					class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
				>
					+ Nouvelle expérience
				</button>
			</div>
		</div>

		<!-- Liste des expériences -->
		{#if loading}
			<div class="text-center py-12">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
				<p class="mt-4 text-gray-600">Chargement...</p>
			</div>
		{:else if experiments.length === 0}
			<div class="bg-white rounded-lg shadow-sm p-12 text-center">
				<div class="text-gray-400 text-6xl mb-4">🤖</div>
				<h3 class="text-xl font-semibold text-gray-900 mb-2">Aucune expérience ML</h3>
				<p class="text-gray-600 mb-6">Créez votre première expérience d'entraînement</p>
				<button
					on:click={() =>
						goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/create`)}
					class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
				>
					+ Créer une expérience
				</button>
			</div>
		{:else}
			<div class="bg-white rounded-lg shadow-sm overflow-hidden">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Nom
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Algorithme
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Statut
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Accuracy
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Temps
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Date
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
								Actions
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each experiments as exp}
							<tr class="hover:bg-gray-50 cursor-pointer">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm font-medium text-gray-900">{exp.name}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">
										{exp.algorithm === 'knn' ? 'K-Nearest Neighbors' : exp.algorithm}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span
										class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusBadge(
											exp.status
										)}"
									>
										{getStatusText(exp.status)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">
										{#if exp.metrics?.accuracy}
											{(exp.metrics.accuracy * 100).toFixed(2)}%
										{:else}
											-
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">
										{#if exp.training_time}
											{exp.training_time.toFixed(8)}s
										{:else}
											-
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-500">
										{new Date(exp.created_at).toLocaleDateString('fr-FR')}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<button
										on:click={() =>
											goto(
												`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/${exp.id}`
											)}
										class="text-blue-600 hover:text-blue-900 mr-3"
									>
										Voir
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>