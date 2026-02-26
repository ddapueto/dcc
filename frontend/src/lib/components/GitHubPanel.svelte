<script lang="ts">
	import { ChevronDown, ChevronRight, CircleDot, GitPullRequest, Milestone } from '@lucide/svelte';
	import { githubStore } from '$stores/github.svelte';
	import type { GitHubIssue } from '$types/index';

	let {
		workspaceId,
		onSelectIssue
	}: {
		workspaceId: string;
		onSelectIssue?: (issue: GitHubIssue) => void;
	} = $props();

	let showIssues = $state(true);
	let showPRs = $state(false);
	let showMilestones = $state(false);

	$effect(() => {
		if (workspaceId) {
			githubStore.loadForWorkspace(workspaceId);
		}
	});
</script>

{#if githubStore.loading}
	<div class="flex items-center justify-center py-4">
		<span class="text-xs text-[var(--color-text-muted)]">Loading GitHub...</span>
	</div>
{:else if githubStore.error && !githubStore.hasRepo}
	<!-- No repo — silently hide -->
{:else}
	<div class="flex flex-col gap-2">
		<!-- Issues -->
		<div class="glass rounded-lg">
			<button
				class="flex w-full items-center gap-2 px-3 py-2 text-left"
				onclick={() => (showIssues = !showIssues)}
			>
				{#if showIssues}
					<ChevronDown class="h-3 w-3 text-[var(--color-text-muted)]" />
				{:else}
					<ChevronRight class="h-3 w-3 text-[var(--color-text-muted)]" />
				{/if}
				<CircleDot class="h-3 w-3 text-[var(--color-success)]" />
				<span class="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
					Issues ({githubStore.issues.length})
				</span>
			</button>
			{#if showIssues && githubStore.issues.length > 0}
				<div class="border-t border-[var(--color-border)] px-2 py-1">
					{#each githubStore.issues.slice(0, 15) as issue (issue.number)}
						<button
							class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left hover:bg-[var(--color-bg-card)]"
							onclick={() => onSelectIssue?.(issue)}
							title={issue.title}
						>
							<span class="h-1.5 w-1.5 shrink-0 rounded-full {issue.state === 'open' ? 'bg-[var(--color-success)]' : 'bg-purple-400'}"></span>
							<span class="text-[10px] text-[var(--color-text-muted)]">#{issue.number}</span>
							<span class="min-w-0 flex-1 truncate text-xs text-[var(--color-text-primary)]">
								{issue.title}
							</span>
							{#each issue.labels.slice(0, 2) as label}
								<span
									class="shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-medium"
									style="background-color: #{label.color}20; color: #{label.color}"
								>
									{label.name}
								</span>
							{/each}
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Pull Requests -->
		<div class="glass rounded-lg">
			<button
				class="flex w-full items-center gap-2 px-3 py-2 text-left"
				onclick={() => (showPRs = !showPRs)}
			>
				{#if showPRs}
					<ChevronDown class="h-3 w-3 text-[var(--color-text-muted)]" />
				{:else}
					<ChevronRight class="h-3 w-3 text-[var(--color-text-muted)]" />
				{/if}
				<GitPullRequest class="h-3 w-3 text-[var(--color-info)]" />
				<span class="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
					PRs ({githubStore.pulls.length})
				</span>
			</button>
			{#if showPRs && githubStore.pulls.length > 0}
				<div class="border-t border-[var(--color-border)] px-2 py-1">
					{#each githubStore.pulls as pr (pr.number)}
						<a
							href={pr.html_url}
							target="_blank"
							rel="noopener"
							class="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-[var(--color-bg-card)]"
						>
							<span class="text-[10px] text-[var(--color-text-muted)]">#{pr.number}</span>
							<span class="min-w-0 flex-1 truncate text-xs text-[var(--color-text-primary)]">
								{pr.title}
							</span>
							{#if pr.draft}
								<span class="shrink-0 rounded-full bg-[var(--color-text-muted)]/10 px-1.5 py-0.5 text-[9px] text-[var(--color-text-muted)]">
									draft
								</span>
							{/if}
							<span class="shrink-0 text-[9px] text-[var(--color-text-muted)]">
								{pr.head.ref}
							</span>
						</a>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Milestones -->
		{#if githubStore.milestones.length > 0}
			<div class="glass rounded-lg">
				<button
					class="flex w-full items-center gap-2 px-3 py-2 text-left"
					onclick={() => (showMilestones = !showMilestones)}
				>
					{#if showMilestones}
						<ChevronDown class="h-3 w-3 text-[var(--color-text-muted)]" />
					{:else}
						<ChevronRight class="h-3 w-3 text-[var(--color-text-muted)]" />
					{/if}
					<Milestone class="h-3 w-3 text-[var(--color-warning)]" />
					<span class="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
						Milestones ({githubStore.milestones.length})
					</span>
				</button>
				{#if showMilestones}
					<div class="border-t border-[var(--color-border)] px-2 py-1">
						{#each githubStore.milestones as ms (ms.number)}
							{@const total = ms.open_issues + ms.closed_issues}
							{@const pct = total > 0 ? Math.round((ms.closed_issues / total) * 100) : 0}
							<button
								class="flex w-full flex-col gap-1 rounded px-2 py-1.5 text-left hover:bg-[var(--color-bg-card)]"
								onclick={() => githubStore.selectMilestone(workspaceId, ms.number)}
							>
								<div class="flex items-center gap-2">
									<span class="min-w-0 flex-1 truncate text-xs text-[var(--color-text-primary)]">
										{ms.title}
									</span>
									<span class="shrink-0 text-[10px] text-[var(--color-text-muted)]">
										{ms.closed_issues}/{total}
									</span>
								</div>
								<div class="h-1 w-full rounded-full bg-[var(--color-bg-input)]">
									<div
										class="h-full rounded-full bg-[var(--color-accent)]"
										style="width: {pct}%"
									></div>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>
{/if}
