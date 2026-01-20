<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import ConfusionMatrixPlot from '$lib/components/ml/ConfusionMatrixPlot.svelte';
	import MetricsBarChart from '$lib/components/ml/MetricsBarChart.svelte';
	import TreeVisualization from '$lib/components/ml/TreeVisualization.svelte';
	import ROCCurvePlot from '$lib/components/ml/ROCCurvePlot.svelte';
	import RegressionMetricsChart from '$lib/components/ml/RegressionMetricsChart.svelte';
	import ResidualsPlot from '$lib/components/ml/ResidualsPlot.svelte';
	const projectId = $page.params.id;
	const datasetId = $page.params.datasetId;
	const experimentId = $page.params.experimentId;
    
	let experiment = $state<any>(null);
        let loading = $state(true);
        let error = $state('');
        let activeTab = $state<'metrics' | 'tree'>('metrics');
        let isRegression = $derived(experiment?.algorithm === 'linear_regression');
        
	onMount(async () => {
		await loadExperiment();
		
		// Auto-refresh si en cours d'entraînement
		if (experiment?.status === 'training' || experiment?.status === 'pending') {
			const interval = setInterval(async () => {
				await loadExperiment();
				if (experiment?.status === 'completed' || experiment?.status === 'failed') {
					clearInterval(interval);
				}
			}, 3000);
			
			return () => clearInterval(interval);
		}
	});

	async function loadExperiment() {
		try {
			const res = await fetch(`http://localhost:8001/ml/experiments/${experimentId}`);
			
			if (res.ok) {
				const data = await res.json();
				experiment = data;
			} else {
				error = 'Experiment not found';
			}
		} catch (err) {
			console.error('Fetch error:', err);
			error = 'Loading error';
		} finally {
			loading = false;
		}
	}

    async function downloadModel() {
		try {
			const response = await fetch(
				`http://localhost:8001/ml/experiments/${experimentId}/download-model`
			);
			if (response.ok) {
				const blob = await response.blob();
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = `model_${experiment.name}_${experiment.algorithm}.pkl`;
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
			}
		} catch (error) {
			console.error('Error downloading model:', error);
		}
	}

	function getStatusColor(status: string) {
		const colors: any = {
			pending: 'bg-gray-100 text-gray-800',
			training: 'bg-blue-100 text-blue-800',
			completed: 'bg-green-100 text-green-800',
			failed: 'bg-red-100 text-red-800'
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

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

	// Vérifier si c'est un algorithme d'arbre de décision
	let isTreeAlgorithm = $derived(
		experiment?.algorithm === 'decision_tree' ||
		experiment?.algorithm === 'c45' ||
		experiment?.algorithm === 'chaid'
	);

	// Calculer les valeurs de la confusion matrix
	let confusionMatrixData = $derived.by(() => {
		if (!experiment?.confusion_matrix) return null;
		
		const matrix = experiment.confusion_matrix;
		const total = matrix.flat().reduce((a: number, b: number) => a + b, 0);
		
		return {
			matrix,
			total,
			classes: matrix.length
		};
	});
</script>

<svelte:head>
	<title>Experiment {experiment?.name || experimentId} - DataMine</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-7xl mx-auto">
		<!-- Breadcrumb -->
		<div class="mb-6">
			<button
				on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml`)}
				class="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
			>
				← Back to experiments
			</button>
		</div>

		{#if loading}
			<div class="text-center py-12">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
				<p class="mt-4 text-gray-600">Loading...</p>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
				{error}
			</div>
		{:else if experiment}
			<!-- Header -->
			<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
				<div class="flex justify-between items-start mb-4">
					<div>
						<h1 class="text-3xl font-bold text-gray-900 mb-2">{experiment.name}</h1>
						{#if experiment.description}
							<p class="text-gray-600">{experiment.description}</p>
						{/if}
					</div>

					<div class="flex items-center gap-3">
                    	<span class="px-3 py-1 rounded-full text-sm font-medium {getStatusColor(experiment.status)}">
                    		{experiment.status === 'pending'
                    			? 'Pending'
                    			: experiment.status === 'training'
                    				? 'Training...'
                    				: experiment.status === 'completed'
                    					? 'Completed'
                    					: 'Failed'}
                    	</span>
                    
                    	<!-- Boutons d'actions -->
                    	{#if experiment.status === 'completed'}
                    		<button
                    			on:click={downloadModel}
                    			class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                    			title="Download trained model"
                    		>
                    			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    				<path
                    					stroke-linecap="round"
                    					stroke-linejoin="round"
                    					stroke-width="2"
                    					d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    				/>
                    			</svg>
                    			Download Model
                    		</button>
                        
                    		<button
                    			on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/${experimentId}/test`)}
                    			class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                    			title="Test model with new data"
                    		>
                    			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    				<path
                    					stroke-linecap="round"
                    					stroke-linejoin="round"
                    					stroke-width="2"
                    					d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    				/>
                    			</svg>
                    			Test Model
                    		</button>
                        
                    		<button
                    			on:click={() => goto(`/dashboard/projects/${projectId}/datasets/${datasetId}/ml/compare`)}
                    			class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
                    		>
                    			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    				<path
                    					stroke-linecap="round"
                    					stroke-linejoin="round"
                    					stroke-width="2"
                    					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    				/>
                    			</svg>
                    			Compare
                    		</button>
                    	{/if}
                    </div>
				</div>

				<div class="grid grid-cols-4 gap-4 pt-4 border-t">
					<div>
						<p class="text-sm text-gray-600">Algorithm</p>
						<p class="text-lg font-semibold text-gray-900">
							{getAlgorithmName(experiment.algorithm)}
						</p>
					</div>
					<div>
						<p class="text-sm text-gray-600">Created</p>
						<p class="text-lg font-semibold text-gray-900">
							{new Date(experiment.created_at).toLocaleDateString()}
						</p>
					</div>
					<div>
						<p class="text-sm text-gray-600">Training Time</p>
						<p class="text-lg font-semibold text-gray-900">
							{experiment.training_time ? `${experiment.training_time.toFixed(4)}s` : '—'}
						</p>
					</div>
					<div>
						<p class="text-sm text-gray-600">Accuracy</p>
						<p class="text-lg font-semibold text-gray-900">
							{experiment.metrics?.accuracy
								? `${(experiment.metrics.accuracy * 100).toFixed(2)}%`
								: '—'}
						</p>
					</div>
				</div>
			</div>

			<!-- Status Messages -->
			{#if experiment.status === 'training' || experiment.status === 'pending'}
				<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
					<div class="flex items-start">
						<svg class="animate-spin w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						<div>
							<h3 class="text-sm font-medium text-blue-800">
								{experiment.status === 'pending' ? 'Pending' : 'Training in progress'}
							</h3>
							<p class="text-sm text-blue-700 mt-1">
								The experiment is running. This page will auto-refresh.
							</p>
						</div>
					</div>
				</div>
			{:else if experiment.status === 'failed'}
				<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
					<div class="flex items-start">
						<svg class="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<div>
							<h3 class="text-sm font-medium text-red-800">Training Failed</h3>
							<p class="text-sm text-red-700 mt-1">
								{experiment.error_message || 'Unknown error'}
							</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- NOUVEAU: Tabs pour les arbres de décision -->
			{#if experiment.status === 'completed' && isTreeAlgorithm}
				<div class="mb-6 border-b border-gray-200">
					<nav class="flex space-x-8">
						<button
							on:click={() => (activeTab = 'metrics')}
							class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'metrics'
								? 'border-blue-600 text-blue-600'
								: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
						>
							📊 Metrics & Performance
						</button>
						<button
							on:click={() => (activeTab = 'tree')}
							class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'tree'
								? 'border-blue-600 text-blue-600'
								: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
						>
							🌳 Tree Visualization
						</button>
					</nav>
				</div>
			{/if}
                <!-- Results (if completed) -->
            {#if experiment.status === 'completed' && experiment.metrics}
            	{#if activeTab === 'metrics' || !isTreeAlgorithm}
            		{#if isRegression}
            			<!-- RÉGRESSION -->
            			<div class="grid grid-cols-1 gap-6 mb-6">
            				<div class="bg-white rounded-lg shadow-sm p-6">
            					<h2 class="text-xl font-bold text-gray-900 mb-4">Regression Metrics</h2>
            					<RegressionMetricsChart metrics={experiment.metrics} />
            				</div>
            			</div>
                    
            			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            				<!-- Detailed Metrics -->
            				<div class="bg-white rounded-lg shadow-sm p-6">
            					<h2 class="text-xl font-bold text-gray-900 mb-4">Detailed Metrics</h2>
            					<div class="space-y-4">
            						<div class="flex justify-between items-center p-3 bg-red-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">MSE</span>
            							<span class="text-2xl font-bold text-red-600">
            								{experiment.metrics.mse.toFixed(4)}
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">RMSE</span>
            							<span class="text-2xl font-bold text-orange-600">
            								{experiment.metrics.rmse.toFixed(4)}
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">MAE</span>
            							<span class="text-2xl font-bold text-purple-600">
            								{experiment.metrics.mae.toFixed(4)}
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">R² Score</span>
            							<span class="text-2xl font-bold text-green-600">
            								{(experiment.metrics.r2_score * 100).toFixed(2)}%
            							</span>
            						</div>
            					</div>
            				</div>
                        
            				<!-- Residuals Plot -->
            				{#if experiment.residuals && experiment.predictions}
            					<div class="bg-white rounded-lg shadow-sm p-6">
            						<h2 class="text-xl font-bold text-gray-900 mb-4">Residuals Analysis</h2>
            						<ResidualsPlot
            							predictions={experiment.predictions}
            							residuals={experiment.residuals}
            						/>
            					</div>
            				{/if}
            			</div>
            		{:else}
            			<!-- CLASSIFICATION (code existant) -->
            			<div class="grid grid-cols-1 gap-6 mb-6">
            				<div class="bg-white rounded-lg shadow-sm p-6">
            					<h2 class="text-xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
            					<MetricsBarChart metrics={experiment.metrics} />
            				</div>
            			</div>
                    
            			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            				<!-- Detailed Metrics -->
            				<div class="bg-white rounded-lg shadow-sm p-6">
            					<h2 class="text-xl font-bold text-gray-900 mb-4">Detailed Metrics</h2>
            					<div class="space-y-4">
            						<div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">Accuracy</span>
            							<span class="text-2xl font-bold text-green-600">
            								{(experiment.metrics.accuracy * 100).toFixed(2)}%
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">Precision</span>
            							<span class="text-2xl font-bold text-blue-600">
            								{(experiment.metrics.precision * 100).toFixed(2)}%
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">Recall</span>
            							<span class="text-2xl font-bold text-purple-600">
            								{(experiment.metrics.recall * 100).toFixed(2)}%
            							</span>
            						</div>
                                
            						<div class="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
            							<span class="text-sm font-medium text-gray-700">F1-Score</span>
            							<span class="text-2xl font-bold text-orange-600">
            								{(experiment.metrics.f1_score * 100).toFixed(2)}%
            							</span>
            						</div>
                                
            						{#if experiment.metrics.auc}
            							<div class="flex justify-between items-center p-3 bg-indigo-50 rounded-lg">
            								<span class="text-sm font-medium text-gray-700">AUC</span>
            								<span class="text-2xl font-bold text-indigo-600">
            									{experiment.metrics.auc.toFixed(3)}
            								</span>
            							</div>
            						{/if}
            					</div>
            				</div>
                        
            				<!-- Confusion Matrix -->
            				{#if experiment.confusion_matrix}
            					<div class="bg-white rounded-lg shadow-sm p-6">
            						<h2 class="text-xl font-bold text-gray-900 mb-4">Confusion Matrix</h2>
            						<ConfusionMatrixPlot confusionMatrix={experiment.confusion_matrix} />
            					</div>
            				{/if}
            			</div>
                    
            			<!-- ROC Curve (si disponible) -->
            			{#if experiment.roc_data}
            				<div class="bg-white rounded-lg shadow-sm p-6 mt-6">
            					<h2 class="text-xl font-bold text-gray-900 mb-4">
            						ROC Curve (AUC = {experiment.roc_data.auc.toFixed(3)})
            					</h2>
            					<ROCCurvePlot rocData={experiment.roc_data} />
            					<p class="text-sm text-gray-600 mt-4">
            						The ROC curve shows the trade-off between True Positive Rate and False Positive
            						Rate. AUC (Area Under Curve) of 1.0 indicates perfect classification, while 0.5
            						indicates random guessing.
            					</p>
            				</div>
            			{/if}
            		{/if}
            	{:else if activeTab === 'tree'}
            		<!-- Tree Visualization (code existant) -->
            		<div class="bg-white rounded-lg shadow-sm p-6">
            			<h2 class="text-xl font-bold text-gray-900 mb-4">
            				{getAlgorithmName(experiment.algorithm)} - Tree Structure
            			</h2>
            			<div class="text-sm text-gray-600 mb-4">
            				<p>
            					This visualization shows the decision tree structure with nodes, splits, and leaf
            					predictions.
            				</p>
            			</div>
            			<TreeVisualization experimentId={parseInt(experimentId)} />
            		</div>
            	{/if}
            {/if}
		{/if}
	</div>
</div>