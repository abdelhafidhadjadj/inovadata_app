<script lang="ts">
	import { onMount } from 'svelte';

	let { metrics }: { metrics: any } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	function renderPlot() {
		if (!metrics || !plotDiv) return;

		import('plotly.js-dist-min').then((Plotly) => {
			const metricNames = ['Accuracy', 'Precision', 'Recall', 'F1-Score'];
			const values = [
				metrics.accuracy * 100,
				metrics.precision * 100,
				metrics.recall * 100,
				metrics.f1_score * 100
			];

			const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'];

			const data = [
				{
					x: metricNames,
					y: values,
					type: 'bar',
					marker: {
						color: colors
					},
					text: values.map((v) => v.toFixed(2) + '%'),
					textposition: 'auto',
					hovertemplate: '%{x}: %{y:.2f}%<extra></extra>'
				}
			];

			const layout = {
				title: {
					text: 'Performance Metrics',
					font: { size: 16, color: '#1f2937' }
				},
				yaxis: {
					title: 'Score (%)',
					range: [0, 100]
				},
				xaxis: {
					title: ''
				},
				margin: { l: 60, r: 40, t: 60, b: 60 },
				height: 350
			};

			Plotly.newPlot(plotDiv, data, layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>