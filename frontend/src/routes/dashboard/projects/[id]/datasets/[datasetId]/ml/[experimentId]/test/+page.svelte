<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const projectId = $page.params.id;
	const datasetId = $page.params.datasetId;
	const experimentId = $page.params.experimentId;

	// State
	let experiment = $state<any>(null);
	let loading = $state(true);
	let predicting = $state(false);
	let error = $state('');
	let inputData = $state<Record<string, string>>({});
	let predictions = $state<any>(null);
	let csvFile = $state<File | null>(null);
	let batchPredictions = $state<any>(null);
	let testMode = $state<'single' | 'batch'>('single');

	onMount(async () => {
		await loadExperiment();
	});

	async function loadExperiment() {
		try {
			console.log('🔍 Fetching experiment:', experimentId);
			const response = await fetch(`http://localhost:8001/ml/experiments/${experimentId}`);
			console.log('📥 Response status:', response.status);

			if (response.ok) {
				const data = await response.json();
				console.log('📦 Experiment data:', data);
				experiment = data;

				// Parser feature_columns si nécessaire
				if (experiment?.feature_columns) {
					let columns = experiment.feature_columns;
					console.log('🎯 Feature columns raw:', columns, 'Type:', typeof columns);

					// Si c'est une string JSON, parser
					if (typeof columns === 'string') {
						try {
							columns = JSON.parse(columns);
							console.log('✅ Parsed feature columns:', columns);
						} catch (e) {
							console.error('❌ Error parsing feature_columns:', e);
							error = 'Invalid feature columns format';
							loading = false;
							return;
						}
					}

					// S'assurer que c'est un array
					if (Array.isArray(columns)) {
						console.log('✅ Initializing input fields for columns:', columns);
						const initialData: Record<string, string> = {};
						columns.forEach((col: string) => {
							initialData[col] = '';
						});
						inputData = initialData;
						console.log('✅ Input data initialized:', inputData);
					} else {
						console.error('❌ Feature columns is not an array:', columns);
						error = 'Feature columns is not an array';
					}
				} else {
					console.error('❌ No feature columns found in experiment');
					error = 'No feature columns found';
				}
			} else {
				error = 'Experiment not found';
				console.error('❌ Experiment not found, status:', response.status);
			}
		} catch (err) {
			console.error('❌ Error loading experiment:', err);
			error = 'Failed to load experiment';
		} finally {
			loading = false;
			console.log('✅ Loading finished. Has experiment:', !!experiment);
		}
	}

	// Helper pour obtenir les colonnes de features de manière sûre
	function getFeatureColumns(): string[] {
		if (!experiment?.feature_columns) {
			console.log('⚠️ No feature_columns in experiment');
			return [];
		}

		let columns = experiment.feature_columns;

		if (typeof columns === 'string') {
			try {
				columns = JSON.parse(columns);
			} catch {
				console.error('⚠️ Could not parse feature_columns string');
				return [];
			}
		}

		return Array.isArray(columns) ? columns : [];
	}

	async function makePrediction() {
		if (!validateInput()) return;

		predicting = true;
		error = '';
		predictions = null;

		try {
			const numericData: Record<string, number> = {};
			for (const [key, value] of Object.entries(inputData)) {
				numericData[key] = parseFloat(value);
			}

			console.log('🚀 Making prediction with data:', numericData);

			const response = await fetch(
				`http://localhost:8001/ml/experiments/${experimentId}/predict`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ data: [numericData] })
				}
			);

			if (response.ok) {
				predictions = await response.json();
				console.log('✅ Prediction result:', predictions);
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Prediction failed';
				console.error('❌ Prediction failed:', errorData);
			}
		} catch (err) {
			console.error('❌ Prediction error:', err);
			error = 'Network error during prediction';
		} finally {
			predicting = false;
		}
	}

	async function makeBatchPrediction() {
		if (!csvFile) {
			error = 'Please select a CSV file';
			return;
		}

		predicting = true;
		error = '';
		batchPredictions = null;

		try {
			const text = await csvFile.text();
			const rows = text.trim().split('\n');

			if (rows.length < 2) {
				error = 'CSV file must contain headers and at least one data row';
				predicting = false;
				return;
			}

			const headers = rows[0].split(',').map((h) => h.trim());
			const featureCols = getFeatureColumns();

			console.log('📊 CSV headers:', headers);
			console.log('🎯 Required columns:', featureCols);

			const missingCols = featureCols.filter((col: string) => !headers.includes(col));

			if (missingCols.length > 0) {
				error = `Missing required columns: ${missingCols.join(', ')}`;
				predicting = false;
				return;
			}

			const dataRows = rows.slice(1).map((row) => {
				const values = row.split(',');
				const obj: Record<string, number> = {};
				headers.forEach((header, i) => {
					const value = values[i]?.trim();
					obj[header] = parseFloat(value);
				});
				return obj;
			});

			console.log('🚀 Making batch prediction with', dataRows.length, 'rows');

			const response = await fetch(
				`http://localhost:8001/ml/experiments/${experimentId}/predict`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ data: dataRows })
				}
			);

			if (response.ok) {
				batchPredictions = await response.json();
				console.log('✅ Batch prediction result:', batchPredictions);
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Batch prediction failed';
				console.error('❌ Batch prediction failed:', errorData);
			}
		} catch (err) {
			console.error('❌ Batch prediction error:', err);
			error = 'Error processing CSV file';
		} finally {
			predicting = false;
		}
	}

	function validateInput(): boolean {
		const featureCols = getFeatureColumns();

		if (featureCols.length === 0) {
			error = 'No feature columns available';
			return false;
		}

		for (const col of featureCols) {
			const value = inputData[col];

			if (value === '' || value === null || value === undefined) {
				error = `Please fill in all fields. Missing: ${col}`;
				return false;
			}

			if (isNaN(parseFloat(value))) {
				error = `Invalid value for ${col}. Must be a number.`;
				return false;
			}
		}

		error = '';
		return true;
	}

	function resetForm() {
		const featureCols = getFeatureColumns();
		if (featureCols.length > 0) {
			const resetData: Record<string, string> = {};
			featureCols.forEach((col: string) => {
				resetData[col] = '';
			});
			inputData = resetData;
		}
		predictions = null;
		error = '';
	}

	function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			csvFile = target.files[0];
			batchPredictions = null;
			error = '';
		}
	}

	function downloadPredictions() {
		if (!batchPredictions) return;

		const csvContent = ['Index,Prediction']
			.concat(
				batchPredictions.predictions.map((pred: any, i: number) => `${i + 1},${pred}`)
			)
			.join('\n');

		const blob = new Blob([csvContent], { type: 'text/csv' });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `predictions_experiment_${experimentId}.csv`;
		document.body.appendChild(a);
		a.click();
		window.URL.revokeObjectURL(url);
		document.body.removeChild(a);
	}

	function switchToSingle() {
		testMode = 'single';
		error = '';
		predictions = null;
	}

	function switchToBatch() {
		testMode = 'batch';
		error = '';
		batchPredictions = null;
	}

	function navigateBack() {
		goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/${experimentId}`);
	}

	function getAlgorithmName(algo: string) {
		const names: Record<string, string> = {
			knn: 'K-Nearest Neighbors',
			decision_tree: 'Decision Tree (CART)',
			c45: 'C4.5 Decision Tree',
			chaid: 'CHAID Decision Tree',
			naive_bayes: 'Naive Bayes',
			neural_network: 'Neural Network (MLP)',
			linear_regression: 'Linear Regression'
		};
		return names[algo] || algo;
	}

	let isRegression = $derived(experiment?.algorithm === 'linear_regression');
	let featureColumns = $derived(getFeatureColumns());
</script>

<svelte:head>
	<title>Test Model - {experiment?.name || ''} - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-5xl mx-auto">
		<!-- Breadcrumb -->
		<div class="mb-6">
			<button
				type="button"
				on:click={navigateBack}
				class="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
			>
				← Back to experiment
			</button>
		</div>

		{#if loading}
			<div class="text-center py-12">
				<div
					class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
				></div>
				<p class="mt-4 text-gray-600">Loading experiment...</p>
			</div>
		{:else if error && !experiment}
			<div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
				<p class="font-semibold">Error</p>
				<p>{error}</p>
				<p class="text-sm mt-2">Experiment ID: {experimentId}</p>
			</div>
		{:else if experiment}
			<!-- Header -->
			<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
				<h1 class="text-3xl font-bold text-gray-900 mb-2">Test Model: {experiment.name}</h1>
				<p class="text-gray-600">
					Algorithm: <span class="font-semibold"
						>{getAlgorithmName(experiment.algorithm)}</span
					>
				</p>
				{#if isRegression}
					<p class="text-sm text-gray-500 mt-2">
						This model predicts continuous numerical values (regression).
					</p>
				{:else}
					<p class="text-sm text-gray-500 mt-2">
						This model classifies data into discrete categories (classification).
					</p>
				{/if}
			</div>

			<!-- Mode Selection -->
			<div class="bg-white rounded-lg shadow-sm p-4 mb-6">
				<div class="flex items-center gap-4">
					<span class="text-sm font-medium text-gray-700">Test Mode:</span>
					<button
						type="button"
						on:click={switchToSingle}
						class="px-4 py-2 rounded-lg text-sm font-medium transition-colors {testMode ===
						'single'
							? 'bg-blue-600 text-white'
							: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
					>
						Single Prediction
					</button>
					<button
						type="button"
						on:click={switchToBatch}
						class="px-4 py-2 rounded-lg text-sm font-medium transition-colors {testMode ===
						'batch'
							? 'bg-blue-600 text-white'
							: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
					>
						Batch Prediction (CSV)
					</button>
				</div>
			</div>

			{#if testMode === 'single'}
				<!-- Single Prediction Form -->
				<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
					<h2 class="text-xl font-bold text-gray-900 mb-4">Enter Feature Values</h2>

					{#if error}
						<div
							class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-4"
						>
							{error}
						</div>
					{/if}

					{#if featureColumns.length > 0}
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
							{#each featureColumns as feature}
								<div>
									<label
										for={feature}
										class="block text-sm font-medium text-gray-700 mb-2"
									>
										{feature}
									</label>
									<input
										id={feature}
										type="number"
										step="any"
										bind:value={inputData[feature]}
										placeholder="Enter value"
										class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</div>
							{/each}
						</div>

						<div class="flex gap-3">
							<button
								type="button"
								on:click={makePrediction}
								disabled={predicting}
								class="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
							>
								{#if predicting}
									<div
										class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"
									></div>
									Predicting...
								{:else}
									<svg
										class="w-5 h-5"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M13 10V3L4 14h7v7l9-11h-7z"
										/>
									</svg>
									Make Prediction
								{/if}
							</button>

							<button
								type="button"
								on:click={resetForm}
								class="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
							>
								Reset
							</button>
						</div>
					{:else}
						<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
							<div class="text-center">
								<svg
									class="w-12 h-12 text-yellow-600 mx-auto mb-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
									/>
								</svg>
								<p class="text-yellow-800 font-medium">No feature columns available</p>
								<p class="text-sm text-yellow-700 mt-2">
									This experiment might not have feature columns configured properly.
								</p>
								<p class="text-xs text-yellow-600 mt-4">
									Experiment ID: {experimentId}<br />
									Debug: Open browser console (F12) for more details
								</p>
							</div>
						</div>
					{/if}
				</div>

				<!-- Single Prediction Results -->
				{#if predictions}
					<div class="bg-white rounded-lg shadow-sm p-6">
						<h2 class="text-xl font-bold text-gray-900 mb-4">Prediction Result</h2>

						<div
							class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-4"
						>
							<div class="text-center">
								<p class="text-sm text-gray-600 mb-2">
									{isRegression ? 'Predicted Value' : 'Predicted Class'}
								</p>
								<p class="text-4xl font-bold text-blue-600">
									{predictions.predictions[0]}
								</p>
							</div>
						</div>

						{#if predictions.probabilities && predictions.probabilities[0]}
							<div class="mt-4">
								<h3 class="text-lg font-semibold text-gray-900 mb-3">
									Class Probabilities
								</h3>
								<div class="space-y-2">
									{#each predictions.probabilities[0] as prob, i}
										<div class="flex items-center gap-3">
											<span class="text-sm font-medium text-gray-700 w-20"
												>Class {i}</span
											>
											<div class="flex-1 bg-gray-200 rounded-full h-6 relative">
												<div
													class="bg-blue-600 h-6 rounded-full flex items-center justify-end px-2"
													style="width: {prob * 100}%"
												>
													<span class="text-xs font-medium text-white">
														{(prob * 100).toFixed(2)}%
													</span>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<div class="mt-6 p-4 bg-gray-50 rounded-lg">
							<h3 class="text-sm font-semibold text-gray-900 mb-2">Input Data</h3>
							<div class="grid grid-cols-2 gap-2 text-sm">
								{#each Object.entries(inputData) as [key, value]}
									<div class="flex justify-between">
										<span class="text-gray-600">{key}:</span>
										<span class="font-medium text-gray-900">{value}</span>
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/if}
			{:else}
				<!-- Batch Prediction -->
				<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
					<h2 class="text-xl font-bold text-gray-900 mb-4">Upload CSV File</h2>

					{#if featureColumns.length > 0}
						<div class="mb-4">
							<p class="text-sm text-gray-600 mb-2">
								Upload a CSV file with the following columns in any order:
							</p>
							<div class="bg-gray-50 p-3 rounded-lg">
								<code class="text-sm text-gray-800">
									{featureColumns.join(', ')}
								</code>
							</div>
						</div>

						{#if error}
							<div
								class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-4"
							>
								{error}
							</div>
						{/if}

						<div class="mb-6">
							<label
								for="csvFile"
								class="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
							>
								<div class="flex flex-col items-center justify-center pt-5 pb-6">
									<svg
										class="w-10 h-10 mb-3 text-gray-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
										/>
									</svg>
									<p class="mb-2 text-sm text-gray-500">
										{csvFile ? csvFile.name : 'Click to upload CSV file'}
									</p>
									<p class="text-xs text-gray-500">CSV files only</p>
								</div>
								<input
									id="csvFile"
									type="file"
									accept=".csv"
									class="hidden"
									on:change={handleFileChange}
								/>
							</label>
						</div>

						<button
							type="button"
							on:click={makeBatchPrediction}
							disabled={predicting || !csvFile}
							class="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
						>
							{#if predicting}
								<div
									class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"
								></div>
								Processing...
							{:else}
								<svg
									class="w-5 h-5"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M13 10V3L4 14h7v7l9-11h-7z"
									/>
								</svg>
								Predict All
							{/if}
						</button>
					{:else}
						<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
							<div class="text-center">
								<svg
									class="w-12 h-12 text-yellow-600 mx-auto mb-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
									/>
								</svg>
								<p class="text-yellow-800 font-medium">No feature columns available</p>
								<p class="text-sm text-yellow-700 mt-2">
									Cannot perform batch predictions without feature columns.
								</p>
							</div>
						</div>
					{/if}
				</div>

				<!-- Batch Prediction Results -->
				{#if batchPredictions}
					<div class="bg-white rounded-lg shadow-sm p-6">
						<div class="flex justify-between items-center mb-4">
							<h2 class="text-xl font-bold text-gray-900">
								Batch Prediction Results ({batchPredictions.n_samples} samples)
							</h2>
							<button
								type="button"
								on:click={downloadPredictions}
								class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium flex items-center gap-2"
							>
								<svg
									class="w-4 h-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
									/>
								</svg>
								Download CSV
							</button>
						</div>

						<div class="overflow-auto max-h-96 border border-gray-200 rounded-lg">
							<table class="min-w-full divide-y divide-gray-200">
								<thead class="bg-gray-50 sticky top-0">
									<tr>
										<th
											class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
										>
											#
										</th>
										<th
											class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
										>
											Prediction
										</th>
										{#if batchPredictions.probabilities}
											<th
												class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
											>
												Confidence
											</th>
										{/if}
									</tr>
								</thead>
								<tbody class="bg-white divide-y divide-gray-200">
									{#each batchPredictions.predictions as pred, i}
										<tr class="hover:bg-gray-50">
											<td
												class="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
											>
												{i + 1}
											</td>
											<td
												class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900"
											>
												{pred}
											</td>
											{#if batchPredictions.probabilities}
												<td
													class="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
												>
													{(
														Math.max(...batchPredictions.probabilities[i]) *
														100
													).toFixed(2)}%
												</td>
											{/if}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/if}
			{/if}
		{/if}
	</div>
</div>