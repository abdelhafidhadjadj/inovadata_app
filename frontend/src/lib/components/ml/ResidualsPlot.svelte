<script lang="ts">
	import { onMount } from 'svelte';

	let { predictions, residuals }: { predictions: number[]; residuals: number[] } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	$effect(() => {
		if (predictions && residuals && plotDiv) {
			renderPlot();
		}
	});

	function renderPlot() {
		if (!predictions || !residuals || !plotDiv) return;

		import('plotly.js-dist-min').then((Plotly) => {
			const trace = {
				x: predictions,
				y: residuals,
				mode: 'markers',
				type: 'scatter',
				marker: {
					color: '#3b82f6',
					size: 6,
					opacity: 0.6
				},
				name: 'Residuals'
			};

			// Ligne y=0
			const zeroline = {
				x: [Math.min(...predictions), Math.max(...predictions)],
				y: [0, 0],
				mode: 'lines',
				line: {
					color: '#ef4444',
					width: 2,
					dash: 'dash'
				},
				name: 'Zero Line'
			};

			const layout = {
				title: {
					text: 'Residuals Plot',
					font: { size: 16, color: '#1f2937' }
				},
				xaxis: {
					title: 'Predicted Values'
				},
				yaxis: {
					title: 'Residuals',
					zeroline: true
				},
				margin: { l: 60, r: 40, t: 60, b: 60 },
				height: 400,
				showlegend: true
			};

			Plotly.newPlot(plotDiv, [trace, zeroline], layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>