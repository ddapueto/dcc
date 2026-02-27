<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Shell from '$lib/components/Shell.svelte';
	import WorkflowCard from '$lib/components/WorkflowCard.svelte';
	import WorkflowLauncher from '$lib/components/WorkflowLauncher.svelte';
	import CategoryFilter from '$lib/components/CategoryFilter.svelte';
	import { workflowStore } from '$stores/workflows.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { tabsStore } from '$stores/tabs.svelte';
	import { toastStore } from '$stores/toasts.svelte';
	import { Plus, Workflow, X } from '@lucide/svelte';
	import type { Workflow as WorkflowType } from '$types/index';

	let filterWorkspaceId = $state<string>('');
	let selectedCategory = $state<string | null>(null);
	let launcherWorkflow = $state<WorkflowType | null>(null);
	let initialLoadDone = $state(false);

	const categories = [
		{ id: 'development', label: 'Development' },
		{ id: 'testing', label: 'Testing' },
		{ id: 'review', label: 'Review' },
		{ id: 'devops', label: 'DevOps' },
		{ id: 'custom', label: 'Custom' }
	];

	onMount(() => {
		workspacesStore.fetch();
	});

	// Auto-seleccionar workspace actual y cargar workflows filtrados
	$effect(() => {
		if (initialLoadDone) return;
		const wsId = workspacesStore.currentWorkspaceId;
		const workspaces = workspacesStore.workspaces;
		if (workspaces.length === 0) return;

		// Usar workspace actual o el primero disponible
		const targetId = wsId || workspaces[0].id;
		filterWorkspaceId = targetId;
		workflowStore.loadWorkflows(targetId);
		initialLoadDone = true;
	});

	function handleFilter() {
		workflowStore.loadWorkflows(
			filterWorkspaceId || undefined,
			selectedCategory || undefined
		);
	}

	function handleCategorySelect(id: string | null) {
		selectedCategory = id;
		handleFilter();
	}

	function handleClick(wf: WorkflowType) {
		launcherWorkflow = wf;
	}

	async function handleDelete(wf: WorkflowType) {
		try {
			await workflowStore.remove(wf.id);
			toastStore.add(`Workflow "${wf.name}" deleted`, 'success');
		} catch (e) {
			toastStore.add('Failed to delete workflow', 'error');
		}
	}

	async function handleLaunch(params: Record<string, string>, model?: string) {
		if (!launcherWorkflow) return;

		// Usar workspace del workflow o el actual
		const wsId = launcherWorkflow.workspace_id || workspacesStore.currentWorkspaceId;
		if (!wsId) {
			toastStore.add('No workspace selected', 'error');
			return;
		}

		const wfName = launcherWorkflow.name;
		try {
			const sessionId = await workflowStore.launch(
				launcherWorkflow.id,
				wsId,
				params,
				model
			);
			launcherWorkflow = null;
			tabsStore.addTab(wfName);
			goto('/run');
		} catch (e) {
			toastStore.add('Failed to launch workflow', 'error');
		}
	}
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex flex-1 items-center gap-3">
			<Workflow class="h-4 w-4 text-[var(--color-accent)]" />
			<span class="text-sm font-medium text-[var(--color-text-primary)]">Workflows</span>
			<span class="text-xs text-[var(--color-text-muted)]">
				{workflowStore.workflows.length} workflows
			</span>

			<div class="ml-auto flex items-center gap-2">
				<select
					class="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
					bind:value={filterWorkspaceId}
					onchange={handleFilter}
				>
					<option value="">All workspaces</option>
					{#each workspacesStore.workspaces as ws}
						<option value={ws.id}>{ws.name}</option>
					{/each}
				</select>

				<a
					href="/workflows/new"
					class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black transition-opacity hover:opacity-90"
				>
					<Plus class="h-3.5 w-3.5" />
					Create Custom
				</a>
			</div>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="p-4">
			<!-- Category filter -->
			<div class="mb-4">
				<CategoryFilter
					{categories}
					selected={selectedCategory}
					onSelect={handleCategorySelect}
				/>
			</div>

			{#if workflowStore.loading}
				<div class="flex flex-1 items-center justify-center py-20">
					<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
				</div>
			{:else if workflowStore.workflows.length === 0}
				<div class="flex flex-col items-center justify-center gap-3 py-20">
					<Workflow class="h-10 w-10 text-[var(--color-text-muted)]" />
					<p class="text-sm text-[var(--color-text-muted)]">No workflows found</p>
					<p class="text-xs text-[var(--color-text-muted)]">
						Workflows are prompt templates that launch Claude Code sessions.
					</p>
					<a
						href="/workflows/new"
						class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black"
					>
						<Plus class="h-3.5 w-3.5" />
						Create your first workflow
					</a>
				</div>
			{:else}
				<div class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
					{#each workflowStore.workflows as wf (wf.id)}
						<WorkflowCard
							workflow={wf}
							onClick={handleClick}
							onDelete={handleDelete}
						/>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Launcher modal -->
		{#if launcherWorkflow}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
				onclick={() => (launcherWorkflow = null)}
			>
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="glass mx-4 w-full max-w-lg rounded-xl border border-[var(--color-border)] p-6"
					onclick={(e: MouseEvent) => e.stopPropagation()}
				>
					<div class="mb-4 flex items-center justify-between">
						<h2 class="text-lg font-medium text-[var(--color-text-primary)]">
							{launcherWorkflow.name}
						</h2>
						<button
							class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)]"
							onclick={() => (launcherWorkflow = null)}
						>
							<X class="h-4 w-4" />
						</button>
					</div>
					{#if launcherWorkflow.description}
						<p class="mb-4 text-xs text-[var(--color-text-muted)]">
							{launcherWorkflow.description}
						</p>
					{/if}
					<WorkflowLauncher
						workflow={launcherWorkflow}
						workspaceId={workspacesStore.currentWorkspaceId ?? ''}
						onLaunch={handleLaunch}
					/>
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet bottombar()}
		<span class="text-[var(--color-text-muted)]">
			{workflowStore.workflows.length} workflow{workflowStore.workflows.length !== 1 ? 's' : ''}
		</span>
	{/snippet}
</Shell>
