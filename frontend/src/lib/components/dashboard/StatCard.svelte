<script lang="ts">
	import type { Component } from 'svelte';

	let {
		label,
		value,
		sublabel = '',
		icon: Icon
	}: {
		label: string;
		value: string;
		sublabel?: string;
		icon: Component;
	} = $props();
</script>

<div class="glass rounded-xl p-4">
	<div class="flex items-start justify-between">
		<div>
			<p class="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">{label}</p>
			<p class="mt-1 text-2xl font-bold text-[var(--color-text-primary)]">{value}</p>
			{#if sublabel}
				<p class="mt-0.5 text-xs text-[var(--color-text-secondary)]">{sublabel}</p>
			{/if}
		</div>
		<div class="rounded-lg bg-[var(--color-accent)]/10 p-2">
			<Icon class="h-5 w-5 text-[var(--color-accent)]" />
		</div>
	</div>
</div>
