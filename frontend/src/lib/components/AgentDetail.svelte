<script lang="ts">
	import { Bot, Clock, Wrench, Repeat, Shield, TrendingUp, X } from '@lucide/svelte';
	import CostTrendChart from './dashboard/CostTrendChart.svelte';
	import type { RegisteredAgent, AgentUsageStats, CostTrendPoint } from '$types/index';

	let {
		agent,
		stats,
		trend = [],
		onClose
	}: {
		agent: RegisteredAgent;
		stats?: AgentUsageStats | null;
		trend?: CostTrendPoint[];
		onClose?: () => void;
	} = $props();

	const modelColors: Record<string, string> = {
		opus: 'bg-purple-500/20 text-purple-400',
		sonnet: 'bg-blue-500/20 text-blue-400',
		haiku: 'bg-green-500/20 text-green-400'
	};

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}

	function formatDuration(ms: number | null): string {
		if (ms === null) return '-';
		if (ms < 1000) return `${Math.round(ms)}ms`;
		if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
		return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
	}
</script>

<div class="glass flex h-full flex-col rounded-lg border border-[var(--color-border)]">
	<!-- Header -->
	<div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
		<div class="flex items-center gap-2">
			<Bot class="h-4 w-4 text-[var(--color-accent)]" />
			<h2 class="text-sm font-semibold text-[var(--color-text-primary)]">{agent.name}</h2>
			{#if agent.model}
				<span
					class="rounded-full px-2 py-0.5 text-[10px] font-medium {modelColors[agent.model] ?? 'bg-[var(--color-bg-input)] text-[var(--color-text-muted)]'}"
				>
					{agent.model}
				</span>
			{/if}
		</div>
		{#if onClose}
			<button
				onclick={onClose}
				class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]"
			>
				<X class="h-4 w-4" />
			</button>
		{/if}
	</div>

	<div class="flex-1 overflow-y-auto">
		<!-- Description -->
		{#if agent.description}
			<div class="border-b border-[var(--color-border)] px-4 py-3">
				<p class="text-xs text-[var(--color-text-secondary)]">{agent.description}</p>
			</div>
		{/if}

		<!-- Config badges -->
		<div class="flex flex-wrap gap-1.5 border-b border-[var(--color-border)] px-4 py-3">
			{#if agent.tools.length > 0}
				<span
					class="flex items-center gap-1 rounded bg-[var(--color-bg-input)] px-2 py-1 text-[10px] text-[var(--color-text-muted)]"
				>
					<Wrench class="h-2.5 w-2.5" />
					{agent.tools.length} tools: {agent.tools.slice(0, 5).join(', ')}{agent.tools.length > 5
						? '...'
						: ''}
				</span>
			{/if}
			{#if agent.max_turns}
				<span
					class="flex items-center gap-1 rounded bg-[var(--color-bg-input)] px-2 py-1 text-[10px] text-[var(--color-text-muted)]"
				>
					<Repeat class="h-2.5 w-2.5" />
					{agent.max_turns} max turns
				</span>
			{/if}
			{#if agent.isolation}
				<span
					class="flex items-center gap-1 rounded bg-orange-500/10 px-2 py-1 text-[10px] text-orange-400"
				>
					<Shield class="h-2.5 w-2.5" />
					{agent.isolation}
				</span>
			{/if}
			{#if agent.permission_mode}
				<span
					class="rounded bg-yellow-500/10 px-2 py-1 text-[10px] text-yellow-400"
				>
					{agent.permission_mode}
				</span>
			{/if}
			{#if agent.background}
				<span class="rounded bg-blue-500/10 px-2 py-1 text-[10px] text-blue-400">
					background
				</span>
			{/if}
		</div>

		<!-- Stats -->
		{#if stats}
			<div class="grid grid-cols-2 gap-3 border-b border-[var(--color-border)] px-4 py-3">
				<div>
					<p class="text-[10px] text-[var(--color-text-muted)]">Sessions</p>
					<p class="text-sm font-medium text-[var(--color-text-primary)]">{stats.sessions}</p>
				</div>
				<div>
					<p class="text-[10px] text-[var(--color-text-muted)]">Total Cost</p>
					<p class="text-sm font-medium text-[var(--color-accent)]">
						{formatCost(stats.total_cost)}
					</p>
				</div>
				<div>
					<p class="text-[10px] text-[var(--color-text-muted)]">Avg Duration</p>
					<p class="text-sm font-medium text-[var(--color-text-primary)]">
						{formatDuration(stats.avg_duration_ms)}
					</p>
				</div>
				<div>
					<p class="text-[10px] text-[var(--color-text-muted)]">Success Rate</p>
					<p
						class="text-sm font-medium {stats.success_rate >= 80
							? 'text-green-400'
							: stats.success_rate >= 50
								? 'text-yellow-400'
								: 'text-red-400'}"
					>
						{stats.success_rate}%
					</p>
				</div>
			</div>
		{/if}

		<!-- Cost trend -->
		{#if trend.length > 0}
			<div class="px-4 py-3">
				<div class="mb-2 flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]">
					<TrendingUp class="h-3 w-3" />
					Cost Trend (30d)
				</div>
				<CostTrendChart data={trend} />
			</div>
		{/if}
	</div>
</div>
