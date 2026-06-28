<script lang="ts">
	import { toast } from '$lib/toast.svelte';
</script>

<div class="toast-host" aria-live="polite" aria-atomic="true">
	{#each toast.items as item (item.id)}
		<div class="toast toast--{item.kind}" role="status">
			<span>{item.message}</span>
			<button type="button" class="toast__dismiss" onclick={() => toast.dismiss(item.id)} aria-label="Dismiss">
				×
			</button>
		</div>
	{/each}
</div>

<style>
	.toast-host {
		position: fixed;
		bottom: 1.25rem;
		right: 1.25rem;
		z-index: 200;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-width: min(22rem, calc(100vw - 2rem));
		pointer-events: none;
	}

	.toast {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--rule);
		background: var(--ink-raised);
		color: var(--chalk);
		font-size: 0.875rem;
		line-height: 1.45;
		box-shadow: var(--shadow-lift);
		pointer-events: auto;
		animation: rise-in var(--duration-normal) var(--ease-out) both;
	}

	.toast--success {
		border-color: color-mix(in srgb, var(--success) 45%, var(--rule));
	}

	.toast--error {
		border-color: color-mix(in srgb, var(--danger) 45%, var(--rule));
	}

	.toast--info {
		border-color: color-mix(in srgb, var(--route) 35%, var(--rule));
	}

	.toast__dismiss {
		flex-shrink: 0;
		width: 1.5rem;
		height: 1.5rem;
		border-radius: var(--radius-sm);
		color: var(--chalk-muted);
		font-size: 1.125rem;
		line-height: 1;
	}

	.toast__dismiss:hover {
		color: var(--chalk);
		background: var(--ink-soft);
	}
</style>
