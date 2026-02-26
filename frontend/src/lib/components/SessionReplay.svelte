<script lang="ts">
	import { X, Wrench, MessageSquare } from '@lucide/svelte';
	import { fetchSessionEvents } from '$services/api';
	import MarkdownRenderer from './MarkdownRenderer.svelte';
	import DiffViewer from './DiffViewer.svelte';
	import type { SessionEvent, Session, ToolCall, AgUiEvent } from '$types/index';

	let {
		sessionId,
		onClose
	}: {
		sessionId: string;
		onClose: () => void;
	} = $props();

	let session = $state<Session | null>(null);
	let events = $state<SessionEvent[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Reconstruidos desde events
	let outputChunks = $state<string[]>([]);
	let toolCalls = $state<ToolCall[]>([]);

	$effect(() => {
		loadEvents(sessionId);
	});

	async function loadEvents(id: string) {
		loading = true;
		error = null;
		try {
			const data = await fetchSessionEvents(id);
			session = data.session;
			events = data.events;
			reconstruct(data.events);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load events';
		} finally {
			loading = false;
		}
	}

	function reconstruct(evts: SessionEvent[]) {
		const chunks: string[] = [];
		const tools: ToolCall[] = [];

		for (const evt of evts) {
			let parsed: AgUiEvent;
			try {
				parsed = JSON.parse(evt.data);
			} catch {
				continue;
			}

			switch (parsed.type) {
				case 'TextMessageContent':
					if (parsed.text) chunks.push(parsed.text);
					break;
				case 'ToolCallStart':
					if (parsed.tool_call_id && parsed.tool_name) {
						tools.push({
							id: parsed.tool_call_id,
							name: parsed.tool_name,
							input: parsed.tool_input ?? '',
							result: null,
							isError: false,
							status: 'completed'
						});
					}
					break;
				case 'ToolCallResult':
					if (parsed.tool_call_id) {
						const tc = tools.find((t) => t.id === parsed.tool_call_id);
						if (tc) {
							tc.result = parsed.tool_result ?? null;
							tc.isError = parsed.tool_is_error ?? false;
							tc.status = parsed.tool_is_error ? 'error' : 'completed';
						}
					}
					break;
			}
		}

		outputChunks = chunks;
		toolCalls = tools;
	}

	const fullOutput = $derived(outputChunks.join(''));
</script>

<!-- Modal overlay -->
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
	<div class="glass mx-4 flex max-h-[85vh] w-full max-w-4xl flex-col rounded-xl border border-[var(--color-border)]">
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
			<div class="min-w-0 flex-1">
				{#if session}
					<p class="truncate text-sm font-medium text-[var(--color-text-primary)]">
						{session.prompt}
					</p>
					<div class="mt-0.5 flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
						<span>{session.status}</span>
						{#if session.model}
							<span>· {session.model}</span>
						{/if}
						{#if session.cost_usd != null}
							<span class="text-[var(--color-accent)]">· ${session.cost_usd.toFixed(4)}</span>
						{/if}
					</div>
				{/if}
			</div>
			<button
				onclick={onClose}
				class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]"
			>
				<X class="h-4 w-4" />
			</button>
		</div>

		<!-- Body -->
		<div class="flex min-h-0 flex-1">
			{#if loading}
				<div class="flex flex-1 items-center justify-center">
					<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
				</div>
			{:else if error}
				<div class="flex flex-1 items-center justify-center">
					<span class="text-sm text-[var(--color-error)]">{error}</span>
				</div>
			{:else}
				<!-- Output -->
				<div class="min-w-0 flex-1 overflow-y-auto p-4">
					{#if fullOutput}
						<div class="text-sm leading-relaxed text-[var(--color-text-primary)]">
							<MarkdownRenderer content={fullOutput} streaming={false} />
						</div>
						{#if session?.status === 'completed'}
							<div class="mt-4">
								<DiffViewer sessionId={sessionId} collapsed={true} />
							</div>
						{/if}
					{:else}
						<div class="flex items-center justify-center py-8">
							<MessageSquare class="mr-2 h-5 w-5 text-[var(--color-text-muted)]" />
							<span class="text-sm text-[var(--color-text-muted)]">No output</span>
						</div>
					{/if}
				</div>

				<!-- Tool calls -->
				{#if toolCalls.length > 0}
					<div class="w-72 shrink-0 overflow-y-auto border-l border-[var(--color-border)] p-3">
						<div class="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
							Tool Calls ({toolCalls.length})
						</div>
						<div class="flex flex-col gap-1.5">
							{#each toolCalls as tc (tc.id)}
								<div class="glass rounded-lg px-3 py-2">
									<div class="flex items-center gap-2">
										<Wrench class="h-3 w-3 shrink-0 text-[var(--color-accent)]" />
										<span class="min-w-0 flex-1 truncate text-xs font-medium text-[var(--color-text-primary)]">
											{tc.name}
										</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
