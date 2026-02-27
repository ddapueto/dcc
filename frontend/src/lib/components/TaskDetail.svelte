<script lang="ts">
	import { CircleDot, Clock, Layers } from '@lucide/svelte';
	import MarkdownRenderer from './MarkdownRenderer.svelte';
	import type { MonitorTask } from '$types/index';

	let {
		task,
		allTasks = []
	}: {
		task: MonitorTask | null;
		allTasks?: MonitorTask[];
	} = $props();

	const statusColors: Record<string, string> = {
		running: 'text-[var(--color-accent)]',
		completed: 'text-green-400',
		failed: 'text-red-400'
	};

	function formatDuration(ms: number | null): string {
		if (ms === null) return '-';
		if (ms < 1000) return `${ms}ms`;
		if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
		return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
	}

	let childrenCount = $derived(
		task ? allTasks.filter((t) => t.parent_id === task.id).length : 0
	);
</script>

<div
	class="glass flex h-full flex-col overflow-hidden rounded-lg border border-[var(--color-border)]"
>
	{#if !task}
		<div class="flex flex-1 items-center justify-center">
			<p class="text-sm text-[var(--color-text-muted)]">Select a task to view details</p>
		</div>
	{:else}
		<div class="border-b border-[var(--color-border)] p-3">
			<div class="flex items-center gap-2">
				<CircleDot class="h-4 w-4 {statusColors[task.status] ?? 'text-gray-400'}" />
				<h3 class="text-sm font-medium text-[var(--color-text-primary)]">{task.tool_name}</h3>
				<span
					class="rounded-full bg-[var(--color-bg-card)] px-2 py-0.5 text-[10px] {statusColors[task.status] ?? 'text-gray-400'}"
				>
					{task.status}
				</span>
			</div>
			{#if task.description}
				<p class="mt-1 text-xs text-[var(--color-text-muted)]">{task.description}</p>
			{/if}
		</div>

		<div
			class="flex flex-wrap gap-2 border-b border-[var(--color-border)] px-3 py-2 text-[10px]"
		>
			<span
				class="rounded bg-[var(--color-accent)]/10 px-1.5 py-0.5 text-[var(--color-accent)]"
			>
				{task.tool_name}
			</span>
			{#if task.duration_ms !== null}
				<span
					class="flex items-center gap-1 rounded bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[var(--color-text-muted)]"
				>
					<Clock class="h-2.5 w-2.5" />
					{formatDuration(task.duration_ms)}
				</span>
			{/if}
			<span
				class="rounded bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[var(--color-text-muted)]"
			>
				Depth {task.depth}
			</span>
			{#if childrenCount > 0}
				<span
					class="flex items-center gap-1 rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400"
				>
					<Layers class="h-2.5 w-2.5" />
					{childrenCount} subtask{childrenCount !== 1 ? 's' : ''}
				</span>
			{/if}
		</div>

		{#if task.input_summary}
			<div class="border-b border-[var(--color-border)] p-3">
				<p class="mb-1 text-[10px] font-medium text-[var(--color-text-muted)]">Input</p>
				<pre
					class="overflow-auto rounded bg-[var(--color-bg-card)] p-2 text-[11px] text-[var(--color-text-secondary)]"
				>{task.input_summary}</pre>
			</div>
		{/if}

		<div class="flex-1 overflow-y-auto p-3">
			{#if task.status === 'failed' && task.output_summary}
				<p class="mb-1 text-[10px] font-medium text-red-400">Error</p>
				<pre
					class="overflow-auto rounded border border-red-500/20 bg-red-500/5 p-2 text-[11px] text-red-300"
				>{task.output_summary}</pre>
			{:else if task.output_summary && task.status === 'completed'}
				<p class="mb-1 text-[10px] font-medium text-[var(--color-text-muted)]">Output</p>
				<div class="prose-sm">
					<MarkdownRenderer content={task.output_summary} />
				</div>
			{:else if task.status === 'running'}
				<div class="flex items-center gap-2 text-sm text-[var(--color-accent)]">
					<span class="h-2 w-2 animate-pulse rounded-full bg-[var(--color-accent)]"></span>
					Running...
				</div>
			{:else}
				<p class="text-xs text-[var(--color-text-muted)]">No output yet</p>
			{/if}
		</div>
	{/if}
</div>
