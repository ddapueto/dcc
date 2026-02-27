<script lang="ts">
	import type { MonitorTask } from '$types/index';

	let {
		task,
		x,
		y,
		w,
		h,
		selected = false,
		onclick
	}: {
		task: MonitorTask;
		x: number;
		y: number;
		w: number;
		h: number;
		selected?: boolean;
		onclick?: (task: MonitorTask) => void;
	} = $props();

	const statusDot: Record<string, string> = {
		running: '#00d4aa',
		completed: '#22c55e',
		failed: '#ef4444'
	};

	const statusBg: Record<string, string> = {
		running: 'rgba(0,212,170,0.1)',
		completed: 'rgba(34,197,94,0.1)',
		failed: 'rgba(239,68,68,0.1)'
	};

	const toolIcons: Record<string, string> = {
		Task: 'T',
		Read: 'R',
		Write: 'W',
		Edit: 'E',
		Bash: '$',
		Glob: 'G',
		Grep: '?',
		WebFetch: 'F',
		WebSearch: 'S'
	};

	function formatDuration(ms: number | null): string {
		if (ms === null) return '';
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<g class="cursor-pointer" onclick={() => onclick?.(task)}>
	<rect
		{x}
		{y}
		width={w}
		height={h}
		rx="8"
		fill={statusBg[task.status] ?? statusBg.running}
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
					style="background: {statusDot[task.status] ?? statusDot.running}"
					class:animate-pulse={task.status === 'running'}
				></span>
				<span
					class="inline-block shrink-0 rounded bg-[var(--color-bg-card)] px-1 py-0.5 text-[9px] font-mono text-[var(--color-text-muted)]"
				>
					{toolIcons[task.tool_name] ?? task.tool_name.charAt(0)}
				</span>
				<span class="truncate text-[11px] font-medium text-[var(--color-text-primary)]">
					{task.tool_name}
				</span>
				{#if task.subagent_type}
					<span
						class="shrink-0 rounded bg-purple-500/20 px-1 py-0.5 text-[8px] font-medium text-purple-400"
					>
						@{task.subagent_type}
					</span>
				{/if}
				{#if task.subagent_model}
					<span
						class="shrink-0 rounded bg-[var(--color-bg-card)] px-1 py-0.5 text-[8px] text-[var(--color-text-muted)]"
					>
						{task.subagent_model}
					</span>
				{/if}
			</div>
			{#if task.description}
				<p class="mt-1 truncate text-[9px] text-[var(--color-text-muted)]">
					{task.description}
				</p>
			{/if}
			{#if task.duration_ms !== null}
				<span class="mt-0.5 text-[8px] text-[var(--color-text-muted)]">
					{formatDuration(task.duration_ms)}
				</span>
			{/if}
		</div>
	</foreignObject>
</g>
