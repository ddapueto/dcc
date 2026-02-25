<script lang="ts">
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { Zap, Bot } from '@lucide/svelte';
	import type { SkillInfo, AgentInfo } from '$types/index';

	let {
		onSelectSkill,
		onSelectAgent
	}: {
		onSelectSkill?: (skill: SkillInfo) => void;
		onSelectAgent?: (agent: AgentInfo) => void;
	} = $props();

	let tab = $state<'skills' | 'agents'>('skills');

	const skills = $derived(workspacesStore.detail?.skills ?? []);
	const agents = $derived(workspacesStore.detail?.agents ?? []);
</script>

<div class="flex flex-col gap-2">
	<!-- Tab switcher -->
	<div class="flex gap-1 rounded-lg bg-[var(--color-bg-input)] p-0.5">
		<button
			class="flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors
			{tab === 'skills'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'skills')}
		>
			<Zap class="mr-1 inline h-3 w-3" />
			Skills ({skills.length})
		</button>
		<button
			class="flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors
			{tab === 'agents'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'agents')}
		>
			<Bot class="mr-1 inline h-3 w-3" />
			Agents ({agents.length})
		</button>
	</div>

	<!-- Items -->
	<div class="flex flex-col gap-1">
		{#if tab === 'skills'}
			{#each skills as skill}
				<button
					class="glass rounded-lg px-3 py-2 text-left transition-colors hover:border-[var(--color-glass-border-hover)]"
					onclick={() => onSelectSkill?.(skill)}
				>
					<div class="flex items-center gap-2">
						<Zap class="h-3.5 w-3.5 shrink-0 text-[var(--color-accent)]" />
						<span class="text-sm font-medium text-[var(--color-text-primary)]">
							/{skill.name}
						</span>
					</div>
					{#if skill.description}
						<p class="mt-0.5 pl-5.5 text-xs text-[var(--color-text-muted)] line-clamp-2">
							{skill.description}
						</p>
					{/if}
				</button>
			{/each}
			{#if skills.length === 0}
				<p class="py-4 text-center text-xs text-[var(--color-text-muted)]">
					No skills found
				</p>
			{/if}
		{:else}
			{#each agents as agent}
				<button
					class="glass rounded-lg px-3 py-2 text-left transition-colors hover:border-[var(--color-glass-border-hover)]"
					onclick={() => onSelectAgent?.(agent)}
				>
					<div class="flex items-center gap-2">
						<Bot class="h-3.5 w-3.5 shrink-0 text-[var(--color-accent)]" />
						<span class="text-sm font-medium text-[var(--color-text-primary)]">
							{agent.name}
						</span>
						{#if agent.model}
							<span class="rounded bg-[var(--color-bg-input)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]">
								{agent.model}
							</span>
						{/if}
					</div>
					{#if agent.description}
						<p class="mt-0.5 pl-5.5 text-xs text-[var(--color-text-muted)] line-clamp-2">
							{agent.description}
						</p>
					{/if}
				</button>
			{/each}
			{#if agents.length === 0}
				<p class="py-4 text-center text-xs text-[var(--color-text-muted)]">
					No agents found
				</p>
			{/if}
		{/if}
	</div>
</div>
