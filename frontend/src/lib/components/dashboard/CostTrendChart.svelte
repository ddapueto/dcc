<script lang="ts">
	import type { CostTrendPoint } from '$types/index';

	let { data = [] }: { data: CostTrendPoint[] } = $props();

	const WIDTH = 600;
	const HEIGHT = 200;
	const PAD = { top: 10, right: 10, bottom: 25, left: 50 };
	const plotW = WIDTH - PAD.left - PAD.right;
	const plotH = HEIGHT - PAD.top - PAD.bottom;

	const maxCost = $derived(Math.max(...data.map((d) => d.cost), 0.001));

	const points = $derived(
		data.map((d, i) => ({
			x: PAD.left + (data.length > 1 ? (i / (data.length - 1)) * plotW : plotW / 2),
			y: PAD.top + plotH - (d.cost / maxCost) * plotH,
			date: d.date,
			cost: d.cost,
			sessions: d.sessions
		}))
	);

	const linePath = $derived(
		points.length > 0
			? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
			: ''
	);

	const areaPath = $derived(
		points.length > 0
			? linePath +
				` L ${points[points.length - 1].x} ${PAD.top + plotH} L ${points[0].x} ${PAD.top + plotH} Z`
			: ''
	);

	// Y-axis labels
	const yLabels = $derived(
		[0, 0.25, 0.5, 0.75, 1].map((pct) => ({
			value: (maxCost * pct).toFixed(4),
			y: PAD.top + plotH - pct * plotH
		}))
	);
</script>

<div class="glass rounded-xl p-4">
	<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
		Cost Trend (30d)
	</p>

	{#if data.length === 0}
		<p class="py-8 text-center text-xs text-[var(--color-text-muted)]">No data yet</p>
	{:else}
		<svg viewBox="0 0 {WIDTH} {HEIGHT}" class="w-full" preserveAspectRatio="xMidYMid meet">
			<defs>
				<linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="var(--color-accent)" stop-opacity="0.3" />
					<stop offset="100%" stop-color="var(--color-accent)" stop-opacity="0.02" />
				</linearGradient>
			</defs>

			<!-- Grid lines -->
			{#each yLabels as label}
				<line
					x1={PAD.left} y1={label.y}
					x2={PAD.left + plotW} y2={label.y}
					stroke="var(--color-border)" stroke-width="0.5"
				/>
				<text
					x={PAD.left - 5} y={label.y + 3}
					text-anchor="end"
					fill="var(--color-text-muted)"
					style="font-size: 8px;"
				>${label.value}</text>
			{/each}

			<!-- Area -->
			<path d={areaPath} fill="url(#area-grad)" />

			<!-- Line -->
			<path d={linePath} fill="none" stroke="var(--color-accent)" stroke-width="2" stroke-linejoin="round" />

			<!-- Dots -->
			{#each points as p}
				<circle cx={p.x} cy={p.y} r="3" fill="var(--color-accent)" opacity="0.8">
					<title>{p.date}: ${p.cost.toFixed(4)} ({p.sessions} sessions)</title>
				</circle>
			{/each}

			<!-- X-axis labels (show first, middle, last) -->
			{#if points.length >= 1}
				<text x={points[0].x} y={HEIGHT - 5} text-anchor="start" fill="var(--color-text-muted)" style="font-size: 8px;">
					{data[0].date.slice(5)}
				</text>
			{/if}
			{#if points.length >= 3}
				{@const mid = Math.floor(points.length / 2)}
				<text x={points[mid].x} y={HEIGHT - 5} text-anchor="middle" fill="var(--color-text-muted)" style="font-size: 8px;">
					{data[mid].date.slice(5)}
				</text>
			{/if}
			{#if points.length >= 2}
				<text x={points[points.length - 1].x} y={HEIGHT - 5} text-anchor="end" fill="var(--color-text-muted)" style="font-size: 8px;">
					{data[data.length - 1].date.slice(5)}
				</text>
			{/if}
		</svg>
	{/if}
</div>
