<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Shell from '$lib/components/Shell.svelte';
	import WorkflowEditor from '$lib/components/WorkflowEditor.svelte';
	import { workflowStore } from '$stores/workflows.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { Workflow } from '@lucide/svelte';
	import type { WorkflowParam } from '$types/index';

	let selectedWorkspaceId = $state('');

	onMount(() => {
		workspacesStore.fetch();
	});

	async function handleSave(data: {
		name: string;
		description: string;
		category: string;
		prompt_template: string;
		parameters: WorkflowParam[];
		model: string;
	}) {
		if (!selectedWorkspaceId) return;

		try {
			const id = await workflowStore.create({
				workspace_id: selectedWorkspaceId,
				name: data.name,
				prompt_template: data.prompt_template,
				description: data.description || undefined,
				category: data.category,
				parameters: data.parameters as unknown as Array<Record<string, unknown>>,
				model: data.model || undefined
			});
			goto(`/workflows/${id}`);
		} catch (e) {
			console.error('Failed to create workflow:', e);
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
			<span class="text-sm font-medium text-[var(--color-text-primary)]">New Workflow</span>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="mx-auto max-w-2xl p-6">
			<h2 class="mb-4 text-lg font-semibold text-[var(--color-text-primary)]">
				Create Custom Workflow
			</h2>

			<!-- Workspace selector -->
			<div class="mb-4">
				<label
					for="ws-select"
					class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
				>
					Workspace <span class="text-red-400">*</span>
				</label>
				<select
					id="ws-select"
					class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
					bind:value={selectedWorkspaceId}
				>
					<option value="">Select workspace...</option>
					{#each workspacesStore.workspaces as ws}
						<option value={ws.id}>{ws.name}</option>
					{/each}
				</select>
			</div>

			{#if selectedWorkspaceId}
				<WorkflowEditor onSave={handleSave} />
			{:else}
				<p class="py-10 text-center text-sm text-[var(--color-text-muted)]">
					Select a workspace to start creating a workflow
				</p>
			{/if}
		</div>
	{/snippet}

	{#snippet bottombar()}
		<span class="text-[var(--color-text-muted)]">Custom workflow editor</span>
	{/snippet}
</Shell>
