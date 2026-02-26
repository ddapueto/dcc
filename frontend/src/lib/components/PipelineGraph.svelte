<script lang="ts">
	import StepNode from './StepNode.svelte';
	import type { PipelineStep } from '$types/index';

	let {
		steps,
		selectedStepId = null,
		onSelectStep
	}: {
		steps: PipelineStep[];
		selectedStepId?: string | null;
		onSelectStep?: (step: PipelineStep) => void;
	} = $props();

	const NODE_W = 160;
	const NODE_H = 72;
	const GAP_X = 80;
	const GAP_Y = 24;
	const PAD = 20;

	// Topological sort en layers (BFS desde nodos sin deps)
	function computeLayout(
		steps: PipelineStep[]
	): { positions: Map<string, { x: number; y: number }>; width: number; height: number } {
		const positions = new Map<string, { x: number; y: number }>();
		if (steps.length === 0) return { positions, width: 0, height: 0 };

		const stepMap = new Map(steps.map((s) => [s.id, s]));
		const layers: string[][] = [];
		const assigned = new Set<string>();

		// BFS layering
		const inDegree = new Map<string, number>();
		for (const s of steps) {
			const validDeps = (s.depends_on ?? []).filter((d) => stepMap.has(d));
			inDegree.set(s.id, validDeps.length);
		}

		let queue = steps.filter((s) => (inDegree.get(s.id) ?? 0) === 0).map((s) => s.id);

		while (queue.length > 0) {
			layers.push([...queue]);
			for (const id of queue) assigned.add(id);

			const nextQueue: string[] = [];
			for (const s of steps) {
				if (assigned.has(s.id)) continue;
				const deps = (s.depends_on ?? []).filter((d) => stepMap.has(d));
				if (deps.every((d) => assigned.has(d))) {
					nextQueue.push(s.id);
				}
			}
			queue = nextQueue;
		}

		// Posicionar nodos sin deps asignadas (ciclos o huérfanos)
		for (const s of steps) {
			if (!assigned.has(s.id)) {
				if (layers.length === 0) layers.push([]);
				layers[layers.length - 1].push(s.id);
			}
		}

		let maxLayerSize = 0;
		for (let layer = 0; layer < layers.length; layer++) {
			const nodes = layers[layer];
			maxLayerSize = Math.max(maxLayerSize, nodes.length);
			for (let idx = 0; idx < nodes.length; idx++) {
				positions.set(nodes[idx], {
					x: PAD + layer * (NODE_W + GAP_X),
					y: PAD + idx * (NODE_H + GAP_Y)
				});
			}
		}

		const width = PAD * 2 + layers.length * (NODE_W + GAP_X) - GAP_X;
		const height = PAD * 2 + maxLayerSize * (NODE_H + GAP_Y) - GAP_Y;

		return { positions, width: Math.max(width, 400), height: Math.max(height, 200) };
	}

	// Generar paths de flechas SVG
	function computeEdges(
		steps: PipelineStep[],
		positions: Map<string, { x: number; y: number }>
	): { d: string; color: string }[] {
		const edges: { d: string; color: string }[] = [];
		const stepMap = new Map(steps.map((s) => [s.id, s]));

		for (const step of steps) {
			const deps = (step.depends_on ?? []).filter((d) => stepMap.has(d));
			for (const depId of deps) {
				const from = positions.get(depId);
				const to = positions.get(step.id);
				if (!from || !to) continue;

				const x1 = from.x + NODE_W;
				const y1 = from.y + NODE_H / 2;
				const x2 = to.x;
				const y2 = to.y + NODE_H / 2;
				const cx = (x1 + x2) / 2;

				const color =
					stepMap.get(depId)?.status === 'completed'
						? 'rgba(0,212,170,0.5)'
						: 'rgba(255,255,255,0.1)';

				edges.push({
					d: `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`,
					color
				});
			}
		}
		return edges;
	}

	let layout = $derived(computeLayout(steps));
	let edges = $derived(computeEdges(steps, layout.positions));
</script>

<div class="overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)]">
	<svg
		width={layout.width}
		height={layout.height}
		class="min-w-full"
		xmlns="http://www.w3.org/2000/svg"
	>
		<!-- Flechas de dependencias -->
		{#each edges as edge}
			<path d={edge.d} fill="none" stroke={edge.color} stroke-width="2" />
		{/each}

		<!-- Nodos -->
		{#each steps as step (step.id)}
			{@const pos = layout.positions.get(step.id)}
			{#if pos}
				<StepNode
					{step}
					x={pos.x}
					y={pos.y}
					w={NODE_W}
					h={NODE_H}
					selected={selectedStepId === step.id}
					onclick={onSelectStep}
				/>
			{/if}
		{/each}
	</svg>
</div>
