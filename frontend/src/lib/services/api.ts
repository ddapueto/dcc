import type {
	Workspace,
	Tenant,
	WorkspaceDetail,
	SessionHistoryItem,
	SessionEvent,
	Session,
	RuleFile,
	AnalyticsSummary,
	CostByWorkspace,
	CostTrendPoint,
	TopSkillItem,
	TokenEfficiency,
	GitHubMilestone,
	GitHubIssue,
	GitHubPR,
	SessionDiff,
	McpServer,
	Workflow,
	MonitorTask
} from '$types/index';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...options
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`API ${res.status}: ${body}`);
	}
	return res.json();
}

// --- Workspaces ---

export async function fetchWorkspaces(): Promise<{
	tenants: Tenant[];
	workspaces: Workspace[];
}> {
	return request('/workspaces');
}

export async function fetchWorkspaceDetail(id: string): Promise<WorkspaceDetail> {
	return request(`/workspaces/${id}`);
}

export async function scanWorkspaces(): Promise<{ scanned: number; results: unknown[] }> {
	return request('/workspaces/scan', { method: 'POST' });
}

export async function createWorkspace(params: {
	tenant_id: string;
	name: string;
	path: string;
}): Promise<{ id: string }> {
	return request('/workspaces', {
		method: 'POST',
		body: JSON.stringify(params)
	});
}

export async function deleteWorkspace(id: string): Promise<{ deleted: boolean }> {
	return request(`/workspaces/${id}`, { method: 'DELETE' });
}

export async function createTenant(params: {
	name: string;
	config_dir: string;
	claude_alias: string;
}): Promise<{ id: string }> {
	return request('/workspaces/tenants', {
		method: 'POST',
		body: JSON.stringify(params)
	});
}

export async function deleteTenant(id: string): Promise<{ deleted: boolean }> {
	return request(`/workspaces/tenants/${id}`, { method: 'DELETE' });
}

// --- Sessions ---

export async function createSession(params: {
	workspace_id: string;
	prompt: string;
	skill?: string;
	agent?: string;
	model?: string;
}): Promise<{ session_id: string }> {
	return request('/sessions', {
		method: 'POST',
		body: JSON.stringify(params)
	});
}

export async function cancelSession(sessionId: string): Promise<void> {
	await request(`/sessions/${sessionId}/cancel`, { method: 'POST' });
}

// --- Session History ---

export async function fetchSessionHistory(params: {
	workspace_id?: string;
	tenant_id?: string;
	status?: string;
	search?: string;
	limit?: number;
	offset?: number;
}): Promise<{ sessions: SessionHistoryItem[]; total: number; limit: number; offset: number }> {
	const qs = new URLSearchParams();
	if (params.workspace_id) qs.set('workspace_id', params.workspace_id);
	if (params.tenant_id) qs.set('tenant_id', params.tenant_id);
	if (params.status) qs.set('status', params.status);
	if (params.search) qs.set('search', params.search);
	if (params.limit != null) qs.set('limit', String(params.limit));
	if (params.offset != null) qs.set('offset', String(params.offset));
	const query = qs.toString();
	return request(`/sessions/history${query ? `?${query}` : ''}`);
}

export async function fetchSessionEvents(
	sessionId: string
): Promise<{ session: Session; events: SessionEvent[] }> {
	return request(`/sessions/${sessionId}/events`);
}

// --- Config ---

export async function fetchClaudeMd(
	workspaceId: string
): Promise<{ content: string | null; exists: boolean }> {
	return request(`/config/${workspaceId}/claude-md`);
}

export async function fetchRules(
	workspaceId: string
): Promise<{ rules: RuleFile[] }> {
	return request(`/config/${workspaceId}/rules`);
}

export async function fetchSettings(
	workspaceId: string
): Promise<{ content: Record<string, unknown> | null; exists: boolean }> {
	return request(`/config/${workspaceId}/settings`);
}

// --- Analytics ---

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
	return request('/analytics/summary');
}

export async function fetchCostByWorkspace(): Promise<CostByWorkspace[]> {
	return request('/analytics/cost-by-workspace');
}

export async function fetchCostTrend(days: number = 30): Promise<CostTrendPoint[]> {
	return request(`/analytics/cost-trend?days=${days}`);
}

