import type { AgUiEvent, ToolCall } from '$types/index';
import { createSession, cancelSession } from '$services/api';
import { connectSession } from '$services/sse';
import { monitorStore } from './monitor.svelte';
import { toastStore } from './toasts.svelte';

export class TabSession {
	status = $state<'idle' | 'running' | 'completed' | 'error'>('idle');
	sessionId = $state<string | null>(null);
	outputChunks = $state<string[]>([]);
	toolCalls = $state<ToolCall[]>([]);
	costUsd = $state<number | null>(null);
	inputTokens = $state<number | null>(null);
	outputTokens = $state<number | null>(null);
	cacheReadTokens = $state<number | null>(null);
	cacheWriteTokens = $state<number | null>(null);
	model = $state<string | null>(null);
	numTurns = $state<number | null>(null);
	durationMs = $state<number | null>(null);
	errorMsg = $state<string | null>(null);

	private eventSource: EventSource | null = null;

	fullOutput = $derived(this.outputChunks.join(''));
	totalTokens = $derived((this.inputTokens ?? 0) + (this.outputTokens ?? 0));

	async start(workspaceId: string, prompt: string, skill?: string, agent?: string, model?: string) {
		this.reset();
		monitorStore.reset();
		this.status = 'running';

		try {
			const { session_id } = await createSession({
				workspace_id: workspaceId,
				prompt,
				skill,
				agent,
				model
			});
			this.sessionId = session_id;

			this.eventSource = connectSession(
				session_id,
				(event) => this.handleEvent(event),
				() => {
					if (this.status === 'running') {
						this.status = 'error';
						this.errorMsg = 'SSE connection lost';
					}
				}
			);
		} catch (e) {
			this.status = 'error';
			this.errorMsg = e instanceof Error ? e.message : 'Failed to start session';
		}
	}

	handleEvent(event: AgUiEvent) {
		switch (event.type) {
			case 'RunStarted':
				this.status = 'running';
				break;

			case 'TextMessageContent':
				if (event.text) {
					this.outputChunks = [...this.outputChunks, event.text];
				}
				break;

			case 'ToolCallStart':
				if (event.tool_call_id && event.tool_name) {
					this.toolCalls = [
						...this.toolCalls,
						{
							id: event.tool_call_id,
							name: event.tool_name,
							input: event.tool_input ?? '',
							result: null,
							isError: false,
							status: 'running'
						}
					];
				}
				break;

			case 'ToolCallResult':
				if (event.tool_call_id) {
					this.toolCalls = this.toolCalls.map((tc) =>
						tc.id === event.tool_call_id
							? {
									...tc,
									result: event.tool_result ?? null,
									isError: event.tool_is_error ?? false,
									status: event.tool_is_error ? 'error' : 'completed'
								}
							: tc
					);
				}
				break;

			case 'ToolCallEnd':
				if (event.tool_call_id) {
					this.toolCalls = this.toolCalls.map((tc) =>
						tc.id === event.tool_call_id && tc.status === 'running'
							? { ...tc, status: 'completed' }
							: tc
					);
				}
				break;

			case 'StateSnapshot':
				if (event.state?.model) {
					this.model = event.state.model as string;
				}
				break;

			case 'RunFinished':
				this.status = 'completed';
				this.costUsd = event.cost_usd ?? null;
				this.inputTokens = event.input_tokens ?? null;
				this.outputTokens = event.output_tokens ?? null;
				this.cacheReadTokens = event.cache_read_tokens ?? null;
				this.cacheWriteTokens = event.cache_write_tokens ?? null;
				this.numTurns = event.num_turns ?? null;
				this.durationMs = event.duration_ms ?? null;
				if (event.model) this.model = event.model;
				this.disconnect();
				this._notifyIfBackground('completed');
				break;

			case 'RunError':
				this.status = 'error';
				this.errorMsg = event.error ?? 'Unknown error';
				this.disconnect();
				this._notifyIfBackground('error');
				break;
		}

		// Forward al monitor para construir arbol de ejecucion
		monitorStore.processEvent(event);
	}

	async cancel() {
		if (this.sessionId) {
			try {
				await cancelSession(this.sessionId);
			} catch {
				// ignore
			}
		}
		this.disconnect();
		this.status = 'error';
		this.errorMsg = 'Cancelled';
	}

	reset() {
		this.disconnect();
		this.status = 'idle';
		this.sessionId = null;
		this.outputChunks = [];
		this.toolCalls = [];
		this.costUsd = null;
		this.inputTokens = null;
		this.outputTokens = null;
		this.cacheReadTokens = null;
		this.cacheWriteTokens = null;
		this.model = null;
		this.numTurns = null;
		this.durationMs = null;
		this.errorMsg = null;
	}

	private _notifyIfBackground(result: 'completed' | 'error') {
		const tab = tabsStore.tabs.find((t) => t.session === this);
		if (!tab || tab.id === tabsStore.activeTabId) return;
		const label = tab.label.length > 25 ? tab.label.slice(0, 25) + '...' : tab.label;
		if (result === 'completed') {
			toastStore.add(`"${label}" finished`, 'success');
		} else {
			toastStore.add(`"${label}" failed`, 'error');
		}
	}

	private disconnect() {
		if (this.eventSource) {
			this.eventSource.close();
			this.eventSource = null;
		}
	}
}

export interface Tab {
	id: string;
	label: string;
	session: TabSession;
}

let _nextId = 1;

class TabsStore {
	tabs = $state<Tab[]>([]);
	activeTabId = $state<string | null>(null);

	activeTab = $derived(this.tabs.find((t) => t.id === this.activeTabId) ?? null);
	activeSession = $derived(this.activeTab?.session ?? null);

	addTab(label?: string): Tab {
		const id = String(_nextId++);
		const tab: Tab = {
			id,
			label: label ?? `Tab ${id}`,
			session: new TabSession()
		};
		this.tabs = [...this.tabs, tab];
		this.activeTabId = id;
		return tab;
	}

	closeTab(id: string) {
		const tab = this.tabs.find((t) => t.id === id);
		if (tab) {
			tab.session.reset();
		}
		this.tabs = this.tabs.filter((t) => t.id !== id);
		if (this.activeTabId === id) {
			this.activeTabId = this.tabs.length > 0 ? this.tabs[this.tabs.length - 1].id : null;
		}
		// Siempre mantener al menos una tab
		if (this.tabs.length === 0) {
			this.addTab();
		}
	}

	switchTab(id: string) {
		if (this.tabs.some((t) => t.id === id)) {
			this.activeTabId = id;
		}
	}

	ensureTab(): Tab {
		if (this.tabs.length === 0) {
			return this.addTab();
		}
		return this.activeTab ?? this.tabs[0];
	}
}

export const tabsStore = new TabsStore();
