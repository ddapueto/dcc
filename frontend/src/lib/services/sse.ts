import type { AgUiEvent, AgUiEventType, PipelineEvent, PipelineEventType } from '$types/index';

const ALL_EVENT_TYPES: AgUiEventType[] = [
	'RunStarted',
	'RunFinished',
	'RunError',
	'TextMessageStart',
	'TextMessageContent',
	'TextMessageEnd',
	'ToolCallStart',
	'ToolCallEnd',
	'ToolCallResult',
	'StateSnapshot',
	'Custom'
];

const PIPELINE_EVENT_TYPES: PipelineEventType[] = [
	'PipelineStarted',
	'PipelineStepStarted',
	'PipelineStepCompleted',
	'PipelineStepFailed',
	'PipelineCompleted',
	'PipelineFailed'
];

export function connectSession(
	sessionId: string,
	onEvent: (event: AgUiEvent) => void,
	onError: (error: Event) => void
): EventSource {
	const url = `/api/sessions/${sessionId}/stream`;
	const es = new EventSource(url);

	for (const eventType of ALL_EVENT_TYPES) {
		es.addEventListener(eventType, (e: MessageEvent) => {
			try {
				const data: AgUiEvent = JSON.parse(e.data);
				onEvent(data);
			} catch (err) {
				console.error('Failed to parse SSE event:', err, e.data);
			}
		});
	}

	es.onerror = onError;

	return es;
}

export function connectPipeline(
	pipelineId: string,
	maxParallel: number,
	onEvent: (event: PipelineEvent) => void,
	onError: (error: Event) => void
): EventSource {
	const url = `/api/pipelines/${pipelineId}/execute?max_parallel=${maxParallel}`;
	const es = new EventSource(url);

	for (const eventType of PIPELINE_EVENT_TYPES) {
		es.addEventListener(eventType, (e: MessageEvent) => {
			try {
				const data: PipelineEvent = JSON.parse(e.data);
				onEvent(data);
			} catch (err) {
				console.error('Failed to parse pipeline SSE event:', err, e.data);
			}
		});
	}

	es.onerror = onError;

	return es;
}
