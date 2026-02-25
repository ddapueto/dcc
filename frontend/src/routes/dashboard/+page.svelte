<script lang="ts">
	import { onMount } from 'svelte';
	import { DollarSign, Calendar, Clock, Cpu, RefreshCw } from '@lucide/svelte';
	import Shell from '$lib/components/Shell.svelte';
	import StatCard from '$lib/components/dashboard/StatCard.svelte';
	import StatusDonut from '$lib/components/dashboard/StatusDonut.svelte';
	import CostBarChart from '$lib/components/dashboard/CostBarChart.svelte';
	import CostTrendChart from '$lib/components/dashboard/CostTrendChart.svelte';
	import TopSkillsList from '$lib/components/dashboard/TopSkillsList.svelte';
	import { analyticsStore } from '$stores/analytics.svelte';

	onMount(() => {
		analyticsStore.fetchAll();
	});

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}

	function formatTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
		return String(n);
	}
</script>

<Shell>
	{#snippet topbar()}
		<span class="text-sm font-semibold text-[var(--color-text-primary)]">Dashboard</span>
		<div class="ml-auto">
			<button
				onclick={() => analyticsStore.fetchAll()}
				disabled={analyticsStore.loading}
				class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)] disabled:opacity-50"
			>
				<RefreshCw class="h-3.5 w-3.5 {analyticsStore.loading ? 'animate-spin' : ''}" />
				Refresh
			</button>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="p-6">
			{#if analyticsStore.error}
				<div class="mb-4 rounded-lg bg-[var(--color-error)]/10 px-4 py-3 text-sm text-[var(--color-error)]">
					{analyticsStore.error}
				</div>
			{/if}

			<!-- Row 1: Stat cards -->
			<div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<StatCard
					label="Total Cost"
					value={formatCost(analyticsStore.summary?.total_cost ?? 0)}
					sublabel="{analyticsStore.summary?.total_sessions ?? 0} sessions"
					icon={DollarSign}
				/>
				<StatCard
					label="Last 7 Days"
					value={formatCost(analyticsStore.summary?.cost_7d ?? 0)}
					sublabel="{analyticsStore.summary?.sessions_7d ?? 0} sessions"
					icon={Calendar}
				/>
				<StatCard
					label="Last 24 Hours"
					value={formatCost(analyticsStore.summary?.cost_24h ?? 0)}
					sublabel="{analyticsStore.summary?.sessions_24h ?? 0} sessions"
					icon={Clock}
				/>
				<StatCard
					label="Total Tokens"
					value={formatTokens(
						(analyticsStore.summary?.total_input_tokens ?? 0) +
							(analyticsStore.summary?.total_output_tokens ?? 0)
					)}
					sublabel="in: {formatTokens(analyticsStore.summary?.total_input_tokens ?? 0)} · out: {formatTokens(analyticsStore.summary?.total_output_tokens ?? 0)}"
					icon={Cpu}
				/>
			</div>

			<!-- Row 2: Trend + Donut -->
			<div class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
				<div class="lg:col-span-2">
					<CostTrendChart data={analyticsStore.costTrend} />
				</div>
				<StatusDonut byStatus={analyticsStore.summary?.by_status ?? {}} />
			</div>

			<!-- Row 3: Cost bars + Top skills -->
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
				<CostBarChart data={analyticsStore.costByWorkspace} />
				<TopSkillsList data={analyticsStore.topSkills} />
			</div>
		</div>
	{/snippet}
</Shell>