export async function fetchTopSkills(limit: number = 10): Promise<TopSkillItem[]> {
	return request(`/analytics/top-skills?limit=${limit}`);
}

export async function fetchTokenEfficiency(): Promise<TokenEfficiency> {
	return request('/analytics/token-efficiency');
}

// --- GitHub ---

export async function fetchMilestones(
	workspaceId: string,
	state: string = 'open'
): Promise<{ milestones: GitHubMilestone[] }> {
	return request(`/github/milestones?workspace_id=${workspaceId}&state=${state}`);
}

export async function fetchMilestoneIssues(
	workspaceId: string,
	number: number
): Promise<{ issues: GitHubIssue[] }> {
	return request(`/github/milestones/${number}/issues?workspace_id=${workspaceId}`);
}

export async function fetchGitHubIssues(
	workspaceId: string,
	state: string = 'open'
): Promise<{ issues: GitHubIssue[] }> {
	return request(`/github/issues?workspace_id=${workspaceId}&state=${state}`);
}

export async function fetchGitHubIssue(
	workspaceId: string,
	number: number
): Promise<GitHubIssue> {
	const data = await request<{ issue: GitHubIssue }>(
		`/github/issues/${number}?workspace_id=${workspaceId}`
	);
	return data.issue;
}

export async function fetchGitHubPRs(
	workspaceId: string,
	state: string = 'open'
): Promise<{ pulls: GitHubPR[] }> {
	return request(`/github/pulls?workspace_id=${workspaceId}&state=${state}`);
}

export async function createGitHubIssue(params: {
	workspace_id: string;
	title: string;
	body?: string;
	labels?: string[];
}): Promise<GitHubIssue> {
	const data = await request<{ issue: GitHubIssue }>('/github/issues', {
		method: 'POST',
		body: JSON.stringify(params)
	});
	return data.issue;
}

// --- Session Diff ---

export async function fetchSessionDiff(
	sessionId: string
): Promise<{ has_diff: boolean; diff: SessionDiff | null }> {
	return request(`/sessions/${sessionId}/diff`);
}

// --- MCP ---

export async function fetchMcps(
	workspaceId: string
): Promise<{ servers: McpServer[] }> {
	return request(`/config/${workspaceId}/mcps`);
}

// --- Workflows ---

export async function fetchWorkflows(
	workspaceId?: string,
	category?: string
): Promise<{ workflows: Workflow[] }> {
	const qs = new URLSearchParams();
	if (workspaceId) qs.set('workspace_id', workspaceId);
	if (category) qs.set('category', category);
	return request(`/workflows?${qs}`);
}

export async function fetchWorkflow(id: string): Promise<{ workflow: Workflow }> {
	return request(`/workflows/${id}`);
}

export async function createWorkflow(params: {
	workspace_id: string;
	name: string;
	prompt_template: string;
	description?: string;
	category?: string;
	icon?: string;
	parameters?: Array<Record<string, unknown>>;
	model?: string;
}): Promise<{ workflow_id: string }> {
	return request('/workflows', {
		method: 'POST',
		body: JSON.stringify(params)
	});
}

export async function updateWorkflow(
	id: string,
	updates: Partial<{
		name: string;
		description: string;
		category: string;
		icon: string;
		prompt_template: string;
		parameters: Array<Record<string, unknown>>;
		model: string;
	}>
): Promise<{ updated: boolean }> {
	return request(`/workflows/${id}`, {
		method: 'PUT',
		body: JSON.stringify(updates)
	});
}

export async function deleteWorkflow(id: string): Promise<{ deleted: boolean }> {
	return request(`/workflows/${id}`, { method: 'DELETE' });
}

export async function launchWorkflow(
	id: string,
	workspaceId: string,
	params: Record<string, string>,
	model?: string
): Promise<{ session_id: string; redirect: string }> {
	return request(`/workflows/${id}/launch`, {
		method: 'POST',
		body: JSON.stringify({ workspace_id: workspaceId, params, model })
	});
}

// --- Monitor ---

export async function fetchMonitorTasks(
	sessionId: string
): Promise<{ tasks: MonitorTask[] }> {
	return request(`/sessions/${sessionId}/monitor`);
}
