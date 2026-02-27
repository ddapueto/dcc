<script lang="ts">
	let {
		categories,
		selected,
		onSelect
	}: {
		categories: { id: string; label: string }[];
		selected: string | null;
		onSelect: (id: string | null) => void;
	} = $props();
</script>

<div class="flex flex-wrap gap-2">
	<button
		class="rounded-full px-3 py-1 text-xs transition-colors {selected === null
			? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
			: 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-secondary)]'}"
		onclick={() => onSelect(null)}
	>
		All
	</button>
	{#each categories as cat}
		<button
			class="rounded-full px-3 py-1 text-xs transition-colors {selected === cat.id
				? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => onSelect(cat.id)}
		>
			{cat.label}
		</button>
	{/each}
</div>
