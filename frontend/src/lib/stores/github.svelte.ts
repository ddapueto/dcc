import {
	fetchMilestones,
	fetchGitHubIssues,
	fetchGitHubPRs,
	fetchMilestoneIssues
} from '$services/api';
import type { GitHubMilestone, GitHubIssue, GitHubPR } from '$types/index';

class GitHubStore {
	milestones = $state<GitHubMilestone[]>([]);
	issues = $state<GitHubIssue[]>([]);
	pulls = $state<GitHubPR[]>([]);

	selectedMilestone = $state<number | null>(null);
	milestoneIssues = $state<GitHubIssue[]>([]);

	hasRepo = $state(false);
	loading = $state(false);
	error = $state<string | null>(null);

	async loadForWorkspace(workspaceId: string) {
		this.loading = true;
		this.error = null;
		this.hasRepo = true;
		try {
			const [ms, is, pr] = await Promise.all([
				fetchMilestones(workspaceId),
				fetchGitHubIssues(workspaceId),
				fetchGitHubPRs(workspaceId)
			]);
			this.milestones = ms.milestones;
			this.issues = is.issues;
			this.pulls = pr.pulls;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load GitHub data';
			// If 400 = no repo configured, mark accordingly
			if (this.error.includes('400')) {
				this.hasRepo = false;
			}
		} finally {
			this.loading = false;
		}
	}

	async selectMilestone(workspaceId: string, number: number) {
		this.selectedMilestone = number;
		try {
			const data = await fetchMilestoneIssues(workspaceId, number);
			this.milestoneIssues = data.issues;
		} catch {
			this.milestoneIssues = [];
		}
	}

	reset() {
		this.milestones = [];
		this.issues = [];
		this.pulls = [];
		this.selectedMilestone = null;
		this.milestoneIssues = [];
		this.hasRepo = false;
		this.loading = false;
		this.error = null;
	}
}

export const githubStore = new GitHubStore();
