// Legacy singleton — kept for backward compatibility.
// New code should use tabsStore / TabSession from tabs.svelte.ts.
import { TabSession } from '$stores/tabs.svelte';

export const sessionStore = new TabSession();
