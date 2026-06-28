export type ConfirmOptions = {
	title: string;
	message: string;
	confirmLabel?: string;
	cancelLabel?: string;
};

type ConfirmState = ConfirmOptions & {
	open: boolean;
	resolve: ((ok: boolean) => void) | null;
};

let state = $state<ConfirmState>({
	open: false,
	title: '',
	message: '',
	confirmLabel: 'Confirm',
	cancelLabel: 'Cancel',
	resolve: null
});

export const confirmStore = {
	get state() {
		return state;
	},
	confirm(options: ConfirmOptions): Promise<boolean> {
		return new Promise((resolve) => {
			state = {
				open: true,
				title: options.title,
				message: options.message,
				confirmLabel: options.confirmLabel ?? 'Confirm',
				cancelLabel: options.cancelLabel ?? 'Cancel',
				resolve
			};
		});
	},
	answer(ok: boolean) {
		state.resolve?.(ok);
		state = { ...state, open: false, resolve: null };
	}
};
