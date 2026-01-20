<script lang="ts">
	import { onMount } from 'svelte';

	let { experimentId }: { experimentId: number } = $props();

	let loading = $state(true);
	let error = $state('');
	let treeData = $state<any>(null);
	let scale = $state(1);
	let translateX = $state(0);
	let translateY = $state(0);
	let containerDiv: HTMLElement;
	
	// Variables pour le drag
	let isDragging = $state(false);
	let startX = $state(0);
	let startY = $state(0);
	let scrollLeft = $state(0);
	let scrollTop = $state(0);

	onMount(async () => {
		await loadTreeVisualization();
	});

	async function loadTreeVisualization() {
		try {
			const res = await fetch(
				`http://localhost:8001/ml/experiments/${experimentId}/tree-visualization`
			);
			if (res.ok) {
				treeData = await res.json();
			} else {
				const errorData = await res.json();
				error = errorData.detail || 'Failed to load tree visualization';
			}
		} catch (err) {
			error = 'Error loading tree visualization';
			console.error(err);
		} finally {
			loading = false;
		}
	}

	function zoomIn() {
		scale = Math.min(scale + 0.2, 3);
	}

	function zoomOut() {
		scale = Math.max(scale - 0.2, 0.5);
	}

	function resetZoom() {
		scale = 1;
		if (containerDiv) {
			containerDiv.scrollLeft = 0;
			containerDiv.scrollTop = 0;
		}
	}

	function downloadTree() {
		if (!treeData || treeData.type !== 'image') return;

		const link = document.createElement('a');
		link.href = `data:image/png;base64,${treeData.content}`;
		link.download = `decision_tree_experiment_${experimentId}.png`;
		link.click();
	}

	function openInNewTab() {
		if (!treeData || treeData.type !== 'image') return;

		const newWindow = window.open();
		if (newWindow) {
			newWindow.document.write(`
				<!DOCTYPE html>
				<html>
				<head>
					<title>Decision Tree - Experiment ${experimentId}</title>
					<style>
						body {
							margin: 0;
							padding: 20px;
							background: #f3f4f6;
							display: flex;
							justify-content: center;
							align-items: center;
							min-height: 100vh;
						}
						img {
							max-width: 100%;
							height: auto;
							box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
							background: white;
							padding: 20px;
							border-radius: 8px;
						}
					</style>
				</head>
				<body>
					<img src="data:image/png;base64,${treeData.content}" alt="Decision Tree" />
				</body>
				</html>
			`);
		}
	}

	// Drag handlers
	function handleMouseDown(e: MouseEvent) {
		if (!containerDiv) return;
		isDragging = true;
		startX = e.pageX - containerDiv.offsetLeft;
		startY = e.pageY - containerDiv.offsetTop;
		scrollLeft = containerDiv.scrollLeft;
		scrollTop = containerDiv.scrollTop;
		containerDiv.style.cursor = 'grabbing';
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging || !containerDiv) return;
		e.preventDefault();
		const x = e.pageX - containerDiv.offsetLeft;
		const y = e.pageY - containerDiv.offsetTop;
		const walkX = (x - startX) * 2;
		const walkY = (y - startY) * 2;
		containerDiv.scrollLeft = scrollLeft - walkX;
		containerDiv.scrollTop = scrollTop - walkY;
	}

	function handleMouseUp() {
		isDragging = false;
		if (containerDiv) {
			containerDiv.style.cursor = scale > 1 ? 'grab' : 'default';
		}
	}

	function handleMouseLeave() {
		if (isDragging) {
			isDragging = false;
			if (containerDiv) {
				containerDiv.style.cursor = scale > 1 ? 'grab' : 'default';
			}
		}
	}

	// Mettre à jour le curseur quand le scale change
	$effect(() => {
		if (containerDiv) {
			containerDiv.style.cursor = scale > 1 ? 'grab' : 'default';
		}
	});
</script>

