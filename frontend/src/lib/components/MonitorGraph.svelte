<script lang="ts">
	import TaskNode from './TaskNode.svelte';
	import type { MonitorTask } from '$types/index';

	let {
		tasks,
		selectedTaskId = null,
		onSelectTask
	}: {
		tasks: MonitorTask[];
		selectedTaskId?: string | null;
		onSelectTask?: (task: MonitorTask) => void;
	} = $props();

	const TASK_W = 180;
	const TASK_H = 80;
	const TOOL_W = 140;
	const TOOL_H = 56;
	const GAP_X = 60;
	const GAP_Y = 16;
	const PAD = 20;

	function getNodeSize(task: MonitorTask): { w: number; h: number } {
		return task.tool_name === 'Task' ? { w: TASK_W, h: TASK_H } : { w: TOOL_W, h: TOOL_H };
	}

	// Layout: root tasks a la izquierda, children a la derecha
	function computeLayout(tasks: MonitorTask[]): {
		positions: Map<string, { x: number; y: number; w: number; h: number }>;
		width: number;
		height: number;
	} {
		const positions = new Map<string, { x: number; y: number; w: number; h: number }>();
		if (tasks.length === 0) return { positions, width: 0, height: 0 };

		// Agrupar por depth
		const byDepth = new Map<number, MonitorTask[]>();
		for (const t of tasks) {
			const arr = byDepth.get(t.depth) || [];
			arr.push(t);
			byDepth.set(t.depth, arr);
		}

		const maxDepth = Math.max(...byDepth.keys(), 0);
		let maxY = 0;

		for (let depth = 0; depth <= maxDepth; depth++) {
			const nodes = byDepth.get(depth) || [];
			for (let idx = 0; idx < nodes.length; idx++) {
				const task = nodes[idx];
				const size = getNodeSize(task);
				const x = PAD + depth * (TASK_W + GAP_X);
				const y = PAD + idx * (Math.max(TASK_H, TOOL_H) + GAP_Y);
				positions.set(task.id, { x, y, ...size });
				maxY = Math.max(maxY, y + size.h);
			}
		}

		const width = PAD * 2 + (maxDepth + 1) * (TASK_W + GAP_X) - GAP_X;
		const height = maxY + PAD;

		return {
			positions,
			width: Math.max(width, 400),
			height: Math.max(height, 200)
		};
	}

	function computeEdges(
		tasks: MonitorTask[],
		positions: Map<string, { x: number; y: number; w: number; h: number }>
	): { d: string; color: string }[] {
		const edges: { d: string; color: string }[] = [];

		for (const task of tasks) {
			if (!task.parent_id) continue;
			const from = positions.get(task.parent_id);
			const to = positions.get(task.id);
			if (!from || !to) continue;

			const x1 = from.x + from.w;
			const y1 = from.y + from.h / 2;
			const x2 = to.x;
			const y2 = to.y + to.h / 2;
			const cx = (x1 + x2) / 2;

			const color =
				task.status === 'completed'
					? 'rgba(0,212,170,0.5)'
					: task.status === 'failed'
						? 'rgba(239,68,68,0.4)'
						: 'rgba(255,255,255,0.15)';

			edges.push({
				d: `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`,
				color
			});
		}
		return edges;
	}

	let layout = $derived(computeLayout(tasks));
	let edges = $derived(computeEdges(tasks, layout.positions));
</script>

<div
	class="overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)]"
>
	<svg
		width={layout.width}
		height={layout.height}
		class="min-w-full"
		xmlns="http://www.w3.org/2000/svg"
	>
		{#each edges as edge}
			<path d={edge.d} fill="none" stroke={edge.color} stroke-width="1.5" />
		{/each}

		{#each tasks as task (task.id)}
			{@const pos = layout.positions.get(task.id)}
			{#if pos}
				<TaskNode
					{task}
					x={pos.x}
					y={pos.y}
					w={pos.w}
					h={pos.h}
					selected={selectedTaskId === task.id}
					onclick={onSelectTask}
				/>
			{/if}
		{/each}
	</svg>
</div>
