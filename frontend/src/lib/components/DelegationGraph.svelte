<script lang="ts">
	import type { AgentDelegation } from '$types/index';

	let {
		delegations
	}: {
		delegations: AgentDelegation[];
	} = $props();

	// Build unique nodes and edges
	let nodes = $derived(() => {
		const names = new Set<string>();
		for (const d of delegations) {
			if (d.parent_agent) names.add(d.parent_agent);
			names.add(d.subagent_type);
		}
		return [...names];
	});

	let maxCount = $derived(Math.max(1, ...delegations.map((d) => d.count)));

	// Layout: agents on left, subagent_types on right
	let parentAgents = $derived([...new Set(delegations.map((d) => d.parent_agent).filter(Boolean))]);
	let subagentTypes = $derived([...new Set(delegations.map((d) => d.subagent_type))]);

	const nodeW = 120;
	const nodeH = 32;
	const leftX = 20;
	const rightX = 280;
	const startY = 20;
	const gapY = 50;

	function parentY(i: number) {
		return startY + i * gapY;
	}
	function subY(i: number) {
		return startY + i * gapY;
	}

	const svgHeight = $derived(
		Math.max(
			startY + parentAgents.length * gapY,
			startY + subagentTypes.length * gapY,
			100
		) + 20
	);
</script>

<div class="glass rounded-lg border border-[var(--color-border)]">
	<div class="border-b border-[var(--color-border)] px-4 py-2">
		<h3 class="text-xs font-semibold text-[var(--color-text-primary)]">Agent Delegations</h3>
	</div>
	{#if delegations.length === 0}
		<div class="flex items-center justify-center py-8">
			<p class="text-xs text-[var(--color-text-muted)]">No delegation data yet</p>
		</div>
	{:else}
		<div class="overflow-auto p-2">
			<svg width="420" height={svgHeight} viewBox="0 0 420 {svgHeight}">
				<!-- Edges -->
				{#each delegations as d}
					{@const pi = parentAgents.indexOf(d.parent_agent ?? '')}
					{@const si = subagentTypes.indexOf(d.subagent_type)}
					{@const thickness = Math.max(1, Math.min(6, (d.count / maxCount) * 6))}
					{#if pi >= 0 && si >= 0}
						<line
							x1={leftX + nodeW}
							y1={parentY(pi) + nodeH / 2}
							x2={rightX}
							y2={subY(si) + nodeH / 2}
							stroke="rgba(0,212,170,0.3)"
							stroke-width={thickness}
						/>
						<text
							x={(leftX + nodeW + rightX) / 2}
							y={(parentY(pi) + subY(si)) / 2 + nodeH / 2 - 4}
							text-anchor="middle"
							fill="rgba(255,255,255,0.4)"
							font-size="9"
						>
							{d.count}x
						</text>
					{/if}
				{/each}

				<!-- Parent agent nodes (left) -->
				{#each parentAgents as agent, i}
					<rect
						x={leftX}
						y={parentY(i)}
						width={nodeW}
						height={nodeH}
						rx="6"
						fill="rgba(0,212,170,0.1)"
						stroke="rgba(0,212,170,0.3)"
						stroke-width="1"
					/>
					<text
						x={leftX + nodeW / 2}
						y={parentY(i) + nodeH / 2 + 4}
						text-anchor="middle"
						fill="#00d4aa"
						font-size="10"
						font-weight="500"
					>
						@{agent ?? '(prompt)'}
					</text>
				{/each}

				<!-- Subagent type nodes (right) -->
				{#each subagentTypes as subType, i}
					<rect
						x={rightX}
						y={subY(i)}
						width={nodeW}
						height={nodeH}
						rx="6"
						fill="rgba(168,85,247,0.1)"
						stroke="rgba(168,85,247,0.3)"
						stroke-width="1"
					/>
					<text
						x={rightX + nodeW / 2}
						y={subY(i) + nodeH / 2 + 4}
						text-anchor="middle"
						fill="#a855f7"
						font-size="10"
						font-weight="500"
					>
						{subType}
					</text>
				{/each}
			</svg>
		</div>
	{/if}
</div>
