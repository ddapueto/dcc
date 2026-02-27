<script lang="ts">
	import { Bot, Wrench, Repeat, Shield } from '@lucide/svelte';
	import type { RegisteredAgent, AgentUsageStats } from '$types/index';

	let {
		agent,
		stats,
		selected = false,
		onclick
	}: {
		agent: RegisteredAgent;
		stats?: AgentUsageStats | null;
		selected?: boolean;
		onclick?: (agent: RegisteredAgent) => void;
	} = $props();

	const modelColors: Record<string, string> = {
		opus: 'bg-purple-500/20 text-purple-400',
		sonnet: 'bg-blue-500/20 text-blue-400',
		haiku: 'bg-green-500/20 text-green-400'
	};

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="glass cursor-pointer rounded-lg border p-4 transition-all hover:border-[var(--color-glass-border-hover)] {selected
		? 'border-[var(--color-accent)] shadow-lg shadow-[var(--color-accent)]/10'
		: 'border-[var(--color-border)]'}"
	onclick={() => onclick?.(agent)}
>
	<div class="flex items-start justify-between">
		<div class="flex items-center gap-2">
			<Bot class="h-4 w-4 text-[var(--color-accent)]" />
			<h3 class="text-sm font-medium text-[var(--color-text-primary)]">{agent.name}</h3>
		</div>
		{#if agent.model}
			<span
				class="rounded-full px-2 py-0.5 text-[10px] font-medium {modelColors[agent.model] ?? 'bg-[var(--color-bg-input)] text-[var(--color-text-muted)]'}"
			>
				{agent.model}
			</span>
		{/if}
	</div>

	{#if agent.description}
		<p class="mt-1.5 text-xs text-[var(--color-text-muted)] line-clamp-2">
			{agent.description}
		</p>
	{/if}

	<!-- Badges -->
	<div class="mt-3 flex flex-wrap gap-1.5">
		{#if agent.tools.length > 0}
			<span
				class="flex items-center gap-1 rounded bg-[var(--color-bg-input)] px-1.5 py-0.5 text-[9px] text-[var(--color-text-muted)]"
			>
				<Wrench class="h-2.5 w-2.5" />
				{agent.tools.length} tools
			</span>
		{/if}
		{#if agent.max_turns}
			<span
				class="flex items-center gap-1 rounded bg-[var(--color-bg-input)] px-1.5 py-0.5 text-[9px] text-[var(--color-text-muted)]"
			>
				<Repeat class="h-2.5 w-2.5" />
				{agent.max_turns} turns
			</span>
		{/if}
		{#if agent.isolation}
			<span
				class="flex items-center gap-1 rounded bg-orange-500/10 px-1.5 py-0.5 text-[9px] text-orange-400"
			>
				<Shield class="h-2.5 w-2.5" />
				{agent.isolation}
			</span>
		{/if}
	</div>

	<!-- Stats -->
	{#if stats}
		<div class="mt-3 flex items-center gap-3 border-t border-[var(--color-border)] pt-2">
			<span class="text-[10px] text-[var(--color-text-muted)]">
				{stats.sessions} sessions
			</span>
			<span class="text-[10px] text-[var(--color-accent)]">
				{formatCost(stats.total_cost)}
			</span>
			<span class="text-[10px] text-green-400">
				{stats.success_rate}%
			</span>
		</div>
	{/if}
</div>
