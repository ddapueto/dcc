<script lang="ts">
	import { PanelLeft, Terminal, History, FileCode, Settings, LayoutDashboard, Workflow } from '@lucide/svelte';
	import { page } from '$app/state';
	import type { Snippet } from 'svelte';

	let {
		sidebar,
		topbar,
		content,
		bottombar
	}: {
		sidebar?: Snippet;
		topbar?: Snippet;
		content?: Snippet;
		bottombar?: Snippet;
	} = $props();

	let sidebarOpen = $state(true);

	const navItems = [
		{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
		{ href: '/run', label: 'Run', icon: Terminal },
		{ href: '/history', label: 'History', icon: History },
		{ href: '/workflows', label: 'Workflows', icon: Workflow },
		{ href: '/config', label: 'Config', icon: FileCode },
		{ href: '/manage', label: 'Manage', icon: Settings }
	];
</script>

<div class="flex h-screen overflow-hidden bg-[var(--color-bg-primary)]">
	<!-- Sidebar -->
	{#if sidebarOpen}
		<aside class="glass flex w-64 shrink-0 flex-col border-r border-[var(--color-border)]">
			<div class="flex items-center gap-2 border-b border-[var(--color-border)] px-4 py-3">
				<Terminal class="h-5 w-5 text-[var(--color-accent)]" />
				<span class="text-sm font-semibold text-[var(--color-text-primary)]">DCC</span>
				<span class="text-xs text-[var(--color-text-muted)]">Dev Command Center</span>
			</div>

			<!-- Nav links -->
			<nav class="flex flex-col gap-0.5 border-b border-[var(--color-border)] p-2">
				{#each navItems as item}
					<a
						href={item.href}
						class="flex items-center gap-2 rounded px-3 py-1.5 text-xs transition-colors {page
							.url.pathname === item.href ||
						(item.href !== '/' && page.url.pathname.startsWith(item.href))
							? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
							: 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]'}"
					>
						<item.icon class="h-3.5 w-3.5" />
						{item.label}
					</a>
				{/each}
			</nav>

			<div class="flex-1 overflow-y-auto p-3">
				{#if sidebar}{@render sidebar()}{/if}
			</div>
		</aside>
	{/if}

	<!-- Main -->
	<div class="flex min-w-0 flex-1 flex-col">
		<!-- Top bar -->
		<header class="glass flex items-center gap-3 border-b border-[var(--color-border)] px-4 py-2">
			<button
				onclick={() => (sidebarOpen = !sidebarOpen)}
				class="rounded p-1 text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]"
			>
				<PanelLeft class="h-4 w-4" />
			</button>
			{#if topbar}{@render topbar()}{/if}
		</header>

		<!-- Content -->
		<main class="flex-1 overflow-y-auto">
			{#if content}{@render content()}{/if}
		</main>

		<!-- Bottom bar -->
		<footer
			class="glass flex items-center gap-4 border-t border-[var(--color-border)] px-4 py-2 text-xs"
		>
			{#if bottombar}{@render bottombar()}{/if}
		</footer>
	</div>
</div>
