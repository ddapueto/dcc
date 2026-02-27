<script lang="ts">
	import { onMount } from 'svelte';
	import { Bot, Users, DollarSign, Activity, RefreshCw } from '@lucide/svelte';
	import Shell from '$lib/components/Shell.svelte';
	import StatCard from '$lib/components/dashboard/StatCard.svelte';
	import AgentCard from '$lib/components/AgentCard.svelte';
	import AgentStatsTable from '$lib/components/AgentStatsTable.svelte';
	import DelegationGraph from '$lib/components/DelegationGraph.svelte';
	import AgentDetail from '$lib/components/AgentDetail.svelte';
	import { agentsStore } from '$stores/agents.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import type { RegisteredAgent } from '$types/index';

	onMount(async () => {
		if (!workspacesStore.workspaces.length) {
			await workspacesStore.fetch();
		}
		await loadData();
	});

	async function loadData() {
		const wsId = workspacesStore.currentWorkspaceId;
		if (wsId) {
			await agentsStore.loadForWorkspace(wsId);
		}
		await agentsStore.loadStats(wsId ?? undefined);
	}

	function handleWorkspaceChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		workspacesStore.currentWorkspaceId = target.value || null;
		agentsStore.reset();
		loadData();
	}

	function handleSelectAgent(agent: RegisteredAgent) {
		agentsStore.selectAgent(agent.name);
	}

	function handleSelectAgentName(name: string) {
		agentsStore.selectAgent(name);
	}

	function formatCost(n: number): string {
		return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
	}
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex items-center gap-2">
			<Bot class="h-4 w-4 text-[var(--color-accent)]" />
			<span class="text-sm font-semibold text-[var(--color-text-primary)]">Agents</span>
			{#if agentsStore.activeAgents.length > 0}
				<span
					class="rounded-full bg-[var(--color-accent)]/10 px-2 py-0.5 text-[10px] text-[var(--color-accent)]"
				>
					{agentsStore.activeAgents.length}
				</span>
			{/if}
		</div>
		<div class="ml-auto flex items-center gap-2">
			<select
				class="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-input)] px-3 py-1.5 text-xs text-[var(--color-text-secondary)]"
				value={workspacesStore.currentWorkspaceId ?? ''}
				onchange={handleWorkspaceChange}
			>
				<option value="">All Workspaces</option>
				{#each workspacesStore.workspaces as ws}
					<option value={ws.id}>{ws.name}</option>
				{/each}
			</select>
			<button
				onclick={loadData}
				disabled={agentsStore.loading}
				class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)] disabled:opacity-50"
			>
				<RefreshCw class="h-3.5 w-3.5 {agentsStore.loading ? 'animate-spin' : ''}" />
				Refresh
			</button>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="p-6">
			{#if agentsStore.error}
				<div
					class="mb-4 rounded-lg bg-[var(--color-error)]/10 px-4 py-3 text-sm text-[var(--color-error)]"
				>
					{agentsStore.error}
				</div>
			{/if}

			<!-- Row 1: Stat cards -->
			<div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<StatCard
					label="Total Agents"
					value={String(agentsStore.activeAgents.length)}
					sublabel="{agentsStore.agents.length} registered"
					icon={Bot}
				/>
				<StatCard
					label="Active Models"
					value={String(agentsStore.uniqueModels.length)}
					sublabel={agentsStore.uniqueModels.join(', ') || 'none'}
					icon={Users}
				/>
				<StatCard
					label="Agent Sessions"
					value={String(agentsStore.totalAgentSessions)}
					sublabel="across all agents"
					icon={Activity}
				/>
				<StatCard
					label="Agent Cost"
					value={formatCost(agentsStore.totalAgentCost)}
					sublabel="total spend"
					icon={DollarSign}
				/>
			</div>

			<!-- Row 2: Agent cards grid -->
			{#if agentsStore.activeAgents.length > 0}
				<div class="mb-6">
					<h2 class="mb-3 text-xs font-semibold text-[var(--color-text-muted)]">
						Agent Registry
					</h2>
					<div class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
						{#each agentsStore.activeAgents as agent (agent.id)}
							<AgentCard
								{agent}
								stats={agentsStore.stats.find((s) => s.name === agent.name)}
								selected={agentsStore.selectedAgentName === agent.name}
								onclick={handleSelectAgent}
							/>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Row 3: Stats table + Delegation graph + Detail panel -->
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
				{#if agentsStore.selectedAgent}
					<div class="lg:col-span-2 mb-4">
						<AgentDetail
							agent={agentsStore.selectedAgent}
							stats={agentsStore.selectedAgentStats}
							trend={agentsStore.selectedAgentTrend}
							onClose={() => (agentsStore.selectedAgentName = null)}
						/>
					</div>
				{/if}
				<AgentStatsTable
					stats={agentsStore.stats}
					onSelectAgent={handleSelectAgentName}
				/>
				<DelegationGraph delegations={agentsStore.delegations} />
			</div>
		</div>
	{/snippet}
</Shell>
