<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Shell from '$lib/components/Shell.svelte';
	import PipelineGraph from '$lib/components/PipelineGraph.svelte';
	import { pipelineStore } from '$stores/pipelines.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import { githubStore } from '$stores/github.svelte';
	import { Plus, Trash2, ChevronUp, ChevronDown, Wand2, ArrowLeft, ArrowRight, Workflow, Play } from '@lucide/svelte';
	import { addPipelineStep, updatePipelineStep, deletePipelineStep } from '$services/api';
	import type { PipelineStep } from '$types/index';

	// Wizard state
	let wizardStep = $state(1);
	let sourceType = $state<'spec' | 'milestone'>('spec');
	let pipelineName = $state('');
	let pipelineDescription = $state('');
	let specText = $state('');
	let selectedWorkspaceId = $state('');
	let selectedMilestone = $state<number | null>(null);
	let generating = $state(false);
	let createdPipelineId = $state<string | null>(null);

	// Step editing state
	let editableSteps = $state<
		{
			id: string;
			name: string;
			description: string;
			agent: string;
			prompt_template: string;
			depends_on: string[];
			position: number;
		}[]
	>([]);

	onMount(() => {
		workspacesStore.fetch();
		pipelineStore.loadAgents();
	});

	// Cargar milestones cuando cambia workspace
	$effect(() => {
		if (selectedWorkspaceId && sourceType === 'milestone') {
			githubStore.loadForWorkspace(selectedWorkspaceId);
		}
	});

	async function handleGenerate() {
		if (!selectedWorkspaceId || !pipelineName) return;

		generating = true;
		pipelineStore.error = null;

		const pipelineId = await pipelineStore.generate(
			selectedWorkspaceId,
			pipelineName,
			sourceType === 'spec' ? specText : undefined,
			sourceType === 'milestone' ? selectedMilestone ?? undefined : undefined
		);

		generating = false;

		if (pipelineId) {
			createdPipelineId = pipelineId;
			editableSteps = pipelineStore.steps.map((s) => ({
				id: s.id,
				name: s.name,
				description: s.description ?? '',
				agent: s.agent ?? '',
				prompt_template: s.prompt_template ?? '',
				depends_on: s.depends_on ?? [],
				position: s.position
			}));
			wizardStep = 2;
		}
	}

	async function handleCreateManual() {
		if (!selectedWorkspaceId || !pipelineName) return;

		const pipelineId = await pipelineStore.create(
			selectedWorkspaceId,
			pipelineName,
			pipelineDescription
		);

		createdPipelineId = pipelineId;
		editableSteps = [];
		wizardStep = 2;
	}

	function addStep() {
		editableSteps = [
			...editableSteps,
			{
				id: '',
				name: 'New Step',
				description: '',
				agent: '',
				prompt_template: '',
				depends_on: [],
				position: editableSteps.length
			}
		];
	}

	function removeStep(index: number) {
		editableSteps = editableSteps.filter((_, i) => i !== index);
		// Reindex positions
		editableSteps = editableSteps.map((s, i) => ({ ...s, position: i }));
	}

	function moveStep(index: number, direction: -1 | 1) {
		const target = index + direction;
		if (target < 0 || target >= editableSteps.length) return;
		const arr = [...editableSteps];
		[arr[index], arr[target]] = [arr[target], arr[index]];
		editableSteps = arr.map((s, i) => ({ ...s, position: i }));
	}

	function goToConfirm() {
		wizardStep = 3;
	}

	async function handleSaveDraft() {
		if (!createdPipelineId) return;
		await syncStepsToBackend();
		goto(`/pipelines/${createdPipelineId}`);
	}

	async function handleExecute() {
		if (!createdPipelineId) return;
		await syncStepsToBackend();
		goto(`/pipelines/${createdPipelineId}`);
		// Pequeño delay para que cargue la página
		setTimeout(() => {
			pipelineStore.execute(createdPipelineId!);
		}, 500);
	}

	async function syncStepsToBackend() {
		if (!createdPipelineId) return;
		// Sincronizar steps editados con backend
		for (const step of editableSteps) {
			if (step.id) {
				await updatePipelineStep(createdPipelineId, step.id, {
					name: step.name,
					description: step.description || undefined,
					agent: step.agent || undefined,
					prompt_template: step.prompt_template || undefined,
					position: step.position,
					depends_on: step.depends_on
				});
			} else {
				await addPipelineStep(createdPipelineId, {
					position: step.position,
					name: step.name,
					description: step.description || undefined,
					agent: step.agent || undefined,
					prompt_template: step.prompt_template || undefined,
					depends_on: step.depends_on
				});
			}
		}
	}

	// Convertir editableSteps a PipelineStep para preview
	let previewSteps = $derived<PipelineStep[]>(
		editableSteps.map((s, i) => ({
			id: s.id || `temp-${i}`,
			pipeline_id: createdPipelineId ?? '',
			position: s.position,
			name: s.name,
			description: s.description || null,
			agent: s.agent || null,
			skill: null,
			model: null,
			prompt_template: s.prompt_template || null,
			status: 'pending' as const,
			session_id: null,
			output_summary: null,
			depends_on: s.depends_on,
			created_at: '',
			started_at: null,
			finished_at: null
		}))
	);

	let agentNames = $derived(pipelineStore.availableAgents.map((a) => a.name));
