<script lang="ts">
	import { onMount } from 'svelte';

	let { experiments }: { experiments: any[] } = $props();

	let plotDiv: HTMLElement;

	onMount(() => {
		renderPlot();
	});

	// Re-render si les expériences changent
	$effect(() => {
		if (experiments && plotDiv) {
			renderPlot();
		}
	});

	function renderPlot() {
		if (!experiments || experiments.length === 0 || !plotDiv) return;

		import('plotly.js-dist-min').then((Plotly) => {
			const experimentNames = experiments.map((exp) => exp.name);

			const traces = [
				{
					name: 'Accuracy',
					x: experimentNames,
					y: experiments.map((exp) => (exp.metrics?.accuracy || 0) * 100),
					type: 'bar',
					marker: { color: '#10b981' }
				},
				{
					name: 'Precision',
					x: experimentNames,
					y: experiments.map((exp) => (exp.metrics?.precision || 0) * 100),
					type: 'bar',
					marker: { color: '#3b82f6' }
				},
				{
					name: 'Recall',
					x: experimentNames,
					y: experiments.map((exp) => (exp.metrics?.recall || 0) * 100),
					type: 'bar',
					marker: { color: '#8b5cf6' }
				},
				{
					name: 'F1-Score',
					x: experimentNames,
					y: experiments.map((exp) => (exp.metrics?.f1_score || 0) * 100),
					type: 'bar',
					marker: { color: '#f59e0b' }
				}
			];

			const layout = {
				title: {
					text: 'Experiment Performance Comparison',
					font: { size: 16, color: '#1f2937' }
				},
				barmode: 'group',
				yaxis: {
					title: 'Score (%)',
					range: [0, 100]
				},
				xaxis: {
					title: 'Experiments'
				},
				margin: { l: 60, r: 40, t: 60, b: 100 },
				height: 400,
				legend: {
					orientation: 'h',
					y: -0.2
				}
			};

			Plotly.newPlot(plotDiv, traces as any, layout, { responsive: true });
		});
	}
</script>

<div bind:this={plotDiv} class="w-full"></div>