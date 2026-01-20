<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const projectId = $page.params.id;
	const datasetId = $page.params.datasetId;

	let dataset: any = null;
	let columns: any[] = [];
	let algorithms: any[] = [];
	let selectedAlgorithm = '';
	let algorithmParams: any = {};

	// Form data
	let experimentName = '';
	let description = '';
	let targetColumn = '';
	let selectedFeatures: string[] = [];
	let trainRatio = 0.8;
	let randomSeed = 42;
	let hyperparameters: any = {};

	let loading = true;
	let creating = false;
	let error = '';

	onMount(async () => {
		await loadDataset();
		await loadAlgorithms();
	});

	async function loadDataset() {
		try {
			const res = await fetch(`http://localhost:8001/datasets/${datasetId}`);
			if (res.ok) {
				dataset = await res.json();
				columns = dataset.columns_info || [];
			}
		} catch (err) {
			error = 'Erreur chargement dataset';
			console.error(err);
		} finally {
			loading = false;
		}
	}

	async function loadAlgorithms() {
		try {
			const res = await fetch('http://localhost:8001/ml/algorithms');
			if (res.ok) {
				const data = await res.json();
				algorithms = data.algorithms || [];
			}
		} catch (err) {
			console.error('Erreur chargement algorithmes:', err);
		}
	}

	async function onAlgorithmChange() {
		if (!selectedAlgorithm) return;

		try {
			const res = await fetch(`http://localhost:8001/ml/algorithms/${selectedAlgorithm}/params`);
			if (res.ok) {
				const data = await res.json();
				algorithmParams = data.parameters || {};

				// Initialiser les hyperparamètres avec les valeurs par défaut
				hyperparameters = {};
				for (const [key, config] of Object.entries(algorithmParams)) {
					hyperparameters[key] = (config as any).default;
				}
			}
		} catch (err) {
			console.error('Erreur chargement paramètres:', err);
		}
	}

	function toggleFeature(columnName: string) {
		if (selectedFeatures.includes(columnName)) {
			selectedFeatures = selectedFeatures.filter((f) => f !== columnName);
		} else {
			selectedFeatures = [...selectedFeatures, columnName];
		}
	}

	function selectAllFeatures() {
		selectedFeatures = columns.filter((col) => col.name !== targetColumn).map((col) => col.name);
	}

	function deselectAllFeatures() {
		selectedFeatures = [];
	}

	async function createExperiment() {
		// Validation
		if (!experimentName.trim()) {
			error = 'Veuillez entrer un nom pour l\'expérience';
			return;
		}

		if (!selectedAlgorithm) {
			error = 'Veuillez sélectionner un algorithme';
			return;
		}

		if (!targetColumn) {
			error = 'Veuillez sélectionner une colonne target';
			return;
		}

		if (selectedFeatures.length === 0) {
			error = 'Veuillez sélectionner au moins une feature';
			return;
		}

		creating = true;
		error = '';

		try {
			const res = await fetch('http://localhost:8001/ml/experiments/create', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: experimentName,
					description: description || null,
					project_id: parseInt(projectId),
					dataset_id: parseInt(datasetId),
					algorithm: selectedAlgorithm,
					hyperparameters: hyperparameters,
					target_column: targetColumn,
					feature_columns: selectedFeatures,
					train_ratio: trainRatio,
					random_seed: randomSeed
				})
			});

			if (res.ok) {
				const experiment = await res.json();

				// Lancer l'entraînement
				await fetch(`http://localhost:8001/ml/experiments/${experiment.id}/train`, {
					method: 'POST'
				});

				// Rediriger vers la liste
				goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml`);
			} else {
				const data = await res.json();
				error = data.detail || 'Erreur lors de la création';
			}
		} catch (err) {
			error = 'Erreur réseau';
			console.error(err);
		} finally {
			creating = false;
		}
	}
</script>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-4xl mx-auto">
		<!-- Header -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml`)}
				class="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
			>
				← Retour aux expériences
			</button>

			<h1 class="text-3xl font-bold text-gray-900">Nouvelle expérience ML</h1>
			{#if dataset}
				<p class="text-gray-600 mt-1">Dataset: {dataset.name}</p>
			{/if}
		</div>

		{#if loading}
			<div class="text-center py-12">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			</div>
		{:else}
			<div class="bg-white rounded-lg shadow-sm p-6">
				{#if error}
					<div class="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
						{error}
					</div>
				{/if}

				<!-- Informations générales -->
				<div class="mb-6">
					<h2 class="text-lg font-semibold mb-4">Informations générales</h2>

					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								Nom de l'expérience *
							</label>
							<input
								type="text"
								bind:value={experimentName}
								placeholder="Ex: KNN - Premier test"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								Description (optionnel)
							</label>
							<textarea
								bind:value={description}
								placeholder="Objectif de cette expérience..."
								rows="3"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							></textarea>
						</div>
					</div>
				</div>

				<hr class="my-6" />

				<!-- Algorithme -->
				<div class="mb-6">
					<h2 class="text-lg font-semibold mb-4">Algorithme</h2>

					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">
							Choisir un algorithme *
						</label>
						<select
							bind:value={selectedAlgorithm}
							on:change={onAlgorithmChange}
							class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="">-- Sélectionner --</option>
							{#each algorithms as algo}
								<option value={algo.id}>{algo.name}</option>
							{/each}
						</select>
					</div>

					<!-- Hyperparamètres -->
					{#if selectedAlgorithm && Object.keys(algorithmParams).length > 0}
						<div class="mt-4 p-4 bg-gray-50 rounded-lg">
							<h3 class="text-sm font-medium text-gray-700 mb-3">Hyperparamètres</h3>

							<div class="space-y-3">
								{#each Object.entries(algorithmParams) as [paramName, paramConfig]}
									<div>
										<label class="block text-sm text-gray-600 mb-1">
											{paramName.replace(/_/g, ' ')}
										</label>

										{#if (paramConfig as any).type === 'int'}
											<input
												type="number"
												bind:value={hyperparameters[paramName]}
												min={(paramConfig as any).min}
												max={(paramConfig as any).max}
												class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
											/>
										{:else if (paramConfig as any).type === 'select'}
											<select
												bind:value={hyperparameters[paramName]}
												class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
											>
												{#each (paramConfig as any).options as option}
													<option value={option}>{option}</option>
												{/each}
											</select>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>

				<hr class="my-6" />

				<!-- Target et Features -->
				<div class="mb-6">
					<h2 class="text-lg font-semibold mb-4">Variables</h2>

					<!-- Target Column -->
					<div class="mb-4">
						<label class="block text-sm font-medium text-gray-700 mb-1">
							Colonne à prédire (target) *
						</label>
						<select
							bind:value={targetColumn}
							class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="">-- Sélectionner --</option>
							{#each columns as col}
								<option value={col.name}>{col.name} ({col.dtype})</option>
							{/each}
						</select>
					</div>

					<!-- Features -->
					<div>
						<div class="flex justify-between items-center mb-2">
							<label class="block text-sm font-medium text-gray-700">
								Features (variables explicatives) *
							</label>
							<div class="space-x-2">
								<button
									type="button"
									on:click={selectAllFeatures}
									class="text-sm text-blue-600 hover:text-blue-800"
								>
									Tout sélectionner
								</button>
								<button
									type="button"
									on:click={deselectAllFeatures}
									class="text-sm text-gray-600 hover:text-gray-800"
								>
									Tout désélectionner
								</button>
							</div>
						</div>

						<div class="border border-gray-300 rounded-lg p-4 max-h-64 overflow-y-auto">
							{#each columns.filter((col) => col.name !== targetColumn) as col}
								<label class="flex items-center space-x-2 py-2 hover:bg-gray-50 cursor-pointer">
									<input
										type="checkbox"
										checked={selectedFeatures.includes(col.name)}
										on:change={() => toggleFeature(col.name)}
										class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
									/>
									<span class="text-sm text-gray-900">{col.name}</span>
									<span class="text-xs text-gray-500">({col.dtype})</span>
								</label>
							{/each}
						</div>

						<p class="text-sm text-gray-600 mt-2">
							{selectedFeatures.length} feature(s) sélectionnée(s)
						</p>
					</div>
				</div>

				<hr class="my-6" />

				<!-- Configuration Train/Test -->
				<div class="mb-6">
					<h2 class="text-lg font-semibold mb-4">Configuration Train/Test Split</h2>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								Ratio Train ({(trainRatio * 100).toFixed(0)}%)
							</label>
							<input
								type="range"
								bind:value={trainRatio}
								min="0.5"
								max="0.9"
								step="0.05"
								class="w-full"
							/>
							<div class="flex justify-between text-xs text-gray-500 mt-1">
								<span>50%</span>
								<span>90%</span>
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Random Seed</label>
							<input
								type="number"
								bind:value={randomSeed}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
					</div>
				</div>

				<!-- Actions -->
				<div class="flex justify-end gap-4 mt-8">
					<button
						type="button"
						on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml`)}
						class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
					>
						Annuler
					</button>

					<button
						on:click={createExperiment}
						disabled={creating}
						class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{creating ? 'Création en cours...' : 'Créer et entraîner'}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>