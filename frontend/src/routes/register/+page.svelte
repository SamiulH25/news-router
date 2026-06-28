<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let submitting = $state(false);
	let registrationOpen = $state(true);

	onMount(async () => {
		try {
			const config = await api.authConfig();
			registrationOpen = config.allow_registration;
		} catch {
			registrationOpen = true;
		}
	});

	async function submit(e: Event) {
		e.preventDefault();
		error = '';
		submitting = true;
		try {
			await api.register(username, password);
			goto('/onboarding');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not create account';
		} finally {
			submitting = false;
		}
	}
</script>

<div class="auth-shell">
	<aside class="auth-brand">
		<h1 class="auth-brand__mark">Your household<br />news desk.</h1>
		<p class="auth-brand__tagline">
			Set up once for the whole household. The first account becomes admin.
		</p>
		<div class="auth-brand__routes">
			sources → topics → today<br />
			···· ···· ···· ····
		</div>
		<div class="auth-ticker" aria-hidden="true">
			<div class="auth-ticker__track">
				<span>New household wire</span>
				<span>Route your sources</span>
				<span>Build your edition</span>
				<span>Digest on schedule</span>
				<span>New household wire</span>
				<span>Route your sources</span>
				<span>Build your edition</span>
				<span>Digest on schedule</span>
			</div>
		</div>
	</aside>

	<div class="auth-panel">
		<div class="auth-form animate-in">
			<p class="eyebrow">Get started</p>
			<h1>Create account</h1>
			<p class="muted">Takes about a minute</p>
			{#if !registrationOpen}
				<p class="error">Registration is disabled on this server.</p>
			{/if}
			<form onsubmit={submit}>
				<div>
					<label class="label" for="username">Username</label>
					<input id="username" class="input" bind:value={username} minlength="3" required />
				</div>
				<div>
					<label class="label" for="password">Password</label>
					<input
						id="password"
						class="input"
						type="password"
						bind:value={password}
						minlength="6"
						required
					/>
				</div>
				{#if error}<p class="error">{error}</p>{/if}
				<button class="btn btn-full" type="submit" disabled={submitting || !registrationOpen}>
					{submitting ? 'Creating…' : 'Create account'}
				</button>
			</form>
			<p class="footer muted">Already have an account? <a href="/login">Sign in</a></p>
		</div>
	</div>
</div>
