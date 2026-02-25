import type { SessionHistoryItem } from '$types/index';
import { fetchSessionHistory } from '$services/api';

class HistoryStore {
	sessions = $state<SessionHistoryItem[]>([]);
	total = $state(0);
	loading = $state(false);
	error = $state<string | null>(null);

	// Filtros
	workspaceId = $state<string | null>(null);
	tenantId = $state<string | null>(null);
	statusFilter = $state<string | null>(null);
	search = $state('');
	page = $state(0);
	pageSize = 25;

	totalPages = $derived(Math.max(1, Math.ceil(this.total / this.pageSize)));

	async fetch() {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchSessionHistory({
				workspace_id: this.workspaceId ?? undefined,
				tenant_id: this.tenantId ?? undefined,
				status: this.statusFilter ?? undefined,
				search: this.search || undefined,
				limit: this.pageSize,
				offset: this.page * this.pageSize
			});
			this.sessions = data.sessions;
			this.total = data.total;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to fetch history';
		} finally {
			this.loading = false;
		}
	}

	setFilters(filters: {
		workspaceId?: string | null;
		tenantId?: string | null;
		statusFilter?: string | null;
		search?: string;
	}) {
		if (filters.workspaceId !== undefined) this.workspaceId = filters.workspaceId;
		if (filters.tenantId !== undefined) this.tenantId = filters.tenantId;
		if (filters.statusFilter !== undefined) this.statusFilter = filters.statusFilter;
		if (filters.search !== undefined) this.search = filters.search;
		this.page = 0;
		this.fetch();
	}

	nextPage() {
		if (this.page < this.totalPages - 1) {
			this.page++;
			this.fetch();
		}
	}

	prevPage() {
		if (this.page > 0) {
			this.page--;
			this.fetch();
		}
	}
}

export const historyStore = new HistoryStore();
