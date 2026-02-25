<script lang="ts">
	import { Search } from '@lucide/svelte';
	import { historyStore } from '$stores/history.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';

	const statuses = ['running', 'completed', 'error', 'cancelled'] as const;

	let searchInput = $state('');
	let debounceTimer: ReturnType<typeof setTimeout>;

	function handleSearch(value: string) {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			historyStore.setFilters({ search: value });
		}, 300);
	}
</script>

<div class="flex flex-wrap items-center gap-3">
	<!-- Search -->
	<div class="relative flex-1">
		<Search class="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--color-text-muted)]" />
		<input
			type="text"
			placeholder="Buscar en prompts..."
			bind:value={searchInput}
			oninput={() => handleSearch(searchInput)}
			class="w-full rounded-lg bg-[var(--color-bg-input)] py-2 pl-9 pr-3 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
		/>
	</div>

	<!-- Workspace filter -->
	<select
		value={historyStore.workspaceId ?? ''}
		onchange={(e) => historyStore.setFilters({ workspaceId: e.currentTarget.value || null })}
		class="rounded-lg bg-[var(--color-bg-input)] px-3 py-2 text-xs text-[var(--color-text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
	>
		<option value="">Todos los workspaces</option>
		{#each workspacesStore.workspacesByTenant as group}
			<optgroup label={group.tenant.name}>
				{#each group.workspaces as ws}
					<option value={ws.id}>{ws.name}</option>
				{/each}
			</optgroup>
		{/each}
	</select>

	<!-- Status chips -->
	<div class="flex gap-1">
		<button
			class="rounded-full px-2.5 py-1 text-[10px] font-medium transition-colors
			{historyStore.statusFilter === null
				? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
				: 'bg-[var(--color-bg-input)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => historyStore.setFilters({ statusFilter: null })}
		>
			All
		</button>
		{#each statuses as s}
			<button
				class="rounded-full px-2.5 py-1 text-[10px] font-medium transition-colors
				{historyStore.statusFilter === s
					? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
					: 'bg-[var(--color-bg-input)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
				onclick={() => historyStore.setFilters({ statusFilter: s })}
			>
				{s}
			</button>
		{/each}
	</div>
</div>
