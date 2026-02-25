<script lang="ts">
	import type { CostByWorkspace } from '$types/index';

	let { data = [] }: { data: CostByWorkspace[] } = $props();

	const maxCost = $derived(Math.max(...data.map((d) => d.total_cost), 0.001));
</script>

<div class="glass rounded-xl p-4">
	<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
		Cost by Workspace
	</p>

	{#if data.length === 0}
		<p class="py-4 text-center text-xs text-[var(--color-text-muted)]">No data yet</p>
	{:else}
		<div class="flex flex-col gap-2.5">
			{#each data as item}
				{@const pct = (item.total_cost / maxCost) * 100}
				<div>
					<div class="mb-1 flex items-center justify-between text-xs">
						<span class="text-[var(--color-text-secondary)]">{item.workspace_name}</span>
						<span class="font-medium text-[var(--color-text-primary)]">
							${item.total_cost.toFixed(4)}
						</span>
					</div>
					<div class="h-2 overflow-hidden rounded-full bg-[var(--color-bg-input)]">
						<div
							class="h-full rounded-full transition-all duration-500"
							style="width: {pct}%; background: linear-gradient(90deg, var(--color-accent-dim), var(--color-accent));"
						></div>
					</div>
					<div class="mt-0.5 flex justify-between text-[10px] text-[var(--color-text-muted)]">
						<span>{item.tenant_name}</span>
						<span>{item.session_count} sessions</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
