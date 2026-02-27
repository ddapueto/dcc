<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import Shell from '$lib/components/Shell.svelte';
	import WorkspacePicker from '$lib/components/WorkspacePicker.svelte';
	import SkillPicker from '$lib/components/SkillPicker.svelte';
	import GitHubPanel from '$lib/components/GitHubPanel.svelte';
	import PromptInput from '$lib/components/PromptInput.svelte';
	import StreamOutput from '$lib/components/StreamOutput.svelte';
	import ToolCallCard from '$lib/components/ToolCallCard.svelte';
	import CostBadge from '$lib/components/CostBadge.svelte';
	import TabBar from '$lib/components/TabBar.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { tabsStore } from '$stores/tabs.svelte';
	import { githubStore } from '$stores/github.svelte';
	import MonitorPanel from '$lib/components/MonitorPanel.svelte';
	import { monitorStore } from '$stores/monitor.svelte';
	import { initGlobalShortcuts } from '$lib/actions/shortcuts';
	import type { SkillInfo, AgentInfo, GitHubIssue } from '$types/index';

	let monitorMode = $state(false);

	let selectedSkill = $state<string | null>(null);
	let selectedAgent = $state<string | null>(null);
	let promptPrefill = $state<string | null>(null);
	let cleanupShortcuts: (() => void) | undefined;

	onMount(() => {
		workspacesStore.fetch();
		tabsStore.ensureTab();
		cleanupShortcuts = initGlobalShortcuts();
	});

	onDestroy(() => {
		cleanupShortcuts?.();
	});

	function handleSelectSkill(skill: SkillInfo) {
		selectedSkill = skill.name;
		selectedAgent = null;
	}

	function handleSelectAgent(agent: AgentInfo) {
		selectedAgent = agent.name;
		selectedSkill = null;
	}

	function handleSubmit(prompt: string, model?: string) {
		if (!workspacesStore.currentWorkspaceId) return;
		const session = tabsStore.activeSession;
		if (!session) return;

		// Actualizar label de la tab con el prompt
		const tab = tabsStore.activeTab;
		if (tab) {
			tab.label = prompt.length > 30 ? prompt.slice(0, 30) + '...' : prompt;
		}

		session.start(
			workspacesStore.currentWorkspaceId,
			prompt,
			selectedSkill ?? undefined,
			selectedAgent ?? undefined,
			model
		);
	}

	function handleCancel() {
		tabsStore.activeSession?.cancel();
	}

	function handleSelectIssue(issue: GitHubIssue) {
		const body = issue.body ? `\n\n${issue.body}` : '';
		promptPrefill = `Issue #${issue.number}: ${issue.title}${body}`;
	}

	function handleUseAsContext(output: string) {
		// Open a new tab with the output as prefill
		tabsStore.addTab('Context');
		promptPrefill = output;
	}

	// Load GitHub data when workspace changes
	$effect(() => {
		const ws = workspacesStore.currentWorkspace;
		if (ws?.repo_owner) {
			githubStore.loadForWorkspace(ws.id);
		} else {
			githubStore.reset();
		}
	});

	const currentSession = $derived(tabsStore.activeSession);
</script>

<Shell>
	{#snippet sidebar()}
		{#if workspacesStore.detail}
			<SkillPicker
				onSelectSkill={handleSelectSkill}
				onSelectAgent={handleSelectAgent}
			/>
			{#if workspacesStore.currentWorkspace?.repo_owner && workspacesStore.currentWorkspaceId}
				<div class="mt-3 border-t border-[var(--color-border)] pt-3">
					<GitHubPanel
						workspaceId={workspacesStore.currentWorkspaceId}
						onSelectIssue={handleSelectIssue}
					/>
				</div>
			{/if}
		{:else if workspacesStore.currentWorkspaceId}
			<div class="flex items-center justify-center py-8">
				<span class="text-xs text-[var(--color-text-muted)]">Loading...</span>
			</div>
		{:else}
			<div class="flex items-center justify-center py-8">
				<span class="text-xs text-[var(--color-text-muted)]">Select a workspace</span>
			</div>
		{/if}
	{/snippet}

	{#snippet topbar()}
		<WorkspacePicker />
		{#if workspacesStore.currentWorkspace}
			<div class="ml-auto flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
				<span>{workspacesStore.currentWorkspace.agents_count} agents</span>
				<span class="text-[var(--color-border)]">|</span>
				<span>{workspacesStore.currentWorkspace.skills_count} skills</span>
			</div>
		{/if}
	{/snippet}

	{#snippet content()}
		<div class="flex h-full flex-col">
			<!-- Tab bar -->
			<TabBar />

			{#if currentSession}
				<div class="flex min-h-0 flex-1">
					<!-- Main content area -->
					<div class="flex min-w-0 flex-1 flex-col">
						<!-- Stream output -->
						<div class="flex-1">
							<StreamOutput session={currentSession} onUseAsContext={handleUseAsContext} />
						</div>

						<!-- Prompt input -->
						<div class="border-t border-[var(--color-border)] p-4">
							<PromptInput
								running={currentSession.status === 'running'}
								disabled={!workspacesStore.currentWorkspaceId}
								{selectedSkill}
								{selectedAgent}
								prefill={promptPrefill}
								onSubmit={handleSubmit}
								onCancel={handleCancel}
							/>
						</div>
					</div>

					<!-- Tool calls / Monitor panel -->
					{#if currentSession.toolCalls.length > 0 || monitorStore.tasks.length > 0}
						<div
							class="flex w-80 shrink-0 flex-col border-l border-[var(--color-border)]"
						>
							<div class="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-2">
								<span class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
									{monitorMode ? 'Monitor' : `Tool Calls (${currentSession.toolCalls.length})`}
								</span>
								<button
									class="rounded px-2 py-0.5 text-[10px] transition-colors {monitorMode
										? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
										: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
									onclick={() => (monitorMode = !monitorMode)}
									title="Toggle monitor view"
								>
									{monitorMode ? 'Tools' : 'Monitor'}
								</button>
							</div>

							{#if monitorMode}
								<MonitorPanel sessionId={currentSession.sessionId} />
							{:else}
								<div class="flex-1 overflow-y-auto p-3">
									<div class="flex flex-col gap-2">
										{#each currentSession.toolCalls as tc (tc.id)}
											<ToolCallCard toolCall={tc} />
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/snippet}

	{#snippet bottombar()}
		{#if currentSession}
			<CostBadge session={currentSession} />
		{/if}
	{/snippet}
</Shell>
