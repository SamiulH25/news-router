<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function submit(e: Event) {
		e.preventDefault();
		error = '';
		submitting = true;
		try {
			await api.login(username, password);
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Wrong username or password';
		} finally {
			submitting = false;
		}
	}
</script>

<div class="auth-shell">
	<aside class="auth-brand">
		<h1 class="auth-brand__mark">Your household<br />news desk.</h1>
		<p class="auth-brand__tagline">
			Route sources into topics. Open one feed for the whole house. Fetch when you're ready for a
			fresh edition.
		</p>
		<div class="auth-brand__routes">
			sources → topics → today<br />
			···· ···· ···· ····
		</div>
		<div class="auth-ticker" aria-hidden="true">
			<div class="auth-ticker__track">
				<span>Routing wire active</span>
				<span>Edition window 12h</span>
				<span>Digest at 7 & 19</span>
				<span>Household feed</span>
				<span>Routing wire active</span>
				<span>Edition window 12h</span>
				<span>Digest at 7 & 19</span>
				<span>Household feed</span>
			</div>
		</div>
	</aside>

	<div class="auth-panel">
		<div class="auth-form animate-in">
			<p class="eyebrow">Welcome back</p>
			<h1>Sign in</h1>
			<p class="muted">Pick up where you left off</p>
			<form onsubmit={submit}>
				<div>
					<label class="label" for="username">Username</label>
					<input
						id="username"
						class="input"
						bind:value={username}
						autocomplete="username"
						required
					/>
				</div>
				<div>
					<label class="label" for="password">Password</label>
					<input
						id="password"
						class="input"
						type="password"
						bind:value={password}
						autocomplete="current-password"
						required
					/>
				</div>
				{#if error}<p class="error">{error}</p>{/if}
				<button class="btn btn-full" type="submit" disabled={submitting}>
					{submitting ? 'Signing in…' : 'Sign in'}
				</button>
			</form>
			<p class="footer muted">No account? <a href="/register">Create one</a></p>
		</div>
	</div>
</div>
