import type { Tenant, Workspace, WorkspaceDetail } from '$types/index';
import { fetchWorkspaces, fetchWorkspaceDetail, scanWorkspaces } from '$services/api';

class WorkspacesStore {
	tenants = $state<Tenant[]>([]);
	workspaces = $state<Workspace[]>([]);
	currentWorkspaceId = $state<string | null>(null);
	detail = $state<WorkspaceDetail | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	currentWorkspace = $derived(
		this.workspaces.find((w) => w.id === this.currentWorkspaceId) ?? null
	);

	workspacesByTenant = $derived(
		this.tenants.map((t) => ({
			tenant: t,
			workspaces: this.workspaces.filter((w) => w.tenant_id === t.id)
		}))
	);

	async fetch() {
		this.loading = true;
		this.error = null;
		try {
			const data = await fetchWorkspaces();
			this.tenants = data.tenants;
			this.workspaces = data.workspaces;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to fetch workspaces';
		} finally {
			this.loading = false;
		}
	}

	async switchWorkspace(id: string) {
		this.currentWorkspaceId = id;
		this.detail = null;
		try {
			this.detail = await fetchWorkspaceDetail(id);
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load workspace detail';
		}
	}

	async scan() {
		this.loading = true;
		try {
			await scanWorkspaces();
			await this.fetch();
			// Refresh detail if a workspace is selected
			if (this.currentWorkspaceId) {
				this.detail = await fetchWorkspaceDetail(this.currentWorkspaceId);
			}
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to scan workspaces';
		} finally {
			this.loading = false;
		}
	}
}

export const workspacesStore = new WorkspacesStore();
