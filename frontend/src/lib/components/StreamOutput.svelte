<script lang="ts">
	import { MessageSquare, AlertCircle } from '@lucide/svelte';
	import type { TabSession } from '$stores/tabs.svelte';

	let { session }: { session: TabSession } = $props();

	let outputEl: HTMLDivElement | undefined = $state();

	// Auto-scroll on new content
	$effect(() => {
		const _ = session.outputChunks.length;
		if (outputEl) {
			outputEl.scrollTop = outputEl.scrollHeight;
		}
	});
</script>

<div class="flex h-full flex-col">
	{#if session.status === 'idle' && session.outputChunks.length === 0}
		<div class="flex flex-1 items-center justify-center">
			<div class="text-center">
				<MessageSquare class="mx-auto mb-2 h-8 w-8 text-[var(--color-text-muted)]" />
				<p class="text-sm text-[var(--color-text-muted)]">
					Seleccioná un workspace y ejecutá un skill o prompt
				</p>
			</div>
		</div>
	{:else}
		<div
			bind:this={outputEl}
			class="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap text-[var(--color-text-primary)]"
		>
			{session.fullOutput}
			{#if session.status === 'running'}
				<span class="inline-block h-4 w-1.5 animate-pulse bg-[var(--color-accent)]"></span>
			{/if}
		</div>

		{#if session.status === 'error' && session.errorMsg}
			<div class="flex items-center gap-2 border-t border-[var(--color-error)]/20 bg-[var(--color-error)]/5 px-4 py-2">
				<AlertCircle class="h-4 w-4 shrink-0 text-[var(--color-error)]" />
				<span class="text-xs text-[var(--color-error)]">{session.errorMsg}</span>
			</div>
		{/if}
	{/if}
</div>
