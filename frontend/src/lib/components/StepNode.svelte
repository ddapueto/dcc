<script lang="ts">
	import type { PipelineStep } from '$types/index';

	let {
		step,
		x,
		y,
		w,
		h,
		selected = false,
		onclick
	}: {
		step: PipelineStep;
		x: number;
		y: number;
		w: number;
		h: number;
		selected?: boolean;
		onclick?: (step: PipelineStep) => void;
	} = $props();

	const statusDot: Record<string, string> = {
		pending: '#6b7280',
		running: '#00d4aa',
		completed: '#22c55e',
		failed: '#ef4444',
		skipped: '#9ca3af'
	};

	const statusBg: Record<string, string> = {
		pending: 'rgba(107,114,128,0.1)',
		running: 'rgba(0,212,170,0.1)',
		completed: 'rgba(34,197,94,0.1)',
		failed: 'rgba(239,68,68,0.1)',
		skipped: 'rgba(156,163,175,0.1)'
	};
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<g
	class="cursor-pointer"
	onclick={() => onclick?.(step)}
>
	<rect
		{x}
		{y}
		width={w}
		height={h}
		rx="8"
		fill={statusBg[step.status] ?? statusBg.pending}
		stroke={selected ? '#00d4aa' : 'rgba(255,255,255,0.08)'}
		stroke-width={selected ? 2 : 1}
	/>
	<foreignObject {x} {y} width={w} height={h}>
		<div
			xmlns="http://www.w3.org/1999/xhtml"
			class="flex h-full flex-col justify-center px-3 py-2"
		>
			<div class="flex items-center gap-1.5">
				<span
					class="inline-block h-2 w-2 shrink-0 rounded-full"
					style="background: {statusDot[step.status] ?? statusDot.pending}"
					class:animate-pulse={step.status === 'running'}
				></span>
				<span class="truncate text-[11px] font-medium text-[var(--color-text-primary)]">
					{step.name}
				</span>
			</div>
			<div class="mt-1 flex items-center gap-2 text-[9px] text-[var(--color-text-muted)]">
				<span class="rounded bg-[var(--color-bg-card)] px-1 py-0.5">
					#{step.position}
				</span>
				{#if step.agent}
					<span class="truncate rounded bg-[var(--color-accent)]/10 px-1 py-0.5 text-[var(--color-accent)]">
						{step.agent}
					</span>
				{/if}
			</div>
		</div>
	</foreignObject>
</g>
