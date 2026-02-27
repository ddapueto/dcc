<script lang="ts">
	import { Rocket, Eye } from '@lucide/svelte';
	import type { Workflow } from '$types/index';

	let {
		workflow,
		workspaceId,
		onLaunch
	}: {
		workflow: Workflow;
		workspaceId: string;
		onLaunch: (params: Record<string, string>, model?: string) => void;
	} = $props();

	let paramValues = $state<Record<string, string>>({});
	let selectedModel = $state<string>(workflow.model || '');
	let showPreview = $state(false);

	// Inicializar con defaults
	$effect(() => {
		const defaults: Record<string, string> = {};
		for (const param of workflow.parameters) {
			defaults[param.key] = param.default ?? '';
		}
		paramValues = defaults;
	});

	let resolvedPrompt = $derived(() => {
		let prompt = workflow.prompt_template;
		for (const [key, value] of Object.entries(paramValues)) {
			prompt = prompt.replaceAll(`{{${key}}}`, value || `{{${key}}}`);
		}
		return prompt;
	});

	let canLaunch = $derived(() => {
		return workflow.parameters
			.filter((p) => p.required)
			.every((p) => paramValues[p.key]?.trim());
	});

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!canLaunch()) return;
		onLaunch(paramValues, selectedModel || undefined);
	}
</script>

<form class="flex flex-col gap-4" onsubmit={handleSubmit}>
	<div class="space-y-3">
		{#each workflow.parameters as param}
			<div>
				<label
					for="param-{param.key}"
					class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
				>
					{param.label}
					{#if param.required}
						<span class="text-red-400">*</span>
					{/if}
				</label>

				{#if param.type === 'textarea'}
					<textarea
						id="param-{param.key}"
						bind:value={paramValues[param.key]}
						rows="3"
						placeholder={param.default || ''}
						class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)] focus:outline-none"
					></textarea>
				{:else if param.type === 'select' && param.options}
					<select
						id="param-{param.key}"
						bind:value={paramValues[param.key]}
						class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
					>
						{#each param.options as option}
							<option value={option}>{option}</option>
						{/each}
					</select>
				{:else}
					<input
						id="param-{param.key}"
						type={param.type === 'number' ? 'number' : 'text'}
						bind:value={paramValues[param.key]}
						placeholder={param.default || ''}
						class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-accent)] focus:outline-none"
					/>
				{/if}
			</div>
		{/each}
	</div>

	<!-- Model selector -->
	<div>
		<label
			for="workflow-model"
			class="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]"
		>
			Model (optional)
		</label>
		<select
			id="workflow-model"
			bind:value={selectedModel}
			class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
		>
			<option value="">Default</option>
			<option value="opus">Opus</option>
			<option value="sonnet">Sonnet</option>
			<option value="haiku">Haiku</option>
		</select>
	</div>

	<!-- Preview toggle -->
	<button
		type="button"
		class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-accent)]"
		onclick={() => (showPreview = !showPreview)}
	>
		<Eye class="h-3.5 w-3.5" />
		{showPreview ? 'Hide' : 'Preview'} resolved prompt
	</button>

	{#if showPreview}
		<pre
			class="max-h-48 overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-3 text-xs text-[var(--color-text-secondary)]"
		>{resolvedPrompt()}</pre>
	{/if}

	<button
		type="submit"
		disabled={!canLaunch()}
		class="flex items-center justify-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
	>
		<Rocket class="h-4 w-4" />
		Launch
	</button>
</form>
