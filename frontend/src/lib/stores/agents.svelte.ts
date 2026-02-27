import type { RegisteredAgent, AgentUsageStats, AgentDelegation, CostTrendPoint } from '$types/index';
import {
	fetchWorkspaceAgents,
	fetchAgentStats,
	fetchAgentDelegations,
	fetchAgentCostTrend
} from '$services/api';

class AgentsStore {
	agents = $state<RegisteredAgent[]>([]);
	stats = $state<AgentUsageStats[]>([]);
	delegations = $state<AgentDelegation[]>([]);
	selectedAgentName = $state<string | null>(null);
	selectedAgentTrend = $state<CostTrendPoint[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	activeAgents = $derived(this.agents.filter((a) => a.is_active));
	uniqueModels = $derived([...new Set(this.activeAgents.map((a) => a.model).filter(Boolean))]);

	selectedAgent = $derived(
		this.selectedAgentName
			? this.agents.find((a) => a.name === this.selectedAgentName) ?? null
			: null
	);

	selectedAgentStats = $derived(
		this.selectedAgentName
			? this.stats.find((s) => s.name === this.selectedAgentName) ?? null
			: null
	);

	totalAgentCost = $derived(this.stats.reduce((sum, s) => sum + s.total_cost, 0));
	totalAgentSessions = $derived(this.stats.reduce((sum, s) => sum + s.sessions, 0));

	async loadForWorkspace(workspaceId: string) {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchWorkspaceAgents(workspaceId);
			this.agents = data.agents;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load agents';
		} finally {
			this.loading = false;
		}
	}

	async loadStats(workspaceId?: string) {
		try {
			const [statsData, delegationsData] = await Promise.all([
				fetchAgentStats(workspaceId),
				fetchAgentDelegations()
			]);
			this.stats = statsData.stats;
			this.delegations = delegationsData.delegations;
		} catch {
			// Stats not critical
		}
	}

	async selectAgent(name: string) {
		this.selectedAgentName = name;
		try {
			const data = await fetchAgentCostTrend(name);
			this.selectedAgentTrend = data.trend;
		} catch {
			this.selectedAgentTrend = [];
		}
	}

	reset() {
		this.agents = [];
		this.stats = [];
		this.delegations = [];
		this.selectedAgentName = null;
		this.selectedAgentTrend = [];
		this.loading = false;
		this.error = null;
	}
}

export const agentsStore = new AgentsStore();
