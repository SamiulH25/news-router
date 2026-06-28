export type ToastKind = 'success' | 'error' | 'info';

export type ToastItem = {
	id: number;
	message: string;
	kind: ToastKind;
};

let nextId = 0;
let items = $state<ToastItem[]>([]);

function dismiss(id: number) {
	items = items.filter((t) => t.id !== id);
}

function push(message: string, kind: ToastKind = 'info', durationMs = 4200) {
	const id = ++nextId;
	items = [...items, { id, message, kind }];
	if (durationMs > 0) {
		setTimeout(() => dismiss(id), durationMs);
	}
}

export const toast = {
	get items() {
		return items;
	},
	dismiss,
	success: (message: string) => push(message, 'success'),
	error: (message: string) => push(message, 'error', 6000),
	info: (message: string) => push(message, 'info')
};
