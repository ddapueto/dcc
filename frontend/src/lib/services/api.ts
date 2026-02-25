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
	TokenEfficiency
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
