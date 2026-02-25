<script lang="ts">
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { ChevronDown, FolderGit2, RefreshCw } from '@lucide/svelte';

	let dropdownOpen = $state(false);
</script>

<div class="relative">
	<button
		onclick={() => (dropdownOpen = !dropdownOpen)}
		class="glass flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors hover:border-[var(--color-glass-border-hover)]"
	>
		<FolderGit2 class="h-4 w-4 text-[var(--color-accent)]" />
		{#if workspacesStore.currentWorkspace}
			<span class="text-[var(--color-text-primary)]">{workspacesStore.currentWorkspace.name}</span>
			<span class="text-[var(--color-text-muted)]">
				({workspacesStore.currentWorkspace.tenant_name})
			</span>
		{:else}
			<span class="text-[var(--color-text-muted)]">Seleccionar workspace...</span>
		{/if}
		<ChevronDown class="h-3 w-3 text-[var(--color-text-muted)]" />
	</button>

	{#if dropdownOpen}
		<!-- Backdrop -->
		<button class="fixed inset-0 z-10" onclick={() => (dropdownOpen = false)} aria-label="Close"></button>

		<!-- Dropdown -->
		<div
			class="glass absolute left-0 top-full z-20 mt-1 w-72 rounded-lg border border-[var(--color-border)] shadow-xl"
		>
			<div class="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-2">
				<span class="text-xs font-medium text-[var(--color-text-secondary)]">Workspaces</span>
				<button
					onclick={() => workspacesStore.scan()}
					class="rounded p-1 text-[var(--color-text-muted)] hover:text-[var(--color-accent)]"
					title="Re-scan workspaces"
				>
					<RefreshCw class="h-3 w-3" />
				</button>
			</div>

			<div class="max-h-80 overflow-y-auto p-1">
				{#each workspacesStore.workspacesByTenant as group}
					{#if group.workspaces.length > 0}
						<div class="px-2 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
							{group.tenant.name}
						</div>
						{#each group.workspaces as ws}
							<button
								class="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors
								{ws.id === workspacesStore.currentWorkspaceId
									? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
									: 'text-[var(--color-text-primary)] hover:bg-[var(--color-bg-card-hover)]'}"
								onclick={() => {
									workspacesStore.switchWorkspace(ws.id);
									dropdownOpen = false;
								}}
							>
								<FolderGit2 class="h-3.5 w-3.5 shrink-0" />
								<span class="truncate">{ws.name}</span>
								{#if ws.agents_count > 0 || ws.skills_count > 0}
									<span class="ml-auto text-[10px] text-[var(--color-text-muted)]">
										{ws.agents_count}A / {ws.skills_count}S
									</span>
								{/if}
							</button>
						{/each}
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</div>
