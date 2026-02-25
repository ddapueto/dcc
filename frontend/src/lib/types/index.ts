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