</script>

<Shell>
	{#snippet topbar()}
		<div class="flex flex-1 items-center gap-3">
			<a href="/pipelines" class="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">
				<Workflow class="h-4 w-4" />
			</a>
			<span class="text-[var(--color-text-muted)]">/</span>
			<span class="text-sm font-medium text-[var(--color-text-primary)]">New Pipeline</span>
			<!-- Step indicator -->
			<div class="ml-auto flex items-center gap-1">
				{#each [1, 2, 3] as num}
					<span
						class="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-medium {wizardStep >= num
							? 'bg-[var(--color-accent)] text-black'
							: 'bg-[var(--color-bg-card)] text-[var(--color-text-muted)]'}"
					>
						{num}
					</span>
				{/each}
			</div>
		</div>
	{/snippet}

	{#snippet content()}
		<div class="mx-auto max-w-4xl p-6">
			<!-- Step 1: Source -->
			{#if wizardStep === 1}
				<div class="flex flex-col gap-4">
					<h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Create Pipeline</h2>

					<!-- Workspace selector -->
					<div>
						<label class="mb-1 block text-xs text-[var(--color-text-muted)]">Workspace</label>
						<select
							class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
							bind:value={selectedWorkspaceId}
						>
							<option value="">Select workspace...</option>
							{#each workspacesStore.workspaces as ws}
								<option value={ws.id}>{ws.name}</option>
							{/each}
						</select>
					</div>

					<!-- Pipeline name -->
					<div>
						<label class="mb-1 block text-xs text-[var(--color-text-muted)]">Pipeline Name</label>
						<input
							class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
							placeholder="e.g., Sprint 3 Implementation"
							bind:value={pipelineName}
						/>
					</div>

					<!-- Description -->
					<div>
						<label class="mb-1 block text-xs text-[var(--color-text-muted)]">Description (optional)</label>
						<input
							class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
							placeholder="Brief description..."
							bind:value={pipelineDescription}
						/>
					</div>

					<!-- Source type toggle -->
					<div>
						<label class="mb-2 block text-xs text-[var(--color-text-muted)]">Source</label>
						<div class="flex gap-2">
							<button
								class="rounded-md px-4 py-2 text-xs font-medium {sourceType === 'spec'
									? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]/30'
									: 'bg-[var(--color-bg-card)] text-[var(--color-text-secondary)] border border-[var(--color-border)]'}"
								onclick={() => (sourceType = 'spec')}
							>
								From Spec
							</button>
							<button
								class="rounded-md px-4 py-2 text-xs font-medium {sourceType === 'milestone'
									? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]/30'
									: 'bg-[var(--color-bg-card)] text-[var(--color-text-secondary)] border border-[var(--color-border)]'}"
								onclick={() => (sourceType = 'milestone')}
							>
								From Milestone
							</button>
						</div>
					</div>

					<!-- Source content -->
					{#if sourceType === 'spec'}
						<div>
							<label class="mb-1 block text-xs text-[var(--color-text-muted)]">Specification</label>
							<textarea
								class="h-40 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
								placeholder="Describe what the pipeline should accomplish..."
								bind:value={specText}
							></textarea>
						</div>
					{:else}
						<div>
							<label class="mb-1 block text-xs text-[var(--color-text-muted)]">Milestone</label>
							{#if githubStore.loading}
								<p class="text-xs text-[var(--color-text-muted)]">Loading milestones...</p>
							{:else if !githubStore.hasRepo}
								<p class="text-xs text-red-400">This workspace has no GitHub repo configured</p>
							{:else}
								<select
									class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
									bind:value={selectedMilestone}
								>
									<option value={null}>Select milestone...</option>
									{#each githubStore.milestones as ms}
										<option value={ms.number}>
											{ms.title} ({ms.open_issues} open)
										</option>
									{/each}
								</select>
							{/if}
						</div>
					{/if}

					{#if pipelineStore.error}
						<p class="text-xs text-red-400">{pipelineStore.error}</p>
					{/if}

					<!-- Action buttons -->
					<div class="flex gap-2">
						<button
							class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
							disabled={!selectedWorkspaceId || !pipelineName || generating ||
								(sourceType === 'spec' && !specText) ||
								(sourceType === 'milestone' && !selectedMilestone)}
							onclick={handleGenerate}
						>
							<Wand2 class="h-3.5 w-3.5" />
							{generating ? 'Generating...' : 'Generate Plan'}
						</button>
						<button
							class="flex items-center gap-1.5 rounded-md bg-[var(--color-bg-card)] px-4 py-2 text-xs font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)] border border-[var(--color-border)]"
							disabled={!selectedWorkspaceId || !pipelineName}
							onclick={handleCreateManual}
						>
							Create Empty
						</button>
					</div>
				</div>

			<!-- Step 2: Review steps -->
			{:else if wizardStep === 2}
				<div class="flex flex-col gap-4">
					<div class="flex items-center justify-between">
						<h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Review Steps</h2>
						<div class="flex gap-2">
							<button
								class="flex items-center gap-1 rounded-md bg-[var(--color-bg-card)] px-3 py-1.5 text-xs text-[var(--color-text-secondary)] border border-[var(--color-border)]"
								onclick={() => (wizardStep = 1)}
							>
								<ArrowLeft class="h-3 w-3" />
								Back
							</button>
							<button
								class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)]/20 px-3 py-1.5 text-xs font-medium text-[var(--color-accent)] border border-[var(--color-accent)]/30"
								onclick={addStep}
							>
								<Plus class="h-3 w-3" />
								Add Step
							</button>
						</div>
					</div>

					{#if editableSteps.length === 0}
						<div class="flex flex-col items-center gap-2 py-10">
							<p class="text-sm text-[var(--color-text-muted)]">No steps yet</p>
							<button
								class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-black"
								onclick={addStep}
							>
								<Plus class="h-3 w-3" />
								Add first step
							</button>
						</div>
					{:else}
						<div class="flex flex-col gap-3">
							{#each editableSteps as step, i}
								<div class="glass rounded-lg border border-[var(--color-border)] p-3">
									<div class="mb-2 flex items-center justify-between">
										<span class="text-[10px] font-medium text-[var(--color-text-muted)]">
											Step #{step.position}
										</span>
										<div class="flex items-center gap-1">
											<button
												class="rounded p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
												onclick={() => moveStep(i, -1)}
												disabled={i === 0}
											>
												<ChevronUp class="h-3 w-3" />
											</button>
											<button
												class="rounded p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
												onclick={() => moveStep(i, 1)}
												disabled={i === editableSteps.length - 1}
											>
												<ChevronDown class="h-3 w-3" />
											</button>
											<button
												class="rounded p-1 text-[var(--color-text-muted)] hover:text-red-400"
												onclick={() => removeStep(i)}
											>
												<Trash2 class="h-3 w-3" />
											</button>
										</div>
									</div>

									<div class="grid grid-cols-2 gap-2">
										<div>
											<label class="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">Name</label>
											<input
												class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
												bind:value={editableSteps[i].name}
											/>
										</div>
										<div>
											<label class="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">Agent</label>
											<select
												class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
												bind:value={editableSteps[i].agent}
											>
												<option value="">Auto-detect</option>
												{#each agentNames as name}
													<option value={name}>{name}</option>
												{/each}
											</select>
										</div>
									</div>

									<div class="mt-2">
										<label class="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">Description</label>
										<input
											class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
											bind:value={editableSteps[i].description}
										/>
									</div>

									<div class="mt-2">
										<label class="mb-0.5 block text-[10px] text-[var(--color-text-muted)]">Prompt Template</label>
										<textarea
											class="h-16 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg-primary)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
											bind:value={editableSteps[i].prompt_template}
											placeholder={'Use {{spec}}, {{prev_output}}, {{step.ID.output}}...'}
										></textarea>
									</div>
								</div>
							{/each}
						</div>
					{/if}

					{#if editableSteps.length > 0}
						<div class="flex justify-end">
							<button
								class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-black"
								onclick={goToConfirm}
							>
								Review
								<ArrowRight class="h-3.5 w-3.5" />
							</button>
						</div>
					{/if}
				</div>

			<!-- Step 3: Confirm -->
			{:else if wizardStep === 3}
				<div class="flex flex-col gap-4">
					<div class="flex items-center justify-between">
						<h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Confirm Pipeline</h2>
						<button
							class="flex items-center gap-1 rounded-md bg-[var(--color-bg-card)] px-3 py-1.5 text-xs text-[var(--color-text-secondary)] border border-[var(--color-border)]"
							onclick={() => (wizardStep = 2)}
						>
							<ArrowLeft class="h-3 w-3" />
							Back
						</button>
					</div>

					<!-- Summary -->
					<div class="glass rounded-lg border border-[var(--color-border)] p-4">
						<h3 class="text-sm font-medium text-[var(--color-text-primary)]">{pipelineName}</h3>
						{#if pipelineDescription}
							<p class="mt-1 text-xs text-[var(--color-text-muted)]">{pipelineDescription}</p>
						{/if}
						<div class="mt-2 flex gap-3 text-xs text-[var(--color-text-muted)]">
							<span>{editableSteps.length} steps</span>
							<span>{new Set(editableSteps.map((s) => s.agent).filter(Boolean)).size} agents</span>
						</div>
					</div>

					<!-- DAG Preview -->
					{#if previewSteps.length > 0}
						<div>
							<p class="mb-2 text-xs font-medium text-[var(--color-text-muted)]">Pipeline Graph Preview</p>
							<PipelineGraph steps={previewSteps} />
						</div>
					{/if}

					<!-- Action buttons -->
					<div class="flex justify-end gap-2">
						<button
							class="rounded-md bg-[var(--color-bg-card)] px-4 py-2 text-xs font-medium text-[var(--color-text-secondary)] border border-[var(--color-border)]"
							onclick={handleSaveDraft}
						>
							Save as Draft
						</button>
						<button
							class="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-black"
							onclick={handleExecute}
						>
							<Play class="h-3.5 w-3.5" />
							Create & Execute
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/snippet}

	{#snippet bottombar()}
		<span class="text-[var(--color-text-muted)]">
			Step {wizardStep} of 3
		</span>
	{/snippet}
</Shell>
