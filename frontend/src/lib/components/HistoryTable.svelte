<script lang="ts">
	import { Clock, Coins, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { historyStore } from '$stores/history.svelte';
	import type { SessionHistoryItem } from '$types/index';

	let { onSelect }: { onSelect?: (session: SessionHistoryItem) => void } = $props();

	function formatTime(iso: string): string {
		const d = new Date(iso + 'Z');
		const now = new Date();
		const diffMs = now.getTime() - d.getTime();
		const diffMin = Math.floor(diffMs / 60000);
		if (diffMin < 1) return 'just now';
		if (diffMin < 60) return `${diffMin}m ago`;
		const diffH = Math.floor(diffMin / 60);
		if (diffH < 24) return `${diffH}h ago`;
		return d.toLocaleDateString();
	}

	function formatCost(usd: number | null): string {
		if (usd == null) return '-';
		if (usd < 0.01) return `$${usd.toFixed(4)}`;
		return `$${usd.toFixed(2)}`;
	}

	function formatDuration(ms: number | null): string {
		if (ms == null) return '-';
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}

	function statusColor(status: string): string {
		switch (status) {
			case 'completed': return 'bg-[var(--color-success)]';
			case 'running': return 'bg-[var(--color-accent)] animate-pulse';
			case 'error': return 'bg-[var(--color-error)]';
			case 'cancelled': return 'bg-[var(--color-warning)]';
			default: return 'bg-[var(--color-text-muted)]';
		}
	}
</script>

<div class="flex flex-col">
	<!-- Table -->
	<div class="overflow-x-auto">
		<table class="w-full text-xs">
			<thead>
				<tr class="border-b border-[var(--color-border)] text-left text-[var(--color-text-muted)]">
					<th class="px-3 py-2 font-medium">Time</th>
					<th class="px-3 py-2 font-medium">Workspace</th>
					<th class="px-3 py-2 font-medium">Prompt</th>
					<th class="px-3 py-2 font-medium">Skill</th>
					<th class="px-3 py-2 font-medium">Status</th>
					<th class="px-3 py-2 font-medium text-right">Cost</th>
					<th class="px-3 py-2 font-medium text-right">Duration</th>
				</tr>
			</thead>
			<tbody>
				{#each historyStore.sessions as session (session.id)}
					<tr
						class="cursor-pointer border-b border-[var(--color-border)]/50 transition-colors hover:bg-[var(--color-bg-card)]"
						onclick={() => onSelect?.(session)}
					>
						<td class="whitespace-nowrap px-3 py-2.5 text-[var(--color-text-muted)]">
							{formatTime(session.started_at)}
						</td>
						<td class="px-3 py-2.5">
							<span class="text-[var(--color-text-secondary)]">{session.workspace_name}</span>
						</td>
						<td class="max-w-xs truncate px-3 py-2.5 text-[var(--color-text-primary)]">
							{session.prompt}
						</td>
						<td class="px-3 py-2.5">
							{#if session.skill}
								<span class="rounded bg-[var(--color-accent)]/10 px-1.5 py-0.5 text-[var(--color-accent)]">
									/{session.skill}
								</span>
							{:else if session.agent}
								<span class="rounded bg-[var(--color-info)]/10 px-1.5 py-0.5 text-[var(--color-info)]">
									@{session.agent}
								</span>
							{:else}
								<span class="text-[var(--color-text-muted)]">-</span>
							{/if}
						</td>
						<td class="px-3 py-2.5">
							<div class="flex items-center gap-1.5">
								<span class="h-1.5 w-1.5 rounded-full {statusColor(session.status)}"></span>
								<span class="text-[var(--color-text-secondary)]">{session.status}</span>
							</div>
						</td>
						<td class="whitespace-nowrap px-3 py-2.5 text-right">
							<span class="text-[var(--color-accent)]">{formatCost(session.cost_usd)}</span>
						</td>
						<td class="whitespace-nowrap px-3 py-2.5 text-right text-[var(--color-text-muted)]">
							{formatDuration(session.duration_ms)}
						</td>
					</tr>
				{/each}
				{#if historyStore.sessions.length === 0 && !historyStore.loading}
					<tr>
						<td colspan="7" class="px-3 py-8 text-center text-[var(--color-text-muted)]">
							No sessions found
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>

	<!-- Pagination -->
	{#if historyStore.total > historyStore.pageSize}
		<div class="flex items-center justify-between border-t border-[var(--color-border)] px-3 py-2">
			<span class="text-[var(--color-text-muted)]">
				{historyStore.total} sessions — page {historyStore.page + 1} of {historyStore.totalPages}
			</span>
			<div class="flex gap-1">
				<button
					onclick={() => historyStore.prevPage()}
					disabled={historyStore.page === 0}
					class="rounded p-1 text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] disabled:opacity-30"
				>
					<ChevronLeft class="h-4 w-4" />
				</button>
				<button
					onclick={() => historyStore.nextPage()}
					disabled={historyStore.page >= historyStore.totalPages - 1}
					class="rounded p-1 text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] disabled:opacity-30"
				>
					<ChevronRight class="h-4 w-4" />
				</button>
			</div>
		</div>
	{/if}
</div>
