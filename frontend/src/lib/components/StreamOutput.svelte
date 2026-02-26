<script lang="ts">
	import { MessageSquare, AlertCircle, Copy } from '@lucide/svelte';
	import MarkdownRenderer from './MarkdownRenderer.svelte';
	import DiffViewer from './DiffViewer.svelte';
	import type { TabSession } from '$stores/tabs.svelte';

	let {
		session,
		onUseAsContext
	}: {
		session: TabSession;
		onUseAsContext?: (output: string) => void;
	} = $props();

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
			class="flex-1 overflow-y-auto p-4 text-sm leading-relaxed text-[var(--color-text-primary)]"
		>
			<MarkdownRenderer content={session.fullOutput} streaming={session.status === 'running'} />
		</div>

		{#if session.status === 'error' && session.errorMsg}
			<div class="flex items-center gap-2 border-t border-[var(--color-error)]/20 bg-[var(--color-error)]/5 px-4 py-2">
				<AlertCircle class="h-4 w-4 shrink-0 text-[var(--color-error)]" />
				<span class="text-xs text-[var(--color-error)]">{session.errorMsg}</span>
			</div>
		{/if}

		{#if session.status === 'completed' && session.sessionId}
			<div class="border-t border-[var(--color-border)] p-4">
				<DiffViewer sessionId={session.sessionId} collapsed={true} />
				{#if onUseAsContext && session.fullOutput}
					<button
						class="mt-2 flex items-center gap-1.5 rounded-lg bg-[var(--color-bg-card)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-accent)]"
						onclick={() => onUseAsContext(session.fullOutput)}
					>
						<Copy class="h-3 w-3" />
						Use as context
					</button>
				{/if}
			</div>
		{/if}
	{/if}
</div>
