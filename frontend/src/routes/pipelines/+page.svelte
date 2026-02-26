<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Shell from '$lib/components/Shell.svelte';
	import PipelineListItem from '$lib/components/PipelineListItem.svelte';
	import { pipelineStore } from '$stores/pipelines.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { Plus, Workflow } from '@lucide/svelte';
	import type { Pipeline } from '$types/index';

	let filterWorkspaceId = $state<string>('');

	onMount(() => {
		workspacesStore.fetch();
		pipelineStore.loadPipelines();
	});

	function handleFilter() {
		pipelineStore.loadPipelines(filterWorkspaceId || undefined);
	}

	function handleClick(p: Pipeline) {
		goto(`/pipelines/${p.id}`);
	}

	async function handleDelete(p: Pipeline) {
		await pipelineStore.remove(p.id);
	}
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex flex-1 items-center gap-3">
			<Workflow class="h-4 w-4 text-[var(--color-accent)]" />
			<span class="text-sm font-medium text-[var(--color-text-primary)]">Pipelines</span>
			<span class="text-xs text-[var(--color-text-muted)]">
				{pipelineStore.pipelines.length} pipelines
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
					href="/pipelines/new"
					class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black transition-opacity hover:opacity-90"
				>
					<Plus class="h-3.5 w-3.5" />
					New Pipeline
				</a>
			</div>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="flex flex-col gap-3 p-4">
			{#if pipelineStore.loading}
				<div class="flex flex-1 items-center justify-center py-20">
					<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
				</div>
			{:else if pipelineStore.pipelines.length === 0}
				<div class="flex flex-col items-center justify-center gap-3 py-20">
					<Workflow class="h-10 w-10 text-[var(--color-text-muted)]" />
					<p class="text-sm text-[var(--color-text-muted)]">No pipelines yet</p>
					<a
						href="/pipelines/new"
						class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black"
					>
						<Plus class="h-3.5 w-3.5" />
						Create your first pipeline
					</a>
				</div>
			{:else}
				{#each pipelineStore.pipelines as pipeline (pipeline.id)}
					<PipelineListItem
						{pipeline}
						onClick={handleClick}
						onDelete={handleDelete}
					/>
				{/each}
			{/if}
		</div>
	{/snippet}

	{#snippet bottombar()}
		<span class="text-[var(--color-text-muted)]">
			{pipelineStore.pipelines.length} pipeline{pipelineStore.pipelines.length !== 1 ? 's' : ''}
		</span>
	{/snippet}
</Shell>
