<script lang="ts">
	import { Send, Square, Loader2 } from '@lucide/svelte';

	let {
		running = false,
		disabled = false,
		selectedSkill = null,
		selectedAgent = null,
		onSubmit,
		onCancel
	}: {
		running?: boolean;
		disabled?: boolean;
		selectedSkill?: string | null;
		selectedAgent?: string | null;
		onSubmit?: (prompt: string) => void;
		onCancel?: () => void;
	} = $props();

	let prompt = $state('');

	function handleSubmit() {
		const text = prompt.trim();
		if (!text || disabled) return;
		onSubmit?.(text);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			handleSubmit();
		}
	}
</script>

<div class="glass rounded-xl p-3">
	<!-- Context chips -->
	{#if selectedSkill || selectedAgent}
		<div class="mb-2 flex items-center gap-2">
			{#if selectedSkill}
				<span class="rounded-full bg-[var(--color-accent)]/10 px-2.5 py-0.5 text-xs font-medium text-[var(--color-accent)]">
					/{selectedSkill}
				</span>
			{/if}
			{#if selectedAgent}
				<span class="rounded-full bg-[var(--color-info)]/10 px-2.5 py-0.5 text-xs font-medium text-[var(--color-info)]">
					@{selectedAgent}
				</span>
			{/if}
		</div>
	{/if}

	<!-- Input area -->
	<div class="flex gap-2">
		<textarea
			bind:value={prompt}
			onkeydown={handleKeydown}
			placeholder={selectedSkill
				? `Describe what to do with /${selectedSkill}...`
				: 'Enter your prompt...'}
			disabled={running}
			rows={2}
			class="flex-1 resize-none rounded-lg bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] disabled:opacity-50"
		></textarea>

		{#if running}
			<button
				onclick={() => onCancel?.()}
				class="flex h-10 w-10 shrink-0 items-center justify-center self-end rounded-lg bg-[var(--color-error)] text-white transition-colors hover:bg-[var(--color-error)]/80"
				title="Cancel (Esc)"
			>
				<Square class="h-4 w-4" />
			</button>
		{:else}
			<button
				onclick={handleSubmit}
				disabled={!prompt.trim() || disabled}
				class="flex h-10 w-10 shrink-0 items-center justify-center self-end rounded-lg bg-[var(--color-accent)] text-[var(--color-bg-primary)] transition-colors hover:bg-[var(--color-accent-light)] disabled:opacity-30 disabled:cursor-not-allowed"
				title="Run (Cmd+Enter)"
			>
				<Send class="h-4 w-4" />
			</button>
		{/if}
	</div>

	<div class="mt-1 text-right text-[10px] text-[var(--color-text-muted)]">
		{running ? 'Running...' : 'Cmd+Enter to run'}
	</div>
</div>
