<script lang="ts">
	import { CircleDot, ExternalLink, ArrowRight } from '@lucide/svelte';
	import MarkdownRenderer from './MarkdownRenderer.svelte';
	import type { PipelineStep, PipelineStatus } from '$types/index';

	let {
		step,
		pipelineStatus
	}: {
		step: PipelineStep | null;
		pipelineStatus: PipelineStatus;
	} = $props();

	const statusColors: Record<string, string> = {
		pending: 'text-gray-400',
		running: 'text-[var(--color-accent)]',
		completed: 'text-green-400',
		failed: 'text-red-400',
		skipped: 'text-gray-500'
	};
</script>

<div class="glass flex h-full flex-col overflow-hidden rounded-lg border border-[var(--color-border)]">
	{#if !step}
		<div class="flex flex-1 items-center justify-center">
			<p class="text-sm text-[var(--color-text-muted)]">Select a step to view details</p>
		</div>
	{:else}
		<div class="border-b border-[var(--color-border)] p-3">
			<div class="flex items-center gap-2">
				<CircleDot class="h-4 w-4 {statusColors[step.status] ?? 'text-gray-400'}" />
				<h3 class="text-sm font-medium text-[var(--color-text-primary)]">{step.name}</h3>
				<span
					class="rounded-full bg-[var(--color-bg-card)] px-2 py-0.5 text-[10px] {statusColors[step.status] ?? 'text-gray-400'}"
				>
					{step.status}
				</span>
			</div>
			{#if step.description}
				<p class="mt-1 text-xs text-[var(--color-text-muted)]">{step.description}</p>
			{/if}
		</div>

		<div class="flex flex-wrap gap-2 border-b border-[var(--color-border)] px-3 py-2 text-[10px]">
			{#if step.agent}
				<span class="rounded bg-[var(--color-accent)]/10 px-1.5 py-0.5 text-[var(--color-accent)]">
					@{step.agent}
				</span>
			{/if}
			{#if step.skill}
				<span class="rounded bg-blue-500/10 px-1.5 py-0.5 text-blue-400">
					/{step.skill}
				</span>
			{/if}
			{#if step.model}
				<span class="rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400">
					{step.model}
				</span>
			{/if}
			<span class="rounded bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[var(--color-text-muted)]">
				Position #{step.position}
			</span>
		</div>

		{#if step.depends_on.length > 0}
			<div class="flex items-center gap-1.5 border-b border-[var(--color-border)] px-3 py-2 text-[10px] text-[var(--color-text-muted)]">
				<ArrowRight class="h-3 w-3" />
				Depends on: {step.depends_on.length} step{step.depends_on.length !== 1 ? 's' : ''}
			</div>
		{/if}

		{#if step.prompt_template}
			<div class="border-b border-[var(--color-border)] p-3">
				<p class="mb-1 text-[10px] font-medium text-[var(--color-text-muted)]">Prompt Template</p>
				<pre class="overflow-auto rounded bg-[var(--color-bg-card)] p-2 text-[11px] text-[var(--color-text-secondary)]">{step.prompt_template}</pre>
			</div>
		{/if}

		<div class="flex-1 overflow-y-auto p-3">
			{#if step.output_summary && (step.status === 'completed' || step.status === 'failed')}
				<p class="mb-1 text-[10px] font-medium text-[var(--color-text-muted)]">Output</p>
				<div class="prose-sm">
					<MarkdownRenderer content={step.output_summary} />
				</div>
			{:else if step.status === 'running'}
				<div class="flex items-center gap-2 text-sm text-[var(--color-accent)]">
					<span class="h-2 w-2 animate-pulse rounded-full bg-[var(--color-accent)]"></span>
					Running...
				</div>
			{:else}
				<p class="text-xs text-[var(--color-text-muted)]">No output yet</p>
			{/if}
		</div>

		{#if step.session_id}
			<div class="border-t border-[var(--color-border)] p-3">
				<a
					href="/history"
					class="flex items-center gap-1.5 text-[10px] text-[var(--color-accent)] hover:underline"
				>
					<ExternalLink class="h-3 w-3" />
					View full session
				</a>
			</div>
		{/if}
	{/if}
</div>
