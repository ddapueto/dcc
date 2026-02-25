<script lang="ts">
	import { onMount } from 'svelte';
	import Shell from '$lib/components/Shell.svelte';
	import HistoryFilters from '$lib/components/HistoryFilters.svelte';
	import HistoryTable from '$lib/components/HistoryTable.svelte';
	import SessionReplay from '$lib/components/SessionReplay.svelte';
	import { historyStore } from '$stores/history.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import type { SessionHistoryItem } from '$types/index';

	let selectedSession = $state<SessionHistoryItem | null>(null);

	onMount(() => {
		workspacesStore.fetch();
		historyStore.fetch();
	});

	function handleSelect(session: SessionHistoryItem) {
		selectedSession = session;
	}
</script>

<Shell>
	{#snippet topbar()}
		<span class="text-sm font-medium text-[var(--color-text-primary)]">Session History</span>
		<span class="text-xs text-[var(--color-text-muted)]">
			{historyStore.total} sessions
		</span>
	{/snippet}

	{#snippet content()}
		<div class="flex h-full flex-col gap-4 p-4">
			<HistoryFilters />
			{#if historyStore.loading}
				<div class="flex flex-1 items-center justify-center">
					<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
				</div>
			{:else}
				<HistoryTable onSelect={handleSelect} />
			{/if}
		</div>

		{#if selectedSession}
			<SessionReplay
				sessionId={selectedSession.id}
				onClose={() => (selectedSession = null)}
			/>
		{/if}
	{/snippet}

	{#snippet bottombar()}
		<span class="text-[var(--color-text-muted)]">
			Page {historyStore.page + 1} of {historyStore.totalPages}
		</span>
	{/snippet}
</Shell>
