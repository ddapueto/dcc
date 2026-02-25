import type {
	AnalyticsSummary,
	CostByWorkspace,
	CostTrendPoint,
	TopSkillItem,
	TokenEfficiency
} from '$types/index';
import {
	fetchAnalyticsSummary,
	fetchCostByWorkspace,
	fetchCostTrend,
	fetchTopSkills,
	fetchTokenEfficiency
} from '$services/api';

class AnalyticsStore {
	summary = $state<AnalyticsSummary | null>(null);
	costByWorkspace = $state<CostByWorkspace[]>([]);
	costTrend = $state<CostTrendPoint[]>([]);
	topSkills = $state<TopSkillItem[]>([]);
	tokenEfficiency = $state<TokenEfficiency | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	async fetchAll() {
		this.loading = true;
		this.error = null;
		try {
			const [summary, costByWorkspace, costTrend, topSkills, tokenEfficiency] =
				await Promise.all([
					fetchAnalyticsSummary(),
					fetchCostByWorkspace(),
					fetchCostTrend(30),
					fetchTopSkills(10),
					fetchTokenEfficiency()
				]);
			this.summary = summary;
			this.costByWorkspace = costByWorkspace;
			this.costTrend = costTrend;
			this.topSkills = topSkills;
			this.tokenEfficiency = tokenEfficiency;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load analytics';
		} finally {
			this.loading = false;
		}
	}
}

export const analyticsStore = new AnalyticsStore();
