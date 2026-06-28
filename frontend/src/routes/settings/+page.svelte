<script lang="ts">
	import { api, type User } from '$lib/api';
	import { defaultTimezone, ensureTimezone, listTimezones } from '$lib/timezones';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let user = $state<User | null>(null);
	let currentPassword = $state('');
	let newPassword = $state('');
	let message = $state('');
	let error = $state('');
	let saving = $state(false);

	const timezones = listTimezones();

	onMount(async () => {
		user = await api.me();
		if (user) {
			user.timezone = ensureTimezone(user.timezone, timezones);
		}
	});

	async function saveSchedule() {
		if (!user) return;
		saving = true;
		error = '';
		message = '';
		try {
			user = await api.updateSettings({
				digest_hour: user.digest_hour,
				digest_minute: user.digest_minute,
				digest_evening_hour: user.digest_evening_hour,
				digest_evening_minute: user.digest_evening_minute,
				timezone: user.timezone,
				feed_window_hours: user.feed_window_hours
			});
			message = 'Schedule saved';
			toast.success('Schedule saved');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not save';
		} finally {
			saving = false;
		}
	}

	async function regenerateNtfy() {
		try {
			user = await api.updateSettings({ regenerate_ntfy_topic: true });
			message = 'Push topic changed — subscribe again in the ntfy app';
			toast.success('New push topic created');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not regenerate topic';
			toast.error(error);
		}
	}

	async function testNotify() {
		try {
			const result = await api.testNotify();
			message = result.sent ? 'Test notification sent' : 'Nothing unread to notify about';
			toast.info(message);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Notification failed';
			toast.error(error);
		}
	}

	async function changePassword(e: Event) {
		e.preventDefault();
		error = '';
		message = '';
		saving = true;
		try {
			await api.changePassword(currentPassword, newPassword);
			currentPassword = '';
			newPassword = '';
			message = 'Password updated';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not update password';
		} finally {
			saving = false;
		}
	}
</script>

<div class="container container--wide">
	<header class="page-header wire-edge">
		<div>
			<p class="eyebrow">Preferences</p>
			<h1 class="display-title">Settings</h1>
			<p class="lead">Digest schedule, feed window, and account security</p>
		</div>
		{#if user?.is_admin}
			<div class="page-header__actions">
				<a href="/settings/admin" class="btn-secondary">Admin</a>
			</div>
		{/if}
	</header>

	{#if user}
		<section class="card settings-section stagger-in" style="--i: 0">
			<h2>For you feed</h2>
			<p class="muted">
				When enabled, story order adapts from choices you make — opening a story boosts similar
				topics; “Less like this” tones them down. Scrolling alone never trains the feed.
			</p>
			<label class="toggle-row">
				<input
					type="checkbox"
					checked={user.personalized_feed}
					onchange={async (e) => {
						const checked = (e.currentTarget as HTMLInputElement).checked;
						try {
							user = await api.updateSettings({ personalized_feed: checked });
							message = checked ? 'Personalized feed on' : 'Showing chronological feed';
							toast.success(message);
						} catch (err) {
							(e.currentTarget as HTMLInputElement).checked = !checked;
							toast.error(err instanceof Error ? err.message : 'Could not update');
						}
					}}
				/>
				<span>Personalize my feed</span>
			</label>
		</section>

		<section class="card settings-section stagger-in" style="--i: 1">
			<h2>Edition schedule</h2>
			<p class="muted">
				Digests use your timezone. Stories in each edition come from the last N hours.
			</p>
			<div class="grid-2">
				<div>
					<label class="label" for="tz">Timezone</label>
					<select id="tz" class="input" bind:value={user.timezone}>
						{#each timezones as tz}
							<option value={tz}>{tz}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="label" for="window">Feed window (hours)</label>
					<input
						id="window"
						class="input"
						type="number"
						min="1"
						max="72"
						bind:value={user.feed_window_hours}
					/>
				</div>
			</div>
			<div class="grid-2" style="margin-top: 0.75rem">
				<div>
					<label class="label">Morning digest</label>
					<div class="time-row">
						<input class="input" type="number" min="0" max="23" bind:value={user.digest_hour} />
						<span>:</span>
						<input
							class="input"
							type="number"
							min="0"
							max="59"
							bind:value={user.digest_minute}
						/>
					</div>
				</div>
				<div>
					<label class="label">Evening digest</label>
					<div class="time-row">
						<input
							class="input"
							type="number"
							min="0"
							max="23"
							bind:value={user.digest_evening_hour}
						/>
						<span>:</span>
						<input
							class="input"
							type="number"
							min="0"
							max="59"
							bind:value={user.digest_evening_minute}
						/>
					</div>
				</div>
			</div>
			<div class="settings-actions">
				<button class="btn" onclick={saveSchedule} disabled={saving}>
					{saving ? 'Saving…' : 'Save schedule'}
				</button>
			</div>
		</section>
	{/if}

	<section class="card settings-section stagger-in" style="--i: 2">
		<h2>Digest push</h2>
		<p class="muted">
			Subscribe to your private topic in the ntfy app. On your home network, server URL is
			<code>http://&lt;server-ip&gt;:2586</code>
		</p>
		{#if user?.ntfy_topic}
			<div class="topic-box">
				<span class="muted small">Your topic</span><br />
				<code>{user.ntfy_topic}</code>
			</div>
		{/if}
		<div class="settings-actions">
			<button class="btn-secondary" onclick={testNotify}>Send test</button>
			<button class="btn-secondary" onclick={regenerateNtfy}>New push topic</button>
		</div>
	</section>

	<section class="card settings-section stagger-in" style="--i: 3">
		<h2>Password</h2>
		<form onsubmit={changePassword}>
			<label class="label" for="current">Current password</label>
			<input id="current" class="input" type="password" bind:value={currentPassword} required />
			<label class="label" for="new">New password</label>
			<input id="new" class="input" type="password" bind:value={newPassword} minlength="6" required />
			<div class="settings-actions">
				<button class="btn" type="submit" disabled={saving}>
					{saving ? 'Updating…' : 'Update password'}
				</button>
			</div>
		</form>
	</section>

	{#if message}<p class="success">{message}</p>{/if}
	{#if error}<p class="error">{error}</p>{/if}
</div>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 0.875rem;
	}

	.grid-2 {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.time-row {
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.time-row .input {
		width: 4rem;
	}

	@media (max-width: 540px) {
		.grid-2 {
			grid-template-columns: 1fr;
		}
	}
</style>
