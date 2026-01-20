<script lang="ts">
	import { onMount } from 'svelte';

	let { confusionMatrix }: { confusionMatrix: number[][] } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	function renderPlot() {
		if (!confusionMatrix || !plotDiv) return;

		// Importer Plotly dynamiquement
		import('plotly.js-dist-min').then((Plotly) => {
			const data = [
				{
					z: confusionMatrix,
					type: 'heatmap',
					colorscale: 'Blues',
					showscale: true,
					hovertemplate: 'Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>'
				}
			];

			const layout = {
				title: {
					text: 'Confusion Matrix',
					font: { size: 16, color: '#1f2937' }
				},
				xaxis: {
					title: 'Predicted Class',
					tickmode: 'linear',
					tick0: 0,
					dtick: 1
				},
				yaxis: {
					title: 'Actual Class',
					tickmode: 'linear',
					tick0: 0,
					dtick: 1,
					autorange: 'reversed'
				},
				annotations: [] as any[],
				margin: { l: 80, r: 40, t: 60, b: 80 },
				height: 400
			};

			// Ajouter les annotations (valeurs dans les cellules)
			for (let i = 0; i < confusionMatrix.length; i++) {
				for (let j = 0; j < confusionMatrix[i].length; j++) {
					layout.annotations.push({
						x: j,
						y: i,
						text: confusionMatrix[i][j].toString(),
						showarrow: false,
						font: {
							color: confusionMatrix[i][j] > confusionMatrix.flat().reduce((a, b) => Math.max(a, b)) / 2
								? 'white'
								: 'black',
							size: 14,
							weight: 'bold'
						}
					});
				}
			}

			Plotly.newPlot(plotDiv, data, layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>