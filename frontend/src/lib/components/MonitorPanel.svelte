<script lang="ts">
	import { Activity, GitBranch, CheckCircle, XCircle, Clock } from '@lucide/svelte';
	import MonitorGraph from './MonitorGraph.svelte';
	import TaskDetail from './TaskDetail.svelte';
	import type { MonitorTask } from '$types/index';
	import { monitorStore } from '$stores/monitor.svelte';

	let {
		sessionId
	}: {
		sessionId: string | null;
	} = $props();

	let viewMode = $state<'graph' | 'timeline'>('timeline');

	function selectTask(task: MonitorTask) {
		monitorStore.selectedTaskId = task.id;
	}
</script>

<div class="flex h-full flex-col">
	<!-- Stats bar -->
	<div class="flex items-center gap-3 border-b border-[var(--color-border)] px-3 py-2">
		<span class="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]">
			<Activity class="h-3 w-3" />
			{monitorStore.totalTasks} tasks
		</span>
		{#if monitorStore.runningTasks > 0}
			<span class="flex items-center gap-1 text-[10px] text-[var(--color-accent)]">
				<Clock class="h-3 w-3 animate-pulse" />
				{monitorStore.runningTasks} running
			</span>
		{/if}
		{#if monitorStore.completedTasks > 0}
			<span class="flex items-center gap-1 text-[10px] text-green-400">
				<CheckCircle class="h-3 w-3" />
				{monitorStore.completedTasks}
			</span>
		{/if}
		{#if monitorStore.failedTasks > 0}
			<span class="flex items-center gap-1 text-[10px] text-red-400">
				<XCircle class="h-3 w-3" />
				{monitorStore.failedTasks}
			</span>
		{/if}

		<div class="ml-auto flex gap-1">
			<button
				class="rounded px-2 py-0.5 text-[10px] transition-colors {viewMode === 'timeline'
					? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
					: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
				onclick={() => (viewMode = 'timeline')}
			>
				Timeline
			</button>
			<button
				class="rounded px-2 py-0.5 text-[10px] transition-colors {viewMode === 'graph'
					? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
					: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
				onclick={() => (viewMode = 'graph')}
			>
				<GitBranch class="inline h-3 w-3" /> Graph
			</button>
		</div>
	</div>

	{#if monitorStore.tasks.length === 0}
		<div class="flex flex-1 items-center justify-center">
			<p class="text-xs text-[var(--color-text-muted)]">
				Tool calls will appear here as they execute...
			</p>
		</div>
	{:else if viewMode === 'graph'}
		<div class="flex flex-1 gap-2 overflow-hidden p-2">
			<div class="flex-1 overflow-auto">
				<MonitorGraph
					tasks={monitorStore.tasks}
					selectedTaskId={monitorStore.selectedTaskId}
					onSelectTask={selectTask}
				/>
			</div>
			{#if monitorStore.selectedTask}
				<div class="w-64 shrink-0">
					<TaskDetail task={monitorStore.selectedTask} allTasks={monitorStore.tasks} />
				</div>
			{/if}
		</div>
	{:else}
		<!-- Timeline view: lista vertical -->
		<div class="flex-1 overflow-y-auto">
			{#each monitorStore.tasks as task (task.id)}
				{@const statusDot =
					task.status === 'running'
						? 'bg-[var(--color-accent)]'
						: task.status === 'completed'
							? 'bg-green-400'
							: 'bg-red-400'}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="flex cursor-pointer items-start gap-2 border-b border-[var(--color-border)] px-3 py-2 transition-colors hover:bg-[var(--color-bg-card)] {monitorStore.selectedTaskId === task.id ? 'bg-[var(--color-accent-dim)]' : ''}"
					style="padding-left: {12 + task.depth * 16}px"
					onclick={() => (monitorStore.selectedTaskId = task.id)}
				>
					<span
						class="mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full {statusDot}"
						class:animate-pulse={task.status === 'running'}
					></span>
					<div class="min-w-0 flex-1">
						<div class="flex items-center gap-1.5">
							<span class="text-[11px] font-medium text-[var(--color-text-primary)]">
								{task.tool_name}
							</span>
							{#if task.duration_ms !== null}
								<span class="text-[9px] text-[var(--color-text-muted)]">
									{task.duration_ms < 1000
										? `${task.duration_ms}ms`
										: `${(task.duration_ms / 1000).toFixed(1)}s`}
								</span>
							{/if}
						</div>
						{#if task.description}
							<p class="truncate text-[10px] text-[var(--color-text-muted)]">
								{task.description}
							</p>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		{#if monitorStore.selectedTask}
			<div class="h-48 shrink-0 border-t border-[var(--color-border)]">
				<TaskDetail task={monitorStore.selectedTask} allTasks={monitorStore.tasks} />
			</div>
		{/if}
	{/if}
</div>
