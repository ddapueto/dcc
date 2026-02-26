<script lang="ts">
	import { Play, Pause, Square, RotateCcw, DollarSign, Clock } from '@lucide/svelte';
	import type { Pipeline } from '$types/index';

	let {
		pipeline,
		executing,
		progress,
		onExecute,
		onCancel,
		onPause,
		onResume
	}: {
		pipeline: Pipeline;
		executing: boolean;
		progress: number;
		onExecute: () => void;
		onCancel: () => void;
		onPause: () => void;
		onResume: () => void;
	} = $props();

	function formatDuration(ms: number): string {
		if (ms < 1000) return `${ms}ms`;
		const s = Math.round(ms / 1000);
		if (s < 60) return `${s}s`;
		return `${Math.floor(s / 60)}m ${s % 60}s`;
	}
</script>

<div class="flex items-center gap-3">
	<!-- Action buttons -->
	<div class="flex items-center gap-1">
		{#if pipeline.status === 'draft' || pipeline.status === 'ready' || pipeline.status === 'failed'}
			<button
				class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black transition-opacity hover:opacity-90"
				onclick={onExecute}
			>
				<Play class="h-3.5 w-3.5" />
				Execute
			</button>
		{/if}
		{#if pipeline.status === 'running' && executing}
			<button
				class="flex items-center gap-1.5 rounded-md bg-yellow-500/20 px-3 py-1.5 text-xs font-medium text-yellow-400 hover:bg-yellow-500/30"
				onclick={onPause}
			>
				<Pause class="h-3.5 w-3.5" />
				Pause
			</button>
			<button
				class="flex items-center gap-1.5 rounded-md bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/30"
				onclick={onCancel}
			>
				<Square class="h-3.5 w-3.5" />
				Cancel
			</button>
		{/if}
		{#if pipeline.status === 'paused'}
			<button
				class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)]/20 px-3 py-1.5 text-xs font-medium text-[var(--color-accent)] hover:bg-[var(--color-accent)]/30"
				onclick={onResume}
			>
				<RotateCcw class="h-3.5 w-3.5" />
				Resume
			</button>
			<button
				class="flex items-center gap-1.5 rounded-md bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/30"
				onclick={onCancel}
			>
				<Square class="h-3.5 w-3.5" />
				Cancel
			</button>
		{/if}
	</div>

	<!-- Progress bar -->
	{#if executing || pipeline.status === 'running'}
		<div class="flex flex-1 items-center gap-2">
			<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-bg-card)]">
				<div
					class="h-full rounded-full bg-[var(--color-accent)] transition-all duration-500"
					style="width: {progress}%"
				></div>
			</div>
			<span class="text-xs text-[var(--color-text-muted)]">{progress}%</span>
		</div>
	{/if}

	<!-- Cost + duration badges -->
	<div class="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
		{#if pipeline.total_cost > 0}
			<span class="flex items-center gap-1 rounded bg-[var(--color-bg-card)] px-2 py-0.5">
				<DollarSign class="h-3 w-3" />
				${pipeline.total_cost.toFixed(4)}
			</span>
		{/if}
		{#if pipeline.total_duration_ms > 0}
			<span class="flex items-center gap-1 rounded bg-[var(--color-bg-card)] px-2 py-0.5">
				<Clock class="h-3 w-3" />
				{formatDuration(pipeline.total_duration_ms)}
			</span>
		{/if}
	</div>
</div>
