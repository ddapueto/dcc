<script lang="ts">
	import { onMount } from 'svelte';
	import Shell from '$lib/components/Shell.svelte';
	import { workspacesStore } from '$stores/workspaces.svelte';
	import {
		createTenant,
		deleteTenant,
		createWorkspace,
		deleteWorkspace,
		scanWorkspaces
	} from '$services/api';
	import { Trash2, Plus, RefreshCw, FolderGit2, Users } from '@lucide/svelte';

	// Tenant form
	let tenantName = $state('');
	let tenantConfigDir = $state('');
	let tenantAlias = $state('');

	// Workspace form
	let wsName = $state('');
	let wsPath = $state('');
	let wsTenantId = $state('');

	let busy = $state(false);

	onMount(() => {
		workspacesStore.fetch();
	});

	async function handleCreateTenant() {
		if (!tenantName || !tenantConfigDir || !tenantAlias) return;
		busy = true;
		try {
			await createTenant({
				name: tenantName,
				config_dir: tenantConfigDir,
				claude_alias: tenantAlias
			});
			tenantName = '';
			tenantConfigDir = '';
			tenantAlias = '';
			await workspacesStore.fetch();
		} finally {
			busy = false;
		}
	}

	async function handleDeleteTenant(id: string) {
		busy = true;
		try {
			await deleteTenant(id);
			await workspacesStore.fetch();
		} finally {
			busy = false;
		}
	}

	async function handleCreateWorkspace() {
		if (!wsName || !wsPath || !wsTenantId) return;
		busy = true;
		try {
			await createWorkspace({ tenant_id: wsTenantId, name: wsName, path: wsPath });
			wsName = '';
			wsPath = '';
			wsTenantId = '';
			await workspacesStore.fetch();
		} finally {
			busy = false;
		}
	}

	async function handleDeleteWorkspace(id: string) {
		busy = true;
		try {
			await deleteWorkspace(id);
			await workspacesStore.fetch();
		} finally {
			busy = false;
		}
	}

	async function handleScan() {
		busy = true;
		try {
			await scanWorkspaces();
			await workspacesStore.fetch();
		} finally {
			busy = false;
		}
	}
</script>

<Shell>
	{#snippet topbar()}
		<span class="text-sm font-medium text-[var(--color-text-primary)]">Manage Workspaces & Tenants</span>
	{/snippet}

	{#snippet content()}
		<div class="flex h-full flex-col gap-6 overflow-y-auto p-6">
			<!-- Tenants Section -->
			<section>
				<div class="mb-3 flex items-center gap-2">
					<Users class="h-4 w-4 text-[var(--color-accent)]" />
					<h2 class="text-sm font-semibold text-[var(--color-text-primary)]">Tenants</h2>
				</div>

				<!-- Existing tenants -->
				<div class="mb-3 flex flex-col gap-2">
					{#each workspacesStore.tenants as tenant (tenant.id)}
						<div class="glass flex items-center justify-between rounded-lg px-4 py-2.5">
							<div class="flex items-center gap-3">
								<span class="text-sm font-medium text-[var(--color-text-primary)]">{tenant.name}</span>
								<span class="rounded bg-[var(--color-bg-input)] px-2 py-0.5 text-[10px] text-[var(--color-text-muted)]">
									{tenant.claude_alias}
								</span>
								<span class="text-xs text-[var(--color-text-muted)]">{tenant.config_dir}</span>
							</div>
							<button
								onclick={() => handleDeleteTenant(tenant.id)}
								disabled={busy}
								class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-error)]/10 hover:text-[var(--color-error)] disabled:opacity-30"
							>
								<Trash2 class="h-3.5 w-3.5" />
							</button>
						</div>
					{/each}
				</div>

				<!-- New tenant form -->
				<div class="glass flex items-end gap-2 rounded-lg p-3">
					<label class="flex-1">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Name</span>
						<input
							bind:value={tenantName}
							placeholder="personal"
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						/>
					</label>
					<label class="flex-1">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Config Dir</span>
						<input
							bind:value={tenantConfigDir}
							placeholder="~/.claude-personal"
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						/>
					</label>
					<label class="flex-1">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Claude Alias</span>
						<input
							bind:value={tenantAlias}
							placeholder="claude-personal"
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						/>
					</label>
					<button
						onclick={handleCreateTenant}
						disabled={busy || !tenantName || !tenantConfigDir || !tenantAlias}
						class="flex items-center gap-1 rounded-lg bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-[var(--color-bg-primary)] hover:bg-[var(--color-accent-light)] disabled:opacity-30"
					>
						<Plus class="h-3.5 w-3.5" /> Add
					</button>
				</div>
			</section>

			<!-- Workspaces Section -->
			<section>
				<div class="mb-3 flex items-center gap-2">
					<FolderGit2 class="h-4 w-4 text-[var(--color-accent)]" />
					<h2 class="text-sm font-semibold text-[var(--color-text-primary)]">Workspaces</h2>
					<button
						onclick={handleScan}
						disabled={busy}
						class="ml-auto flex items-center gap-1 rounded px-2 py-1 text-[10px] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-secondary)] disabled:opacity-30"
					>
						<RefreshCw class="h-3 w-3" /> Re-scan all
					</button>
				</div>

				<!-- Workspaces grouped by tenant -->
				{#each workspacesStore.workspacesByTenant as group (group.tenant.id)}
					<div class="mb-4">
						<h3 class="mb-2 text-xs font-medium text-[var(--color-text-muted)]">{group.tenant.name}</h3>
						<div class="flex flex-col gap-1.5">
							{#each group.workspaces as ws (ws.id)}
								<div class="glass flex items-center justify-between rounded-lg px-4 py-2">
									<div class="flex items-center gap-3">
										<span class="text-sm text-[var(--color-text-primary)]">{ws.name}</span>
										<span class="text-xs text-[var(--color-text-muted)]">{ws.path}</span>
										<span class="text-[10px] text-[var(--color-text-muted)]">
											{ws.agents_count}a · {ws.skills_count}s
										</span>
									</div>
									<button
										onclick={() => handleDeleteWorkspace(ws.id)}
										disabled={busy}
										class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-error)]/10 hover:text-[var(--color-error)] disabled:opacity-30"
									>
										<Trash2 class="h-3.5 w-3.5" />
									</button>
								</div>
							{/each}
						</div>
					</div>
				{/each}

				<!-- New workspace form -->
				<div class="glass flex items-end gap-2 rounded-lg p-3">
					<label class="w-40">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Tenant</span>
						<select
							bind:value={wsTenantId}
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						>
							<option value="">Select...</option>
							{#each workspacesStore.tenants as t}
								<option value={t.id}>{t.name}</option>
							{/each}
						</select>
					</label>
					<label class="flex-1">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Name</span>
						<input
							bind:value={wsName}
							placeholder="my-project"
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						/>
					</label>
					<label class="flex-1">
						<span class="mb-1 block text-[10px] text-[var(--color-text-muted)]">Path</span>
						<input
							bind:value={wsPath}
							placeholder="/home/user/projects/my-project"
							class="w-full rounded bg-[var(--color-bg-input)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
						/>
					</label>
					<button
						onclick={handleCreateWorkspace}
						disabled={busy || !wsName || !wsPath || !wsTenantId}
						class="flex items-center gap-1 rounded-lg bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-[var(--color-bg-primary)] hover:bg-[var(--color-accent-light)] disabled:opacity-30"
					>
						<Plus class="h-3.5 w-3.5" /> Add
					</button>
				</div>
			</section>
		</div>
	{/snippet}
</Shell>
