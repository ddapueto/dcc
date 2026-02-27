<script lang="ts">
	import { Play, Trash2 } from '@lucide/svelte';
	import type { Workflow } from '$types/index';

	let {
		workflow,
		onClick,
		onDelete
	}: {
		workflow: Workflow;
		onClick: (workflow: Workflow) => void;
		onDelete?: (workflow: Workflow) => void;
	} = $props();

	const categoryColors: Record<string, string> = {
		development: 'bg-blue-500/10 text-blue-400',
		testing: 'bg-green-500/10 text-green-400',
		review: 'bg-purple-500/10 text-purple-400',
		devops: 'bg-orange-500/10 text-orange-400',
		custom: 'bg-gray-500/10 text-gray-400'
	};
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="glass group cursor-pointer rounded-lg border border-[var(--color-border)] p-4 transition-all hover:border-[var(--color-accent)]/30"
	onclick={() => onClick(workflow)}
>
	<div class="flex items-start justify-between">
		<div class="flex items-center gap-2">
			<div
				class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent)]/10"
			>
				<Play class="h-4 w-4 text-[var(--color-accent)]" />
			</div>
			<div>
				<h3 class="text-sm font-medium text-[var(--color-text-primary)]">{workflow.name}</h3>
				<span
					class="inline-block rounded px-1.5 py-0.5 text-[10px] {categoryColors[workflow.category] ?? categoryColors.custom}"
				>
					{workflow.category}
				</span>
			</div>
		</div>

		{#if !workflow.is_builtin && onDelete}
			<button
				class="rounded p-1 text-[var(--color-text-muted)] opacity-0 transition-opacity hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
				onclick={(e: MouseEvent) => { e.stopPropagation(); onDelete?.(workflow); }}
				title="Delete workflow"
			>
				<Trash2 class="h-3.5 w-3.5" />
			</button>
		{/if}
	</div>

	{#if workflow.description}
		<p class="mt-2 line-clamp-2 text-xs text-[var(--color-text-muted)]">
			{workflow.description}
		</p>
	{/if}

	<div class="mt-3 flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
		{#if workflow.usage_count > 0}
			<span>{workflow.usage_count} uses</span>
		{/if}
		{#if workflow.model}
			<span class="rounded bg-purple-500/10 px-1 py-0.5 text-purple-400">
				{workflow.model}
			</span>
		{/if}
		{#if workflow.is_builtin}
			<span class="rounded bg-[var(--color-bg-card)] px-1 py-0.5">built-in</span>
		{/if}
	</div>
</div>
