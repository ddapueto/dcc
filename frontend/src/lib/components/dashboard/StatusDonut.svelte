<script lang="ts">
	let { byStatus = {} }: { byStatus: Record<string, number> } = $props();

	const statusColors: Record<string, string> = {
		completed: 'var(--color-success)',
		running: 'var(--color-accent)',
		error: 'var(--color-error)',
		cancelled: 'var(--color-warning)',
		pending: 'var(--color-text-muted)'
	};

	const total = $derived(Object.values(byStatus).reduce((a, b) => a + b, 0));

	const segments = $derived(() => {
		if (total === 0) return [];
		const entries = Object.entries(byStatus).sort((a, b) => b[1] - a[1]);
		let offset = 0;
		return entries.map(([status, count]) => {
			const pct = (count / total) * 100;
			const seg = {
				status,
				count,
				pct,
				offset,
				color: statusColors[status] ?? 'var(--color-text-muted)'
			};
			offset += pct;
			return seg;
		});
	});
</script>

<div class="glass rounded-xl p-4">
	<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
		Sessions by Status
	</p>

	<div class="flex items-center gap-6">
		<!-- SVG donut -->
		<svg viewBox="0 0 36 36" class="h-28 w-28 shrink-0">
			{#if total === 0}
				<circle
					cx="18" cy="18" r="15.9"
					fill="none"
					stroke="var(--color-border)"
					stroke-width="3"
				/>
			{:else}
				{#each segments() as seg}
					<circle
						cx="18" cy="18" r="15.9"
						fill="none"
						stroke={seg.color}
						stroke-width="3"
						stroke-dasharray="{seg.pct} {100 - seg.pct}"
						stroke-dashoffset={-seg.offset}
						stroke-linecap="round"
						transform="rotate(-90 18 18)"
					/>
				{/each}
			{/if}
			<text x="18" y="17" text-anchor="middle" class="fill-[var(--color-text-primary)]" style="font-size: 5px; font-weight: 700;">
				{total}
			</text>
			<text x="18" y="22" text-anchor="middle" class="fill-[var(--color-text-muted)]" style="font-size: 2.5px;">
				sessions
			</text>
		</svg>

		<!-- Legend -->
		<div class="flex flex-col gap-1.5">
			{#each segments() as seg}
				<div class="flex items-center gap-2 text-xs">
					<span class="inline-block h-2.5 w-2.5 rounded-full" style="background: {seg.color}"></span>
					<span class="text-[var(--color-text-secondary)] capitalize">{seg.status}</span>
					<span class="ml-auto font-medium text-[var(--color-text-primary)]">{seg.count}</span>
				</div>
			{/each}
			{#if total === 0}
				<span class="text-xs text-[var(--color-text-muted)]">No sessions yet</span>
			{/if}
		</div>
	</div>
</div>
