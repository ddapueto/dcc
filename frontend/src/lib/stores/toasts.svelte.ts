export interface Toast {
	id: number;
	message: string;
	type: 'success' | 'error' | 'info';
	exiting: boolean;
}

let _nextId = 1;

class ToastStore {
	toasts = $state<Toast[]>([]);

	add(message: string, type: Toast['type'] = 'info') {
		const id = _nextId++;
		this.toasts = [...this.toasts, { id, message, type, exiting: false }];

		setTimeout(() => this.dismiss(id), 4000);
	}

	dismiss(id: number) {
		// Trigger exit animation
		this.toasts = this.toasts.map((t) => (t.id === id ? { ...t, exiting: true } : t));

		// Remove after animation
		setTimeout(() => {
			this.toasts = this.toasts.filter((t) => t.id !== id);
		}, 300);
	}
}

export const toastStore = new ToastStore();
