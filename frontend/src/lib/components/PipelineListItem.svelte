<script lang="ts">
	import { Trash2, Clock, DollarSign } from '@lucide/svelte';
	import type { Pipeline } from '$types/index';

	let {
		pipeline,
		onClick,
		onDelete
	}: {
		pipeline: Pipeline;
		onClick: (p: Pipeline) => void;
		onDelete: (p: Pipeline) => void;
	} = $props();

	const statusColors: Record<string, string> = {
		draft: 'bg-gray-500/20 text-gray-400',
		ready: 'bg-blue-500/20 text-blue-400',
		running: 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] animate-pulse',
		paused: 'bg-yellow-500/20 text-yellow-400',
		completed: 'bg-green-500/20 text-green-400',
		failed: 'bg-red-500/20 text-red-400'
	};

	function formatDuration(ms: number): string {
		if (ms < 1000) return `${ms}ms`;
		const s = Math.round(ms / 1000);
		if (s < 60) return `${s}s`;
		return `${Math.floor(s / 60)}m ${s % 60}s`;
	}

	function formatDate(date: string): string {
		return new Date(date + 'Z').toLocaleDateString('es', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="glass w-full cursor-pointer rounded-lg border border-[var(--color-border)] p-4 text-left transition-colors hover:border-[var(--color-accent)]/30"
	onclick={() => onClick(pipeline)}
>
	<div class="flex items-start justify-between gap-3">
		<div class="min-w-0 flex-1">
			<div class="flex items-center gap-2">
				<h3 class="truncate text-sm font-medium text-[var(--color-text-primary)]">
					{pipeline.name}
				</h3>
				<span
					class="inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium {statusColors[
						pipeline.status
					] ?? statusColors.draft}"
				>
					{pipeline.status}
				</span>
			</div>
			{#if pipeline.description}
				<p class="mt-1 truncate text-xs text-[var(--color-text-muted)]">
					{pipeline.description}
				</p>
			{/if}
			<div class="mt-2 flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
				{#if pipeline.source_type}
					<span class="rounded bg-[var(--color-bg-card)] px-1.5 py-0.5">
						{pipeline.source_type}
					</span>
				{/if}
				{#if pipeline.total_cost > 0}
					<span class="flex items-center gap-1">
						<DollarSign class="h-3 w-3" />
						${pipeline.total_cost.toFixed(4)}
					</span>
				{/if}
				{#if pipeline.total_duration_ms > 0}
					<span class="flex items-center gap-1">
						<Clock class="h-3 w-3" />
						{formatDuration(pipeline.total_duration_ms)}
					</span>
				{/if}
				<span>{formatDate(pipeline.created_at)}</span>
			</div>
		</div>
		<button
			class="shrink-0 rounded p-1 text-[var(--color-text-muted)] hover:bg-red-500/10 hover:text-red-400"
			onclick={(e: MouseEvent) => { e.stopPropagation(); onDelete(pipeline); }}
		>
			<Trash2 class="h-3.5 w-3.5" />
		</button>
	</div>
</div>
