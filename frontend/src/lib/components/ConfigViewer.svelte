<script lang="ts">
	import { ChevronDown, ChevronRight } from '@lucide/svelte';
	import { fetchClaudeMd, fetchRules, fetchSettings, fetchMcps } from '$services/api';
	import type { RuleFile, McpServer } from '$types/index';

	let { workspaceId }: { workspaceId: string } = $props();

	let tab = $state<'claude-md' | 'rules' | 'settings' | 'mcps'>('claude-md');
	let loading = $state(false);

	// claude-md
	let claudeMdContent = $state<string | null>(null);
	let claudeMdExists = $state(false);

	// rules
	let rules = $state<RuleFile[]>([]);
	let expandedRule = $state<string | null>(null);

	// settings
	let settingsContent = $state<Record<string, unknown> | null>(null);
	let settingsExists = $state(false);

	// mcps
	let mcps = $state<McpServer[]>([]);

	$effect(() => {
		loadTab(workspaceId, tab);
	});

	async function loadTab(wsId: string, currentTab: string) {
		loading = true;
		try {
			if (currentTab === 'claude-md') {
				const data = await fetchClaudeMd(wsId);
				claudeMdContent = data.content;
				claudeMdExists = data.exists;
			} else if (currentTab === 'rules') {
				const data = await fetchRules(wsId);
				rules = data.rules;
			} else if (currentTab === 'settings') {
				const data = await fetchSettings(wsId);
				settingsContent = data.content;
				settingsExists = data.exists;
			} else if (currentTab === 'mcps') {
				const data = await fetchMcps(wsId);
				mcps = data.servers;
			}
		} catch {
			// silenciar — UI muestra estado vacío
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex h-full flex-col">
	<!-- Tab switcher -->
	<div class="flex gap-1 rounded-lg bg-[var(--color-bg-input)] p-0.5">
		<button
			class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors
			{tab === 'claude-md'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'claude-md')}
		>
			CLAUDE.md
		</button>
		<button
			class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors
			{tab === 'rules'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'rules')}
		>
			Rules ({rules.length})
		</button>
		<button
			class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors
			{tab === 'settings'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'settings')}
		>
			Settings
		</button>
		<button
			class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors
			{tab === 'mcps'
				? 'bg-[var(--color-bg-card)] text-[var(--color-accent)]'
				: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'}"
			onclick={() => (tab = 'mcps')}
		>
			MCPs ({mcps.length})
		</button>
	</div>

	<!-- Content -->
	<div class="mt-3 flex-1 overflow-y-auto">
		{#if loading}
			<div class="flex items-center justify-center py-8">
				<span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
			</div>
		{:else if tab === 'claude-md'}
			{#if claudeMdExists && claudeMdContent}
				<pre class="glass rounded-lg p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-[var(--color-text-primary)]">{claudeMdContent}</pre>
			{:else}
				<div class="py-8 text-center text-sm text-[var(--color-text-muted)]">
					No CLAUDE.md found
				</div>
			{/if}
		{:else if tab === 'rules'}
			{#if rules.length > 0}
				<div class="flex flex-col gap-2">
					{#each rules as rule (rule.filename)}
						<div class="glass rounded-lg">
							<button
								class="flex w-full items-center gap-2 px-4 py-2.5 text-left"
								onclick={() => (expandedRule = expandedRule === rule.filename ? null : rule.filename)}
							>
								{#if expandedRule === rule.filename}
									<ChevronDown class="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
								{:else}
									<ChevronRight class="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
								{/if}
								<span class="text-xs font-medium text-[var(--color-text-primary)]">
									{rule.filename}
								</span>
							</button>
							{#if expandedRule === rule.filename}
								<div class="border-t border-[var(--color-border)] px-4 py-3">
									<pre class="font-mono text-xs leading-relaxed whitespace-pre-wrap text-[var(--color-text-secondary)]">{rule.content}</pre>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<div class="py-8 text-center text-sm text-[var(--color-text-muted)]">
					No rules found in .claude/rules/
				</div>
			{/if}
		{:else if tab === 'settings'}
			{#if settingsExists && settingsContent}
				<pre class="glass rounded-lg p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-[var(--color-text-primary)]">{JSON.stringify(settingsContent, null, 2)}</pre>
			{:else}
				<div class="py-8 text-center text-sm text-[var(--color-text-muted)]">
					No settings.json found
				</div>
			{/if}
		{:else if tab === 'mcps'}
			{#if mcps.length > 0}
				<div class="flex flex-col gap-2">
					{#each mcps as server (server.name)}
						<div class="glass rounded-lg px-4 py-3">
							<div class="flex items-center gap-2">
								<span class="text-xs font-medium text-[var(--color-text-primary)]">{server.name}</span>
								<span class="rounded-full px-1.5 py-0.5 text-[9px] font-medium {server.source === 'workspace'
									? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
									: 'bg-[var(--color-info)]/10 text-[var(--color-info)]'}">
									{server.source}
								</span>
							</div>
							<div class="mt-1 font-mono text-[11px] text-[var(--color-text-muted)]">
								{server.command} {server.args.join(' ')}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="py-8 text-center text-sm text-[var(--color-text-muted)]">
					No MCP servers configured
				</div>
			{/if}
		{/if}
	</div>
</div>
