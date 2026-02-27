<script lang="ts">
	import { Plus, X, Save } from '@lucide/svelte';
	import type { Workflow, WorkflowParam } from '$types/index';

	let {
		workflow = null,
		onSave
	}: {
		workflow?: Workflow | null;
		onSave: (data: {
			name: string;
			description: string;
			category: string;
			prompt_template: string;
			parameters: WorkflowParam[];
			model: string;
		}) => void;
	} = $props();

	let name = $state(workflow?.name ?? '');
	let description = $state(workflow?.description ?? '');
	let category = $state(workflow?.category ?? 'custom');
	let promptTemplate = $state(workflow?.prompt_template ?? '');
	let model = $state(workflow?.model ?? '');
	let parameters = $state<WorkflowParam[]>(workflow?.parameters ?? []);

	function addParameter() {
		parameters = [
			...parameters,
			{ key: '', label: '', type: 'text', required: false }
		];
	}

	function removeParameter(idx: number) {
		parameters = parameters.filter((_, i) => i !== idx);
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!name.trim() || !promptTemplate.trim()) return;

		onSave({
			name: name.trim(),
			description: description.trim(),
			category,
			prompt_template: promptTemplate,
			parameters: parameters.filter((p) => p.key.trim()),
			model: model || ''
		});
	}

	let canSave = $derived(name.trim() && promptTemplate.trim());
</script>

<form class="flex flex-col gap-4" onsubmit={handleSubmit}>
	<div>
		<label for="wf-name" class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]">
			Name <span class="text-red-400">*</span>
		</label>
		<input
			id="wf-name"
			bind:value={name}
			placeholder="My Workflow"
			class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
		/>
	</div>

	<div>
		<label for="wf-desc" class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]">
			Description
		</label>
		<textarea
			id="wf-desc"
			bind:value={description}
			rows="2"
			placeholder="What does this workflow do?"
			class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
		></textarea>
	</div>

	<div class="grid grid-cols-2 gap-3">
		<div>
			<label
				for="wf-category"
				class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
			>
				Category
			</label>
			<select
				id="wf-category"
				bind:value={category}
				class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
			>
				<option value="development">Development</option>
				<option value="testing">Testing</option>
				<option value="review">Review</option>
				<option value="devops">DevOps</option>
				<option value="custom">Custom</option>
			</select>
		</div>
		<div>
			<label
				for="wf-model"
				class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
			>
				Model
			</label>
			<select
				id="wf-model"
				bind:value={model}
				class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
			>
				<option value="">Default</option>
				<option value="opus">Opus</option>
				<option value="sonnet">Sonnet</option>
				<option value="haiku">Haiku</option>
			</select>
		</div>
	</div>

	<div>
		<label
			for="wf-template"
			class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
		>
			Prompt Template <span class="text-red-400">*</span>
		</label>
		<textarea
			id="wf-template"
			bind:value={promptTemplate}
			rows="6"
			placeholder="Use double braces for parameter placeholders..."
			class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 font-mono text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
		></textarea>
		<p class="mt-1 text-[10px] text-[var(--color-text-muted)]">
			Use {'{{key}}'} syntax for dynamic parameters
		</p>
	</div>

	<!-- Parameters editor -->
	<div>
		<div class="mb-2 flex items-center justify-between">
			<span class="text-xs font-medium text-[var(--color-text-secondary)]">Parameters</span>
			<button
				type="button"
				class="flex items-center gap-1 rounded px-2 py-1 text-[10px] text-[var(--color-accent)] hover:bg-[var(--color-accent)]/10"
				onclick={addParameter}
			>
				<Plus class="h-3 w-3" /> Add
			</button>
		</div>

		{#each parameters as param, idx}
			<div class="mb-2 flex items-start gap-2 rounded-lg border border-[var(--color-border)] p-2">
				<div class="grid flex-1 grid-cols-2 gap-2">
					<input
						bind:value={param.key}
						placeholder="key"
						class="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1 font-mono text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
					/>
					<input
						bind:value={param.label}
						placeholder="Label"
						class="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
					/>
					<select
						bind:value={param.type}
						class="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1 text-xs text-[var(--color-text-primary)]"
					>
						<option value="text">Text</option>
						<option value="textarea">Textarea</option>
						<option value="number">Number</option>
						<option value="select">Select</option>
					</select>
					<label class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
						<input type="checkbox" bind:checked={param.required} />
						Required
					</label>
				</div>
				<button
					type="button"
					class="rounded p-1 text-[var(--color-text-muted)] hover:bg-red-500/10 hover:text-red-400"
					onclick={() => removeParameter(idx)}
				>
					<X class="h-3.5 w-3.5" />
				</button>
			</div>
		{/each}
	</div>

	<button
		type="submit"
		disabled={!canSave}
		class="flex items-center justify-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
	>
		<Save class="h-4 w-4" />
		{workflow ? 'Update' : 'Create'} Workflow
	</button>
</form>
