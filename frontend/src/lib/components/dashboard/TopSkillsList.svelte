<script lang="ts">
	import type { TopSkillItem } from '$types/index';

	let { data = [] }: { data: TopSkillItem[] } = $props();

	const maxCount = $derived(Math.max(...data.map((d) => d.count), 1));

	const kindColors: Record<string, string> = {
		skill: 'var(--color-accent)',
		agent: 'var(--color-info)',
		prompt: 'var(--color-text-muted)'
	};
</script>

<div class="glass rounded-xl p-4">
	<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
		Top Skills & Agents
	</p>

	{#if data.length === 0}
		<p class="py-4 text-center text-xs text-[var(--color-text-muted)]">No data yet</p>
	{:else}
		<div class="flex flex-col gap-2">
			{#each data as item, i}
				{@const pct = (item.count / maxCount) * 100}
				<div class="flex items-center gap-3">
					<span class="w-4 text-right text-[10px] font-bold text-[var(--color-text-muted)]">
						{i + 1}
					</span>
					<div class="flex-1">
						<div class="mb-0.5 flex items-center justify-between">
							<span class="text-xs font-medium" style="color: {kindColors[item.kind]}">
								{item.name}
							</span>
							<span class="text-[10px] text-[var(--color-text-muted)]">
								{item.count}x · ${item.total_cost.toFixed(4)}
							</span>
						</div>
						<div class="h-1.5 overflow-hidden rounded-full bg-[var(--color-bg-input)]">
							<div
								class="h-full rounded-full transition-all duration-500"
								style="width: {pct}%; background: {kindColors[item.kind]};"
							></div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
