<script lang="ts">
	import { onMount } from 'svelte';

	let { metrics }: { metrics: any } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	$effect(() => {
		if (metrics && plotDiv) {
			renderPlot();
		}
	});

	function renderPlot() {
		if (!metrics || !plotDiv) return;

		import('plotly.js-dist-min').then((Plotly) => {
			const trace = {
				x: ['MSE', 'RMSE', 'MAE', 'R² Score'],
				y: [
					metrics.mse || 0,
					metrics.rmse || 0,
					metrics.mae || 0,
					(metrics.r2_score || 0) * 100 // Normaliser R² en pourcentage
				],
				type: 'bar',
				marker: {
					color: ['#ef4444', '#f59e0b', '#8b5cf6', '#10b981']
				},
				text: [
					metrics.mse?.toFixed(4),
					metrics.rmse?.toFixed(4),
					metrics.mae?.toFixed(4),
					`${((metrics.r2_score || 0) * 100).toFixed(2)}%`
				],
				textposition: 'auto'
			};

			const layout = {
				title: {
					text: 'Regression Metrics',
					font: { size: 16, color: '#1f2937' }
				},
				yaxis: {
					title: 'Value'
				},
				margin: { l: 60, r: 40, t: 60, b: 60 },
				height: 350,
				showlegend: false
			};

			Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>