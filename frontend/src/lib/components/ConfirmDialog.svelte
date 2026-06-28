<script lang="ts">
	import { confirmStore } from '$lib/confirm.svelte';
</script>

{#if confirmStore.state.open}
	<div class="confirm-scrim" role="presentation" onclick={() => confirmStore.answer(false)}></div>
	<div class="confirm-dialog card" role="alertdialog" aria-labelledby="confirm-title" aria-modal="true">
		<h2 id="confirm-title" class="confirm-dialog__title">{confirmStore.state.title}</h2>
		<p class="confirm-dialog__message">{confirmStore.state.message}</p>
		<div class="confirm-dialog__actions">
			<button type="button" class="btn-secondary" onclick={() => confirmStore.answer(false)}>
				{confirmStore.state.cancelLabel}
			</button>
			<button type="button" class="btn" onclick={() => confirmStore.answer(true)}>
				{confirmStore.state.confirmLabel}
			</button>
		</div>
	</div>
{/if}

<style>
	.confirm-scrim {
		position: fixed;
		inset: 0;
		z-index: 150;
		background: var(--scrim);
		animation: fade-in var(--duration-fast) var(--ease-out) both;
	}

	.confirm-dialog {
		position: fixed;
		z-index: 151;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: min(24rem, calc(100vw - 2rem));
		padding: 1.25rem 1.5rem;
		animation: rise-in var(--duration-normal) var(--ease-out) both;
	}

	.confirm-dialog__title {
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 700;
		margin: 0 0 0.5rem;
		color: var(--chalk);
	}

	.confirm-dialog__message {
		margin: 0 0 1.25rem;
		font-size: 0.9375rem;
		line-height: 1.55;
		color: var(--chalk-muted);
	}

	.confirm-dialog__actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
	}

	@keyframes fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
