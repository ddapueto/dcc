export interface Tenant {
	id: string;
	name: string;
	config_dir: string;
	claude_alias: string;
	is_active: boolean;
}

export interface Workspace {
	id: string;
	tenant_id: string;
	tenant_name: string;
	claude_alias: string;
	name: string;
	path: string;
	agents_count: number;
	skills_count: number;
	has_claude_md: boolean;
	repo_owner: string | null;
	repo_name: string | null;
	last_scanned_at: string | null;
}

export interface AgentInfo {
	name: string;
	filename: string;
	description: string;
	model: string | null;
}

export interface SkillInfo {
	name: string;
	filename: string;
	description: string;
}

export interface WorkspaceDetail {
	id: string;
	tenant_id: string;
	tenant_name: string;
	name: string;
	path: string;
	has_claude_md: boolean;
	repo_owner: string | null;
	repo_name: string | null;
	agents: AgentInfo[];
	skills: SkillInfo[];
}

export interface Session {
	id: string;
	workspace_id: string;
	cli_session_id: string | null;
	skill: string | null;
	agent: string | null;
	prompt: string;
	status: 'pending' | 'running' | 'completed' | 'error' | 'cancelled';
	model: string | null;
	cost_usd: number | null;
	input_tokens: number | null;
	output_tokens: number | null;
	num_turns: number | null;
	duration_ms: number | null;
	started_at: string;
	finished_at: string | null;
}

export type AgUiEventType =
	| 'RunStarted'
	| 'RunFinished'
	| 'RunError'
	| 'TextMessageStart'
	| 'TextMessageContent'
	| 'TextMessageEnd'
	| 'ToolCallStart'
	| 'ToolCallEnd'
	| 'ToolCallResult'
	| 'StateSnapshot'
	| 'Custom';

export interface AgUiEvent {
	type: AgUiEventType;
	session_id: string;
	timestamp?: string;
	// Text
	message_id?: string;
	text?: string;
	role?: string;
	// Tool calls
	tool_call_id?: string;
	tool_name?: string;
	tool_input?: string;
	tool_result?: string;
	tool_is_error?: boolean;
	// Run
	model?: string;
	cost_usd?: number;
	input_tokens?: number;
	output_tokens?: number;
	cache_read_tokens?: number;
	cache_write_tokens?: number;
	num_turns?: number;
	duration_ms?: number;
	cli_session_id?: string;
	// State
	state?: Record<string, unknown>;
	// Error
	error?: string;
}

export interface ToolCall {
	id: string;
	name: string;
	input: string;
	result: string | null;
	isError: boolean;
	status: 'running' | 'completed' | 'error';
}

export interface SessionHistoryItem extends Session {
	workspace_name: string;
	tenant_id: string;
	tenant_name: string;
}

export interface SessionEvent {
	id: number;
	session_id: string;
	seq: number;
	event_type: AgUiEventType;
	data: string;
	created_at: string;
}

export interface RuleFile {
	name: string;
	filename: string;
	content: string;
}

// --- Analytics ---

export interface AnalyticsSummary {
	total_sessions: number;
	total_cost: number;
	total_input_tokens: number;
	total_output_tokens: number;
	cost_7d: number;
	sessions_7d: number;
	cost_24h: number;
	sessions_24h: number;
	by_status: Record<string, number>;
}

export interface CostByWorkspace {
	workspace_name: string;
	tenant_name: string;
	session_count: number;
	total_cost: number;
	total_input_tokens: number;
	total_output_tokens: number;
}

export interface CostTrendPoint {
	date: string;
	sessions: number;
	cost: number;
}

export interface TopSkillItem {
	name: string;
	kind: 'skill' | 'agent' | 'prompt';
	count: number;
	total_cost: number;
}

export interface TokenEfficiency {
	total_input: number;
	total_output: number;
	cache_read: number;
	cache_write: number;
	cache_hit_ratio: number;
}

// --- GitHub ---

export interface GitHubMilestone {
	number: number;
	title: string;
	description: string | null;
	state: string;
	open_issues: number;
	closed_issues: number;
	due_on: string | null;
}

export interface GitHubIssue {
	number: number;
	title: string;
	body: string | null;
	state: string;
	labels: { name: string; color: string }[];
	assignees: { login: string }[];
	milestone?: { number: number };
	created_at: string;
	html_url: string;
}

export interface GitHubPR {
	number: number;
	title: string;
	state: string;
	head: { ref: string };
	base: { ref: string };
	draft: boolean;
	user: { login: string };
	html_url: string;
	created_at: string;
}

// --- Diff ---

export interface SessionDiff {
	diff_stat: string | null;
	diff_content: string | null;
	files_changed: number;
	insertions: number;
	deletions: number;
}

// --- MCP ---

export interface McpServer {
	name: string;
	command: string;
	args: string[];
	source: 'workspace' | 'global';
}

// --- Pipelines ---

export type PipelineStatus = 'draft' | 'ready' | 'running' | 'paused' | 'completed' | 'failed';
export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface Pipeline {
	id: string;
	workspace_id: string;
	name: string;
	description: string | null;
	spec: string | null;
	status: PipelineStatus;
	source_type: string | null;
	source_ref: string | null;
	total_cost: number;
	total_duration_ms: number;
	created_at: string;
	started_at: string | null;
	finished_at: string | null;
}

export interface PipelineStep {
	id: string;
	pipeline_id: string;
	position: number;
	name: string;
	description: string | null;
	agent: string | null;
	skill: string | null;
	model: string | null;
	prompt_template: string | null;
	status: StepStatus;
	session_id: string | null;
	output_summary: string | null;
	depends_on: string[];
	created_at: string;
	started_at: string | null;
	finished_at: string | null;
}

export interface AgentRouteInfo {
	name: string;
	keywords: string[];
}

export type PipelineEventType =
	| 'PipelineStarted'
	| 'PipelineStepStarted'
	| 'PipelineStepCompleted'
	| 'PipelineStepFailed'
	| 'PipelineCompleted'
	| 'PipelineFailed';

export interface PipelineEvent {
	type: PipelineEventType;
	session_id: string;
	pipeline_id?: string;
	step_id?: string;
	step_name?: string;
	step_position?: number;
	step_agent?: string;
	step_status?: string;
	steps_completed?: number;
	steps_total?: number;
	cost_usd?: number;
	duration_ms?: number;
	error?: string;
}
