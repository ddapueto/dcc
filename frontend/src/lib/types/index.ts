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
	tools: string[];
	disallowed_tools: string[];
	permission_mode: string | null;
	max_turns: number | null;
	skills: string[];
	memory: string | null;
	background: boolean;
	isolation: string | null;
	system_prompt: string;
}

export interface RegisteredAgent extends AgentInfo {
	id: string;
	workspace_id: string;
	first_seen_at: string;
	last_seen_at: string;
	is_active: boolean;
}

export interface AgentUsageStats {
	name: string;
	sessions: number;
	total_cost: number;
	avg_duration_ms: number | null;
	success_rate: number;
	total_input_tokens?: number;
	total_output_tokens?: number;
}

export interface AgentDelegation {
	parent_agent: string | null;
	subagent_type: string;
	count: number;
	avg_duration_ms: number | null;
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

// --- Workflows ---

export type WorkflowCategory = 'development' | 'testing' | 'review' | 'devops' | 'custom';

export interface WorkflowParam {
	key: string;
	label: string;
	type: 'text' | 'textarea' | 'number' | 'select';
	required: boolean;
	default?: string;
	options?: string[];
}

export interface Workflow {
	id: string;
	workspace_id: string;
	name: string;
	description: string | null;
	category: WorkflowCategory;
	icon: string;
	prompt_template: string;
	parameters: WorkflowParam[];
	model: string | null;
	is_builtin: boolean;
	usage_count: number;
	last_used_at: string | null;
	created_at: string;
}

// --- Monitor ---

export type MonitorTaskStatus = 'running' | 'completed' | 'failed';

export interface MonitorTask {
	id: string;
	session_id: string;
	parent_id: string | null;
	tool_call_id: string | null;
	tool_name: string;
	description: string | null;
	subagent_type: string | null;
	subagent_model: string | null;
	status: MonitorTaskStatus;
	input_summary: string | null;
	output_summary: string | null;
	depth: number;
	started_at: string;
	finished_at: string | null;
	duration_ms: number | null;
	children?: MonitorTask[];
}
