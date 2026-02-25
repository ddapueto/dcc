import { tabsStore } from '$stores/tabs.svelte';

export function initGlobalShortcuts(): () => void {
	function handler(e: KeyboardEvent) {
		const meta = e.metaKey || e.ctrlKey;

		// Escape: cancel active session
		if (e.key === 'Escape') {
			const session = tabsStore.activeSession;
			if (session?.status === 'running') {
				e.preventDefault();
				session.cancel();
			}
			return;
		}

		// Cmd+K: new tab
		if (meta && e.key === 'k') {
			e.preventDefault();
			tabsStore.addTab();
			return;
		}

		// Cmd+W: close active tab
		if (meta && e.key === 'w') {
			e.preventDefault();
			if (tabsStore.activeTabId) {
				tabsStore.closeTab(tabsStore.activeTabId);
			}
			return;
		}

		// Cmd+1–9: switch to tab by index
		if (meta && e.key >= '1' && e.key <= '9') {
			e.preventDefault();
			const idx = parseInt(e.key) - 1;
			if (idx < tabsStore.tabs.length) {
				tabsStore.switchTab(tabsStore.tabs[idx].id);
			}
		}
	}

	window.addEventListener('keydown', handler);
	return () => window.removeEventListener('keydown', handler);
}
