import {
	fetchPipelines,
	fetchPipeline,
	createPipeline,
	generatePipeline,
	deletePipeline,
	cancelPipeline,
	pausePipeline,
	resumePipeline,
	fetchAvailableAgents
} from '$services/api';
import { connectPipeline } from '$services/sse';
import type {
	Pipeline,
	PipelineStep,
	PipelineEvent,
	AgentRouteInfo
} from '$types/index';

class PipelineStore {
	pipelines = $state<Pipeline[]>([]);
	current = $state<Pipeline | null>(null);
	steps = $state<PipelineStep[]>([]);
	executing = $state(false);
	stepsCompleted = $state(0);
	stepsTotal = $state(0);
	availableAgents = $state<AgentRouteInfo[]>([]);

	loading = $state(false);
	error = $state<string | null>(null);

	progress = $derived(this.stepsTotal > 0 ? Math.round((this.stepsCompleted / this.stepsTotal) * 100) : 0);

	private eventSource: EventSource | null = null;

	async loadPipelines(workspaceId?: string) {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchPipelines(workspaceId);
			this.pipelines = data.pipelines;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load pipelines';
		} finally {
			this.loading = false;
		}
	}

	async loadPipeline(pipelineId: string) {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchPipeline(pipelineId);
			this.current = data.pipeline;
			this.steps = data.steps;
			this.stepsTotal = data.steps.length;
			this.stepsCompleted = data.steps.filter(
				(s) => s.status === 'completed' || s.status === 'failed' || s.status === 'skipped'
			).length;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load pipeline';
		} finally {
			this.loading = false;
		}
	}

	async create(workspaceId: string, name: string, description?: string) {
		const data = await createPipeline({ workspace_id: workspaceId, name, description });
		return data.pipeline_id;
	}

	async generate(
		workspaceId: string,
		name: string,
		spec?: string,
		milestoneNumber?: number
	) {
		this.loading = true;
		this.error = null;
		try {
			const data = await generatePipeline({
				workspace_id: workspaceId,
				name,
				spec,
				milestone_number: milestoneNumber
			});
			this.current = data.pipeline;
			this.steps = data.steps;
			this.stepsTotal = data.steps.length;
			return data.pipeline.id;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to generate pipeline';
			return null;
		} finally {
			this.loading = false;
		}
	}

	async remove(pipelineId: string) {
		await deletePipeline(pipelineId);
		this.pipelines = this.pipelines.filter((p) => p.id !== pipelineId);
		if (this.current?.id === pipelineId) {
			this.current = null;
			this.steps = [];
		}
	}

	execute(pipelineId: string, maxParallel: number = 3) {
		this.disconnect();
		this.executing = true;
		this.stepsCompleted = 0;
		this.error = null;

		this.eventSource = connectPipeline(
			pipelineId,
			maxParallel,
			(event) => this.handleEvent(event),
			(error) => {
				console.error('Pipeline SSE error:', error);
				this.executing = false;
				this.disconnect();
			}
		);
	}

	handleEvent(event: PipelineEvent) {
		switch (event.type) {
			case 'PipelineStarted':
				this.stepsTotal = event.steps_total ?? this.stepsTotal;
				if (this.current) {
					this.current = { ...this.current, status: 'running' };
				}
				break;

			case 'PipelineStepStarted':
				this.steps = this.steps.map((s) =>
					s.id === event.step_id ? { ...s, status: 'running' as const } : s
				);
				break;

			case 'PipelineStepCompleted':
				this.steps = this.steps.map((s) =>
					s.id === event.step_id ? { ...s, status: 'completed' as const } : s
				);
				this.stepsCompleted++;
				break;

			case 'PipelineStepFailed':
				this.steps = this.steps.map((s) =>
					s.id === event.step_id ? { ...s, status: 'failed' as const } : s
				);
				this.stepsCompleted++;
				break;

			case 'PipelineCompleted':
				this.executing = false;
				if (this.current) {
					this.current = {
						...this.current,
						status: 'completed',
						total_cost: event.cost_usd ?? this.current.total_cost,
						total_duration_ms: event.duration_ms ?? this.current.total_duration_ms
					};
				}
				this.disconnect();
				break;

			case 'PipelineFailed':
				this.executing = false;
				if (this.current) {
					this.current = {
						...this.current,
						status: 'failed',
						total_cost: event.cost_usd ?? this.current.total_cost,
						total_duration_ms: event.duration_ms ?? this.current.total_duration_ms
					};
				}
				this.disconnect();
				break;
		}
	}

	async cancel() {
		if (this.current) {
			await cancelPipeline(this.current.id);
		}
		this.executing = false;
		this.disconnect();
	}

	async pause() {
		if (this.current) {
			await pausePipeline(this.current.id);
			this.current = { ...this.current, status: 'paused' };
		}
	}

	async resume() {
		if (this.current) {
			await resumePipeline(this.current.id);
			this.current = { ...this.current, status: 'running' };
		}
	}

	async loadAgents() {
		try {
			const data = await fetchAvailableAgents();
			this.availableAgents = data.agents;
		} catch {
			this.availableAgents = [];
		}
	}

	disconnect() {
		if (this.eventSource) {
			this.eventSource.close();
			this.eventSource = null;
		}
	}

	reset() {
		this.disconnect();
		this.pipelines = [];
		this.current = null;
		this.steps = [];
		this.executing = false;
		this.stepsCompleted = 0;
		this.stepsTotal = 0;
		this.loading = false;
		this.error = null;
	}
}

export const pipelineStore = new PipelineStore();
