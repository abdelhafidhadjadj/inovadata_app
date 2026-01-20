<script lang="ts">
	import { onMount } from 'svelte';

	let { rocData }: { rocData: any } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	$effect(() => {
		if (rocData && plotDiv) {
			renderPlot();
		}
	});

	function renderPlot() {
		if (!rocData || !plotDiv) return;

		import('plotly.js-dist-min').then((Plotly) => {
			const trace1 = {
				x: rocData.fpr,
				y: rocData.tpr,
				mode: 'lines',
				name: `ROC Curve (AUC = ${rocData.auc.toFixed(3)})`,
				line: {
					color: '#3b82f6',
					width: 2
				},
				type: 'scatter'
			};

			// Ligne diagonale de référence
			const trace2 = {
				x: [0, 1],
				y: [0, 1],
				mode: 'lines',
				name: 'Random Classifier',
				line: {
					color: '#ef4444',
					width: 2,
					dash: 'dash'
				},
				type: 'scatter'
			};

			const layout = {
				title: {
					text: 'ROC Curve',
					font: { size: 16, color: '#1f2937' }
				},
				xaxis: {
					title: 'False Positive Rate',
					range: [0, 1]
				},
				yaxis: {
					title: 'True Positive Rate',
					range: [0, 1]
				},
				margin: { l: 60, r: 40, t: 60, b: 60 },
				height: 400,
				showlegend: true,
				legend: {
					x: 0.6,
					y: 0.1
				}
			};

			Plotly.newPlot(plotDiv, [trace1, trace2], layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>