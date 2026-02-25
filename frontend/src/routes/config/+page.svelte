<script lang="ts">
	import { onMount } from 'svelte';
	import Shell from '$lib/components/Shell.svelte';
	import WorkspacePicker from '$lib/components/WorkspacePicker.svelte';
	import ConfigViewer from '$lib/components/ConfigViewer.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';

	onMount(() => {
		workspacesStore.fetch();
	});
</script>

<Shell>
	{#snippet topbar()}
		<WorkspacePicker />
		<span class="text-sm font-medium text-[var(--color-text-primary)]">Config Viewer</span>
	{/snippet}

	{#snippet content()}
		<div class="h-full p-4">
			{#if workspacesStore.currentWorkspaceId}
				<ConfigViewer workspaceId={workspacesStore.currentWorkspaceId} />
			{:else}
				<div class="flex h-full items-center justify-center">
					<p class="text-sm text-[var(--color-text-muted)]">
						Seleccioná un workspace para ver su configuración
					</p>
				</div>
			{/if}
		</div>
	{/snippet}
</Shell>
