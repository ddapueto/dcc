<script lang="ts">
	import { Send, Square } from '@lucide/svelte';

	const MODELS = [
		{ id: 'default', label: 'Default', value: undefined },
		{ id: 'opus', label: 'Opus', value: 'claude-opus-4-20250514' },
		{ id: 'sonnet', label: 'Sonnet', value: 'claude-sonnet-4-20250514' },
		{ id: 'haiku', label: 'Haiku', value: 'claude-haiku-4-20250514' }
	] as const;

	const HISTORY_KEY = 'dcc:prompt-history';
	const HISTORY_MAX = 50;

	let {
		running = false,
		disabled = false,
		selectedSkill = null,
		selectedAgent = null,
		prefill = null,
		onSubmit,
		onCancel
	}: {
		running?: boolean;
		disabled?: boolean;
		selectedSkill?: string | null;
		selectedAgent?: string | null;
		prefill?: string | null;
		onSubmit?: (prompt: string, model?: string) => void;
		onCancel?: () => void;
	} = $props();

	let prompt = $state('');
	let selectedModelId = $state<string>('default');

	// Prefill from external source (e.g., GitHub issue, context sharing)
	$effect(() => {
		if (prefill) {
			prompt = prefill;
		}
	});

	// Prompt history
	let historyIndex = $state(-1);
	let savedPrompt = $state('');

	function getHistory(): string[] {
		try {
			return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]');
		} catch {
			return [];
		}
	}

	function saveToHistory(text: string) {
		const history = getHistory();
		if (history[0] === text) return;
		history.unshift(text);
		if (history.length > HISTORY_MAX) history.length = HISTORY_MAX;
		localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
	}

	const selectedModel = $derived(MODELS.find((m) => m.id === selectedModelId)!);

	function handleSubmit() {
		const text = prompt.trim();
		if (!text || disabled) return;
		saveToHistory(text);
		historyIndex = -1;
		onSubmit?.(text, selectedModel.value);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			handleSubmit();
			return;
		}

		if (e.key === 'ArrowUp' && prompt === '' || (e.key === 'ArrowUp' && historyIndex >= 0)) {
			e.preventDefault();
			const history = getHistory();
			if (history.length === 0) return;
			if (historyIndex === -1) savedPrompt = prompt;
			const next = Math.min(historyIndex + 1, history.length - 1);
			historyIndex = next;
			prompt = history[next];
			return;
		}

		if (e.key === 'ArrowDown' && historyIndex >= 0) {
			e.preventDefault();
			historyIndex -= 1;
			if (historyIndex < 0) {
				prompt = savedPrompt;
			} else {
				prompt = getHistory()[historyIndex];
			}
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

	<!-- Model selector pills -->
	<div class="mb-2 flex items-center gap-1.5">
		<span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mr-1">Model</span>
		{#each MODELS as model}
			<button
				onclick={() => (selectedModelId = model.id)}
				class="rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors {selectedModelId === model.id
					? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)] ring-1 ring-[var(--color-accent)]/30'
					: 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-secondary)]'}"
			>
				{model.label}
			</button>
		{/each}
	</div>

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

	<div class="mt-1 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
		<span>⌘K new tab · ⌘W close · Esc cancel</span>
		<span>{running ? 'Running...' : 'Cmd+Enter to run'}</span>
	</div>
</div>
