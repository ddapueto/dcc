<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Shell from '$lib/components/Shell.svelte';
	import WorkflowLauncher from '$lib/components/WorkflowLauncher.svelte';
	import WorkflowEditor from '$lib/components/WorkflowEditor.svelte';
	import { workflowStore } from '$stores/workflows.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { tabsStore } from '$stores/tabs.svelte';
	import { toastStore } from '$stores/toasts.svelte';
	import { Workflow, Edit3 } from '@lucide/svelte';

	let editing = $state(false);

	onMount(() => {
		workspacesStore.fetch();
		const id = page.params.id;
		if (id) {
			workflowStore.loadWorkflow(id);
		}
	});

	async function handleLaunch(params: Record<string, string>, model?: string) {
		if (!workflowStore.current) return;

		const wsId = workflowStore.current.workspace_id || workspacesStore.currentWorkspaceId;
		if (!wsId) {
			toastStore.add('No workspace selected', 'error');
			return;
		}

		try {
			const sessionId = await workflowStore.launch(
				workflowStore.current.id,
				wsId,
				params,
				model
			);
			tabsStore.addTab(workflowStore.current.name);
			goto('/run');
		} catch (e) {
			toastStore.add('Failed to launch workflow', 'error');
		}
	}

	async function handleSave(data: Record<string, unknown>) {
		if (!workflowStore.current) return;
		try {
			await workflowStore.update(workflowStore.current.id, data);
			editing = false;
			toastStore.add('Workflow updated', 'success');
		} catch (e) {
			toastStore.add('Failed to update workflow', 'error');
		}
	}
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex flex-1 items-center gap-3">
			<a
				href="/workflows"
				class="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
			>
				<Workflow class="h-4 w-4" />
			</a>
			<span class="text-[var(--color-text-muted)]">/</span>
			{#if workflowStore.current}
				<span class="text-sm font-medium text-[var(--color-text-primary)]">
					{workflowStore.current.name}
				</span>
				<span
					class="rounded-full bg-[var(--color-bg-card)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)]"
				>
					{workflowStore.current.category}
				</span>
				{#if !workflowStore.current.is_builtin}
					<button
						class="ml-auto flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]"
						onclick={() => (editing = !editing)}
					>
						<Edit3 class="h-3 w-3" />
						{editing ? 'Cancel Edit' : 'Edit'}
					</button>
				{/if}
			{:else}
				<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
			{/if}
		</div>
	{/snippet}

	{#snippet content()}
		{#if workflowStore.loading && !workflowStore.current}
			<div class="flex h-full items-center justify-center">
				<span class="text-sm text-[var(--color-text-muted)]">Loading workflow...</span>
			</div>
		{:else if workflowStore.current}
			<div class="mx-auto max-w-2xl p-6">
				{#if editing}
					<WorkflowEditor workflow={workflowStore.current} onSave={handleSave} />
				{:else}
					<!-- Workflow info -->
					{#if workflowStore.current.description}
						<p class="mb-4 text-sm text-[var(--color-text-muted)]">
							{workflowStore.current.description}
						</p>
					{/if}

					<div class="mb-4 flex flex-wrap gap-2 text-[10px]">
						{#if workflowStore.current.is_builtin}
							<span
								class="rounded bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[var(--color-text-muted)]"
							>
								built-in
							</span>
						{/if}
						{#if workflowStore.current.usage_count > 0}
							<span
								class="rounded bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[var(--color-text-muted)]"
							>
								{workflowStore.current.usage_count} uses
							</span>
						{/if}
						{#if workflowStore.current.model}
							<span class="rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400">
								{workflowStore.current.model}
							</span>
						{/if}
					</div>

					<!-- Launcher form -->
					<div class="glass rounded-xl border border-[var(--color-border)] p-4">
						<h3
							class="mb-3 text-sm font-medium text-[var(--color-text-primary)]"
						>
							Launch Workflow
						</h3>
						<WorkflowLauncher
							workflow={workflowStore.current}
							workspaceId={workspacesStore.currentWorkspaceId ?? ''}
							onLaunch={handleLaunch}
						/>
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex h-full items-center justify-center">
				<span class="text-sm text-[var(--color-text-muted)]">Workflow not found</span>
			</div>
		{/if}
	{/snippet}

	{#snippet bottombar()}
		{#if workflowStore.current}
			<span class="text-[var(--color-text-muted)]">
				{workflowStore.current.parameters.length} parameter{workflowStore.current.parameters
					.length !== 1
					? 's'
					: ''}
			</span>
		{/if}
	{/snippet}
</Shell>
