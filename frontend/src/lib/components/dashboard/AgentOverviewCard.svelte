<script lang="ts">
	import { Bot } from '@lucide/svelte';
	import type { AgentUsageStats } from '$types/index';

	let {
		stats
	}: {
		stats: AgentUsageStats[];
	} = $props();

	let top5 = $derived(
		[...stats]
			.sort((a, b) => b.sessions - a.sessions)
			.slice(0, 5)
	);

	let maxSessions = $derived(Math.max(1, ...top5.map((s) => s.sessions)));

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}
</script>

<div class="glass rounded-lg border border-[var(--color-border)]">
	<div class="flex items-center gap-2 border-b border-[var(--color-border)] px-4 py-2.5">
		<Bot class="h-3.5 w-3.5 text-[var(--color-accent)]" />
		<h3 class="text-xs font-semibold text-[var(--color-text-primary)]">Top Agents</h3>
	</div>
	<div class="p-4">
		{#if top5.length === 0}
			<p class="py-4 text-center text-xs text-[var(--color-text-muted)]">No agent data yet</p>
		{:else}
			<div class="flex flex-col gap-3">
				{#each top5 as stat, i}
					<div>
						<div class="mb-1 flex items-center justify-between text-xs">
							<span class="font-medium text-[var(--color-text-primary)]">
								@{stat.name}
							</span>
							<span class="text-[var(--color-text-muted)]">
								{stat.sessions} · {formatCost(stat.total_cost)}
							</span>
						</div>
						<div class="h-2 overflow-hidden rounded-full bg-[var(--color-bg-card)]">
							<div
								class="h-full rounded-full transition-all"
								style="width: {(stat.sessions / maxSessions) * 100}%;
								       background: {i === 0
									? '#00d4aa'
									: i === 1
										? '#22c55e'
										: i === 2
											? '#3b82f6'
											: i === 3
												? '#a855f7'
												: '#6b7280'}"
							></div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
