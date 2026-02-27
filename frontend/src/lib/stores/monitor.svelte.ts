import type { AgUiEvent, MonitorTask, MonitorTaskStatus } from '$types/index';
import { fetchMonitorTasks } from '$services/api';

class MonitorStore {
	tasks = $state<MonitorTask[]>([]);
	selectedTaskId = $state<string | null>(null);
	active = $state(false);
	loading = $state(false);

	selectedTask = $derived(this.tasks.find((t) => t.id === this.selectedTaskId) ?? null);
	rootTasks = $derived(this.tasks.filter((t) => !t.parent_id));
	taskTree = $derived(this._buildTree());
	totalTasks = $derived(this.tasks.length);
	runningTasks = $derived(this.tasks.filter((t) => t.status === 'running').length);
	completedTasks = $derived(this.tasks.filter((t) => t.status === 'completed').length);
	failedTasks = $derived(this.tasks.filter((t) => t.status === 'failed').length);

	private _taskStack: string[] = [];
	private _toolToTask = new Map<string, string>();
	private _taskStartTimes = new Map<string, number>();
	private _idCounter = 0;

	processEvent(event: AgUiEvent): void {
		if (event.type === 'ToolCallStart') {
			this._handleToolStart(event);
		} else if (event.type === 'ToolCallResult') {
			this._handleToolResult(event);
		} else if (event.type === 'ToolCallEnd') {
			this._handleToolEnd(event);
		}
	}

	reset() {
		this.tasks = [];
		this.selectedTaskId = null;
		this.loading = false;
		this._taskStack = [];
		this._toolToTask.clear();
		this._taskStartTimes.clear();
		this._idCounter = 0;
	}

	/** Cargar monitor tasks historicas desde backend (para sesiones ya completadas o reload). */
	async loadFromSession(sessionId: string) {
		if (this.tasks.length > 0) return; // Ya tiene datos live
		this.loading = true;
		try {
			const data = await fetchMonitorTasks(sessionId);
			if (data.tasks.length > 0) {
				this.tasks = data.tasks;
			}
		} catch {
			// Monitor data not available — not critical
		} finally {
			this.loading = false;
		}
	}

	private _handleToolStart(event: AgUiEvent) {
		if (!event.tool_call_id || !event.tool_name) return;

		const parentId = this._taskStack.length > 0 ? this._taskStack[this._taskStack.length - 1] : null;
		const depth = this._taskStack.length;
		const taskId = `mt_${++this._idCounter}`;

		const metadata = this._extractTaskMetadata(event.tool_name, event.tool_input);

		const task: MonitorTask = {
			id: taskId,
			session_id: event.session_id,
			parent_id: parentId,
			tool_call_id: event.tool_call_id,
			tool_name: event.tool_name,
			description: metadata.description,
			subagent_type: metadata.subagent_type,
			subagent_model: metadata.subagent_model,
			status: 'running',
			input_summary: event.tool_input?.slice(0, 500) ?? null,
			output_summary: null,
			depth,
			started_at: new Date().toISOString(),
			finished_at: null,
			duration_ms: null
		};

		this.tasks = [...this.tasks, task];
		this._toolToTask.set(event.tool_call_id, taskId);
		this._taskStartTimes.set(taskId, performance.now());

		// Si es Task tool, push al stack
		if (event.tool_name === 'Task') {
			this._taskStack.push(taskId);
		}
	}

	private _handleToolResult(event: AgUiEvent) {
		if (!event.tool_call_id) return;

		const taskId = this._toolToTask.get(event.tool_call_id);
		if (!taskId) return;

		const status: MonitorTaskStatus = event.tool_is_error ? 'failed' : 'completed';
		const startTime = this._taskStartTimes.get(taskId);
		const durationMs = startTime ? Math.round(performance.now() - startTime) : null;

		this.tasks = this.tasks.map((t) =>
			t.id === taskId
				? {
						...t,
						status,
						output_summary: event.tool_result?.slice(0, 500) ?? null,
						finished_at: new Date().toISOString(),
						duration_ms: durationMs
					}
				: t
		);

		// Pop del stack si era Task
		const idx = this._taskStack.indexOf(taskId);
		if (idx !== -1) {
			this._taskStack.splice(idx, 1);
		}
	}

	private _handleToolEnd(event: AgUiEvent) {
		if (!event.tool_call_id) return;

		const taskId = this._toolToTask.get(event.tool_call_id);
		if (!taskId) return;

		// Solo cerrar si aun esta running
		const task = this.tasks.find((t) => t.id === taskId);
		if (!task || task.status !== 'running') return;

		const startTime = this._taskStartTimes.get(taskId);
		const durationMs = startTime ? Math.round(performance.now() - startTime) : null;

		this.tasks = this.tasks.map((t) =>
			t.id === taskId
				? {
						...t,
						status: 'completed' as MonitorTaskStatus,
						finished_at: new Date().toISOString(),
						duration_ms: durationMs
					}
				: t
		);

		const idx = this._taskStack.indexOf(taskId);
		if (idx !== -1) {
			this._taskStack.splice(idx, 1);
		}
	}

	private _extractTaskMetadata(
		toolName: string,
		toolInput?: string
	): { description: string; subagent_type: string | null; subagent_model: string | null } {
		const result = { description: toolName, subagent_type: null as string | null, subagent_model: null as string | null };
		if (!toolInput) return result;

		try {
			const parsed = JSON.parse(toolInput);
			if (toolName === 'Task') {
				result.description = (parsed.description || parsed.prompt || toolName).slice(0, 200);
				result.subagent_type = parsed.subagent_type || null;
				result.subagent_model = parsed.model || null;
			} else if (['Read', 'Write', 'Edit'].includes(toolName)) {
				result.description = parsed.file_path || toolName;
			} else if (toolName === 'Bash') {
				result.description = (parsed.command || '').slice(0, 100) || toolName;
			} else if (['Glob', 'Grep'].includes(toolName)) {
				result.description = parsed.pattern || toolName;
			}
			return result;
		} catch {
			return result;
		}
	}

	private _buildTree(): MonitorTask[] {
		const taskMap = new Map<string, MonitorTask>();
		const roots: MonitorTask[] = [];

		// Crear copias con children array
		for (const task of this.tasks) {
			taskMap.set(task.id, { ...task, children: [] });
		}

		// Construir arbol
		for (const task of taskMap.values()) {
			if (task.parent_id && taskMap.has(task.parent_id)) {
				const parent = taskMap.get(task.parent_id)!;
				parent.children = [...(parent.children || []), task];
			} else {
				roots.push(task);
			}
		}

		return roots;
	}
}

export const monitorStore = new MonitorStore();
