import type { Workflow } from '$types/index';
import {
	fetchWorkflows,
	fetchWorkflow,
	createWorkflow,
	updateWorkflow,
	deleteWorkflow,
	launchWorkflow
} from '$services/api';

class WorkflowStore {
	workflows = $state<Workflow[]>([]);
	current = $state<Workflow | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	async loadWorkflows(workspaceId?: string, category?: string) {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchWorkflows(workspaceId, category);
			this.workflows = data.workflows;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load workflows';
		} finally {
			this.loading = false;
		}
	}

	async loadWorkflow(id: string) {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchWorkflow(id);
			this.current = data.workflow;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load workflow';
		} finally {
			this.loading = false;
		}
	}

	async create(params: {
		workspace_id: string;
		name: string;
		prompt_template: string;
		description?: string;
		category?: string;
		icon?: string;
		parameters?: Array<Record<string, unknown>>;
		model?: string;
	}): Promise<string> {
		const data = await createWorkflow(params);
		await this.loadWorkflows(params.workspace_id);
		return data.workflow_id;
	}

	async update(id: string, updates: Record<string, unknown>) {
		await updateWorkflow(id, updates);
		if (this.current?.id === id) {
			await this.loadWorkflow(id);
		}
	}

	async remove(id: string) {
		await deleteWorkflow(id);
		this.workflows = this.workflows.filter((w) => w.id !== id);
		if (this.current?.id === id) {
			this.current = null;
		}
	}

	async launch(
		id: string,
		workspaceId: string,
		params: Record<string, string>,
		model?: string
	): Promise<string> {
		const data = await launchWorkflow(id, workspaceId, params, model);
		return data.session_id;
	}
}

export const workflowStore = new WorkflowStore();
