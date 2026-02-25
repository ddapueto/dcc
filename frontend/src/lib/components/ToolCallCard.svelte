<script lang="ts">
	import type { ToolCall } from '$types/index';
	import { Wrench, Check, AlertCircle, Loader2, ChevronDown, ChevronRight } from '@lucide/svelte';

	let { toolCall }: { toolCall: ToolCall } = $props();

	let expanded = $state(false);

</script>

<div class="glass rounded-lg">
	<button
		class="flex w-full items-center gap-2 px-3 py-2 text-left"
		onclick={() => (expanded = !expanded)}
	>
		<Wrench class="h-3.5 w-3.5 shrink-0 text-[var(--color-accent)]" />
		<span class="min-w-0 flex-1 truncate text-xs font-medium text-[var(--color-text-primary)]">
			{toolCall.name}
		</span>
		{#if toolCall.status === 'running'}
			<Loader2 class="h-3.5 w-3.5 shrink-0 animate-spin text-[var(--color-warning)]" />
		{:else if toolCall.status === 'error'}
			<AlertCircle class="h-3.5 w-3.5 shrink-0 text-[var(--color-error)]" />
		{:else}
			<Check class="h-3.5 w-3.5 shrink-0 text-[var(--color-success)]" />
		{/if}
		{#if expanded}
			<ChevronDown class="h-3 w-3 text-[var(--color-text-muted)]" />
		{:else}
			<ChevronRight class="h-3 w-3 text-[var(--color-text-muted)]" />
		{/if}
	</button>

	{#if expanded}
		<div class="border-t border-[var(--color-border)] px-3 py-2">
			{#if toolCall.input}
				<div class="mb-2">
					<span class="text-[10px] font-semibold uppercase text-[var(--color-text-muted)]">Input</span>
					<pre class="mt-0.5 max-h-32 overflow-auto rounded bg-[var(--color-bg-input)] p-2 text-[11px] text-[var(--color-text-secondary)]">{toolCall.input}</pre>
				</div>
			{/if}
			{#if toolCall.result}
				<div>
					<span class="text-[10px] font-semibold uppercase text-[var(--color-text-muted)]">Result</span>
					<pre
						class="mt-0.5 max-h-48 overflow-auto rounded p-2 text-[11px]
						{toolCall.isError
							? 'bg-[var(--color-error)]/5 text-[var(--color-error)]'
							: 'bg-[var(--color-bg-input)] text-[var(--color-text-secondary)]'}"
					>{toolCall.result}</pre>
				</div>
			{/if}
		</div>
	{/if}
</div>
