<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/state';
	import Shell from '$lib/components/Shell.svelte';
	import PipelineGraph from '$lib/components/PipelineGraph.svelte';
	import PipelineControls from '$lib/components/PipelineControls.svelte';
	import StepDetail from '$lib/components/StepDetail.svelte';
	import { pipelineStore } from '$stores/pipelines.svelte';
	import { Workflow } from '@lucide/svelte';
	import type { PipelineStep } from '$types/index';

	let selectedStepId = $state<string | null>(null);

	let selectedStep = $derived(
		pipelineStore.steps.find((s) => s.id === selectedStepId) ?? null
	);

	const statusColors: Record<string, string> = {
		draft: 'text-gray-400',
		ready: 'text-blue-400',
		running: 'text-[var(--color-accent)]',
		paused: 'text-yellow-400',
		completed: 'text-green-400',
		failed: 'text-red-400'
	};

	onMount(() => {
		const id = page.params.id;
		if (id) {
			pipelineStore.loadPipeline(id);
		}
	});

	onDestroy(() => {
		pipelineStore.disconnect();
	});

	function handleSelectStep(step: PipelineStep) {
		selectedStepId = step.id;
	}

	function handleExecute() {
		if (pipelineStore.current) {
			pipelineStore.execute(pipelineStore.current.id);
		}
	}

	function handleCancel() {
		pipelineStore.cancel();
	}

	function handlePause() {
		pipelineStore.pause();
	}

	function handleResume() {
		pipelineStore.resume();
	}
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex flex-1 items-center gap-3">
			<a href="/pipelines" class="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">
				<Workflow class="h-4 w-4" />
			</a>
			<span class="text-[var(--color-text-muted)]">/</span>
			{#if pipelineStore.current}
				<span class="text-sm font-medium text-[var(--color-text-primary)]">
					{pipelineStore.current.name}
				</span>
				<span
					class="rounded-full bg-[var(--color-bg-card)] px-2 py-0.5 text-[10px] font-medium {statusColors[
						pipelineStore.current.status
					] ?? 'text-gray-400'}"
				>
					{pipelineStore.current.status}
				</span>
				<span class="text-xs text-[var(--color-text-muted)]">
					{pipelineStore.steps.length} steps
				</span>
			{:else}
				<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
			{/if}
		</div>
	{/snippet}

	{#snippet content()}
		{#if pipelineStore.loading && !pipelineStore.current}
			<div class="flex h-full items-center justify-center">
				<span class="text-sm text-[var(--color-text-muted)]">Loading pipeline...</span>
			</div>
		{:else if pipelineStore.current}
			<div class="flex h-full flex-col">
				<!-- Controls strip -->
				<div class="border-b border-[var(--color-border)] px-4 py-2">
					<PipelineControls
						pipeline={pipelineStore.current}
						executing={pipelineStore.executing}
						progress={pipelineStore.progress}
						onExecute={handleExecute}
						onCancel={handleCancel}
						onPause={handlePause}
						onResume={handleResume}
					/>
				</div>

				<!-- Split view -->
				<div class="flex min-h-0 flex-1">
					<!-- Left: DAG Graph (60%) -->
					<div class="flex-[3] overflow-auto border-r border-[var(--color-border)] p-4">
						<PipelineGraph
							steps={pipelineStore.steps}
							{selectedStepId}
							onSelectStep={handleSelectStep}
						/>
					</div>

					<!-- Right: Step Detail (40%) -->
					<div class="flex-[2] overflow-hidden">
						<StepDetail
							step={selectedStep}
							pipelineStatus={pipelineStore.current.status}
						/>
					</div>
				</div>
			</div>
		{:else}
			<div class="flex h-full items-center justify-center">
				<span class="text-sm text-[var(--color-text-muted)]">Pipeline not found</span>
			</div>
		{/if}
	{/snippet}

	{#snippet bottombar()}
		{#if pipelineStore.current}
			<span class="text-[var(--color-text-muted)]">
				{pipelineStore.stepsCompleted}/{pipelineStore.stepsTotal} steps completed
			</span>
			{#if pipelineStore.current.total_cost > 0}
				<span class="text-[var(--color-text-muted)]">
					${pipelineStore.current.total_cost.toFixed(4)}
				</span>
			{/if}
		{/if}
	{/snippet}
</Shell>
