<script lang="ts">
	import { X, CheckCircle, AlertCircle, Info } from '@lucide/svelte';
	import { toastStore } from '$stores/toasts.svelte';

	const icons = {
		success: CheckCircle,
		error: AlertCircle,
		info: Info
	};

	const borderColors = {
		success: 'var(--color-success)',
		error: 'var(--color-error)',
		info: 'var(--color-info)'
	};
</script>

{#if toastStore.toasts.length > 0}
	<div class="fixed right-4 bottom-4 z-50 flex flex-col gap-2">
		{#each toastStore.toasts as toast (toast.id)}
			{@const Icon = icons[toast.type]}
			<div
				class="glass flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg transition-all duration-300 {toast.exiting
					? 'translate-x-full opacity-0'
					: 'translate-x-0 opacity-100'}"
				style="border-left: 3px solid {borderColors[toast.type]}; min-width: 280px; max-width: 400px;"
			>
				<Icon class="h-4 w-4 shrink-0" style="color: {borderColors[toast.type]}" />
				<span class="flex-1 text-xs text-[var(--color-text-primary)]">{toast.message}</span>
				<button
					onclick={() => toastStore.dismiss(toast.id)}
					class="shrink-0 rounded p-0.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
				>
					<X class="h-3 w-3" />
				</button>
			</div>
		{/each}
	</div>
{/if}
