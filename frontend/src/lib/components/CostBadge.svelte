<script lang="ts">
	import { Coins, Cpu, Clock, Layers } from '@lucide/svelte';
	import type { TabSession } from '$stores/tabs.svelte';

	let { session }: { session: TabSession } = $props();

	function formatCost(usd: number | null): string {
		if (usd == null) return '-';
		if (usd < 0.01) return `$${usd.toFixed(4)}`;
		return `$${usd.toFixed(2)}`;
	}

	function formatTokens(n: number | null): string {
		if (n == null) return '-';
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
		return String(n);
	}

	function formatDuration(ms: number | null): string {
		if (ms == null) return '-';
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}
</script>

<div class="flex items-center gap-4 text-[var(--color-text-secondary)]">
	<!-- Status -->
	<div class="flex items-center gap-1">
		{#if session.status === 'running'}
			<span class="h-2 w-2 animate-pulse rounded-full bg-[var(--color-accent)]"></span>
			<span>Running</span>
		{:else if session.status === 'completed'}
			<span class="h-2 w-2 rounded-full bg-[var(--color-success)]"></span>
			<span>Completed</span>
		{:else if session.status === 'error'}
			<span class="h-2 w-2 rounded-full bg-[var(--color-error)]"></span>
			<span>Error</span>
		{:else}
			<span class="h-2 w-2 rounded-full bg-[var(--color-text-muted)]"></span>
			<span>Idle</span>
		{/if}
	</div>

	<!-- Model -->
	{#if session.model}
		<div class="flex items-center gap-1">
			<Cpu class="h-3 w-3" />
			<span>{session.model}</span>
		</div>
	{/if}

	<!-- Tokens -->
	{#if session.totalTokens > 0}
		<div class="flex items-center gap-1" title="Input / Output tokens">
			<Layers class="h-3 w-3" />
			<span>{formatTokens(session.inputTokens)} / {formatTokens(session.outputTokens)}</span>
		</div>
	{/if}

	<!-- Cost -->
	{#if session.costUsd != null}
		<div class="flex items-center gap-1">
			<Coins class="h-3 w-3 text-[var(--color-accent)]" />
			<span class="text-[var(--color-accent)]">{formatCost(session.costUsd)}</span>
		</div>
	{/if}

	<!-- Duration -->
	{#if session.durationMs != null}
		<div class="flex items-center gap-1">
			<Clock class="h-3 w-3" />
			<span>{formatDuration(session.durationMs)}</span>
		</div>
	{/if}

	<!-- Turns -->
	{#if session.numTurns != null}
		<span class="text-[var(--color-text-muted)]">{session.numTurns} turns</span>
	{/if}
</div>