<div class="w-full">
	{#if loading}
		<div class="text-center py-8">
			<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<p class="mt-2 text-sm text-gray-600">Generating tree visualization...</p>
		</div>
	{:else if error}
		<div class="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
			<p class="text-sm font-medium">⚠️ {error}</p>
			<p class="text-xs mt-1">Make sure graphviz is installed in the backend container.</p>
		</div>
	{:else if treeData}
		{#if treeData.type === 'image'}
			<div class="space-y-4">
				<!-- Toolbar -->
				<div class="flex items-center justify-between bg-gray-50 p-3 rounded-lg border border-gray-200">
					<!-- Zoom Controls -->
					<div class="flex items-center gap-2">
						<span class="text-sm text-gray-600 font-medium mr-2">Zoom:</span>
						<button
							on:click={zoomOut}
							disabled={scale <= 0.5}
							class="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-1"
							title="Zoom out"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"
								/>
							</svg>
						</button>

						<span class="text-sm font-medium text-gray-700 min-w-[60px] text-center">
							{Math.round(scale * 100)}%
						</span>

						<button
							on:click={zoomIn}
							disabled={scale >= 3}
							class="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-1"
							title="Zoom in"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"
								/>
							</svg>
						</button>

						<button
							on:click={resetZoom}
							class="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm"
							title="Reset zoom"
						>
							Reset
						</button>

						{#if scale > 1}
							<span class="text-xs text-gray-500 ml-2 flex items-center gap-1">
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11"
									/>
								</svg>
								Drag to pan
							</span>
						{/if}
					</div>

					<!-- Action Buttons -->
					<div class="flex items-center gap-2">
						<button
							on:click={openInNewTab}
							class="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
							title="Open in new tab"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
								/>
							</svg>
							Open Full Size
						</button>

						<button
							on:click={downloadTree}
							class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
							title="Download tree image"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
								/>
							</svg>
							Download PNG
						</button>
					</div>
				</div>

				<!-- Tree Container with Pan & Scroll -->
				<div
					bind:this={containerDiv}
					on:mousedown={handleMouseDown}
					on:mousemove={handleMouseMove}
					on:mouseup={handleMouseUp}
					on:mouseleave={handleMouseLeave}
					class="overflow-auto border border-gray-200 rounded-lg bg-white select-none"
					style="max-height: 600px; cursor: {scale > 1 ? 'grab' : 'default'};"
				>
					<div class="p-4 inline-block min-w-full min-h-[400px]">
						<img
							src="data:image/png;base64,{treeData.content}"
							alt="Decision Tree Visualization"
							class="transition-transform duration-200 ease-in-out pointer-events-none"
							style="transform: scale({scale}); transform-origin: center; display: block; margin: auto;"
							draggable="false"
						/>
					</div>
				</div>

				<!-- Info Footer -->
				<div class="text-xs text-gray-500 text-center space-y-1 bg-gray-50 p-3 rounded-lg">
					<p class="font-medium text-gray-700">
						{treeData.algorithm?.toUpperCase()} Decision Tree Structure
					</p>
					<p>🟦 Blue/Green nodes = predictions | 🟧 Orange nodes = decision splits</p>
					<p class="text-gray-400">
						{#if scale > 1}
							<strong>Tip:</strong> Click and drag to pan the zoomed view
						{:else}
							Use the zoom controls to explore the tree structure in detail
						{/if}
					</p>
				</div>
			</div>
		{:else if treeData.type === 'text'}
			<div class="space-y-4">
				<!-- Toolbar for Text -->
				<div class="flex justify-end">
					<button
						on:click={() => {
							const text = treeData.content;
							navigator.clipboard.writeText(text);
						}}
						class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
							/>
						</svg>
						Copy Text
					</button>
				</div>

				<div class="bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-auto max-h-[600px]">
					<pre class="font-mono text-xs whitespace-pre-wrap text-gray-800">{treeData.content}</pre>
				</div>

				<p class="text-xs text-gray-500 text-center">CHAID Tree Text Representation</p>
			</div>
		{/if}
	{/if}
</div>