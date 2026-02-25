<script lang="ts">
	import { X, Plus } from '@lucide/svelte';
	import { tabsStore } from '$stores/tabs.svelte';
</script>

<div class="flex items-center gap-0.5 border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-2">
	{#each tabsStore.tabs as tab (tab.id)}
		<div
			class="group flex items-center gap-1.5 border-b-2 px-3 py-1.5 text-xs transition-colors
			{tabsStore.activeTabId === tab.id
				? 'border-[var(--color-accent)] text-[var(--color-text-primary)]'
				: 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
		>
			<button
				class="flex items-center gap-1.5"
				onclick={() => tabsStore.switchTab(tab.id)}
			>
				<!-- Status dot -->
				{#if tab.session.status === 'running'}
					<span class="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-accent)]"></span>
				{:else if tab.session.status === 'completed'}
					<span class="h-1.5 w-1.5 rounded-full bg-[var(--color-success)]"></span>
				{:else if tab.session.status === 'error'}
					<span class="h-1.5 w-1.5 rounded-full bg-[var(--color-error)]"></span>
				{:else}
					<span class="h-1.5 w-1.5 rounded-full bg-[var(--color-text-muted)]/40"></span>
				{/if}
				<span class="max-w-[120px] truncate">{tab.label}</span>
			</button>
			<button
				onclick={(e) => { e.stopPropagation(); tabsStore.closeTab(tab.id); }}
				class="rounded p-0.5 opacity-0 transition-opacity hover:bg-[var(--color-bg-card)] group-hover:opacity-100"
			>
				<X class="h-3 w-3" />
			</button>
		</div>
	{/each}

	<!-- New tab -->
	<button
		onclick={() => tabsStore.addTab()}
		class="ml-1 rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-secondary)]"
	>
		<Plus class="h-3.5 w-3.5" />
	</button>
</div>
