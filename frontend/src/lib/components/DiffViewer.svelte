<script lang="ts">
	import { ChevronDown, ChevronRight, GitBranch } from '@lucide/svelte';
	import { fetchSessionDiff } from '$services/api';
	import type { SessionDiff } from '$types/index';

	let {
		sessionId,
		collapsed = true
	}: {
		sessionId: string;
		collapsed?: boolean;
	} = $props();

	let manualToggle = $state<boolean | null>(null);
	let expanded = $derived(manualToggle !== null ? manualToggle : !collapsed);
	let diff = $state<SessionDiff | null>(null);
	let hasDiff = $state(false);
	let loading = $state(false);
	let loaded = $state(false);

	async function loadDiff() {
		if (loaded) return;
		loading = true;
		try {
			const data = await fetchSessionDiff(sessionId);
			hasDiff = data.has_diff;
			diff = data.diff;
		} catch {
			hasDiff = false;
		} finally {
			loading = false;
			loaded = true;
		}
	}

	function toggle() {
		manualToggle = !expanded;
		if (!expanded && !loaded) {
			loadDiff();
		}
	}

	// Auto-load if starting expanded
	$effect(() => {
		if (expanded && !loaded) {
			loadDiff();
		}
	});

	function colorLine(line: string): string {
		if (line.startsWith('+') && !line.startsWith('+++')) return 'color: var(--color-success)';
		if (line.startsWith('-') && !line.startsWith('---')) return 'color: var(--color-error)';
		if (line.startsWith('@@')) return 'color: var(--color-info)';
		return '';
	}
</script>

<div class="glass rounded-lg">
	<button
		class="flex w-full items-center gap-2 px-3 py-2 text-left"
		onclick={toggle}
	>
		{#if expanded}
			<ChevronDown class="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
		{:else}
			<ChevronRight class="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
		{/if}
		<GitBranch class="h-3.5 w-3.5 text-[var(--color-accent)]" />
		<span class="text-xs font-medium text-[var(--color-text-primary)]">Changes</span>

		{#if diff}
			<span class="ml-auto flex items-center gap-1.5 text-[10px]">
				<span class="text-[var(--color-text-muted)]">{diff.files_changed} files</span>
				{#if diff.insertions > 0}
					<span class="text-[var(--color-success)]">+{diff.insertions}</span>
				{/if}
				{#if diff.deletions > 0}
					<span class="text-[var(--color-error)]">-{diff.deletions}</span>
				{/if}
			</span>
		{/if}
	</button>

	{#if expanded}
		<div class="border-t border-[var(--color-border)] px-3 py-2">
			{#if loading}
				<span class="text-xs text-[var(--color-text-muted)]">Loading diff...</span>
			{:else if !hasDiff}
				<span class="text-xs text-[var(--color-text-muted)]">No changes detected</span>
			{:else if diff?.diff_content}
				<pre class="max-h-80 overflow-y-auto font-mono text-[11px] leading-relaxed whitespace-pre-wrap">{#each diff.diff_content.split('\n') as line}<span style={colorLine(line)}>{line}
</span>{/each}</pre>
			{:else if diff?.diff_stat}
				<pre class="font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-[var(--color-text-secondary)]">{diff.diff_stat}</pre>
			{/if}
		</div>
	{/if}
</div>
