<script lang="ts">
	import type { AgentUsageStats } from '$types/index';

	let {
		stats,
		onSelectAgent
	}: {
		stats: AgentUsageStats[];
		onSelectAgent?: (name: string) => void;
	} = $props();

	let sortKey = $state<keyof AgentUsageStats>('sessions');
	let sortDir = $state<'asc' | 'desc'>('desc');

	let sorted = $derived(
		[...stats].sort((a, b) => {
			const av = a[sortKey] ?? 0;
			const bv = b[sortKey] ?? 0;
			return sortDir === 'desc' ? (bv as number) - (av as number) : (av as number) - (bv as number);
		})
	);

	function toggleSort(key: keyof AgentUsageStats) {
		if (sortKey === key) {
			sortDir = sortDir === 'desc' ? 'asc' : 'desc';
		} else {
			sortKey = key;
			sortDir = 'desc';
		}
	}

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}

	function formatDuration(ms: number | null): string {
		if (ms === null) return '-';
		if (ms < 1000) return `${Math.round(ms)}ms`;
		if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
		return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
	}

	const headers: { key: keyof AgentUsageStats; label: string }[] = [
		{ key: 'name', label: 'Agent' },
		{ key: 'sessions', label: 'Sessions' },
		{ key: 'total_cost', label: 'Cost' },
		{ key: 'avg_duration_ms', label: 'Avg Duration' },
		{ key: 'success_rate', label: 'Success' }
	];
</script>

<div class="glass rounded-lg border border-[var(--color-border)]">
	<div class="border-b border-[var(--color-border)] px-4 py-2">
		<h3 class="text-xs font-semibold text-[var(--color-text-primary)]">Agent Stats</h3>
	</div>
	<div class="overflow-x-auto">
		<table class="w-full text-left text-xs">
			<thead>
				<tr class="border-b border-[var(--color-border)]">
					{#each headers as header}
						<th class="px-4 py-2">
							<button
								class="font-medium text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text-primary)]"
								onclick={() => toggleSort(header.key)}
							>
								{header.label}
								{#if sortKey === header.key}
									<span class="ml-0.5 text-[var(--color-accent)]"
										>{sortDir === 'desc' ? '↓' : '↑'}</span
									>
								{/if}
							</button>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each sorted as stat}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<tr
						class="cursor-pointer border-b border-[var(--color-border)] transition-colors last:border-b-0 hover:bg-[var(--color-bg-card)]"
						onclick={() => onSelectAgent?.(stat.name)}
					>
						<td class="px-4 py-2 font-medium text-[var(--color-accent)]">@{stat.name}</td>
						<td class="px-4 py-2 text-[var(--color-text-secondary)]">{stat.sessions}</td>
						<td class="px-4 py-2 text-[var(--color-text-secondary)]"
							>{formatCost(stat.total_cost)}</td
						>
						<td class="px-4 py-2 text-[var(--color-text-secondary)]"
							>{formatDuration(stat.avg_duration_ms)}</td
						>
						<td class="px-4 py-2">
							<span
								class="rounded-full px-1.5 py-0.5 text-[10px] {stat.success_rate >= 80
									? 'bg-green-500/10 text-green-400'
									: stat.success_rate >= 50
										? 'bg-yellow-500/10 text-yellow-400'
										: 'bg-red-500/10 text-red-400'}"
							>
								{stat.success_rate}%
							</span>
						</td>
					</tr>
				{/each}
				{#if sorted.length === 0}
					<tr>
						<td
							colspan="5"
							class="px-4 py-6 text-center text-[var(--color-text-muted)]"
						>
							No agent usage data yet
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>
</div>
