<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, type DailyFeed, type PollResponse, type User } from '$lib/api';
	import PollReport from '$lib/components/PollReport.svelte';
	import { flattenFeed } from '$lib/feedUtils';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let user = $state<User | null>(null);
	let feed = $state<DailyFeed | null>(null);
	let loading = $state(true);
	let polling = $state(false);
	let error = $state('');
	let pollReport = $state<PollResponse | null>(null);

	const todayLabel = new Intl.DateTimeFormat(undefined, {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	}).format(new Date());

	const storyCount = $derived(feed ? flattenFeed(feed).length : 0);
	const channelCount = $derived(feed?.groups.length ?? 0);
	const unreadCount = $derived(feed?.total_unread ?? 0);

	const fetchedLabel = $derived.by(() => {
		if (!feed?.edition_fetched_at) return null;
		return new Date(feed.edition_fetched_at).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	});

	const digestLabel = $derived.by(() => {
		if (!user) return '';
		const fmt = (h: number, m: number) =>
			`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
		return `${fmt(user.digest_hour, user.digest_minute)} & ${fmt(user.digest_evening_hour, user.digest_evening_minute)}`;
	});

	async function load() {
		loading = true;
		error = '';
		try {
			const [me, daily] = await Promise.all([api.me(), api.getDailyFeed()]);
			user = me;
			feed = daily;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load your edition';
		} finally {
			loading = false;
		}
	}

	async function pollNow() {
		polling = true;
		error = '';
		try {
			pollReport = await api.triggerPoll();
			feed = await api.getDailyFeed();
			toast.success(`Pulled ${pollReport.new_articles} new stories`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Pull failed';
			toast.error(error);
		} finally {
			polling = false;
		}
	}

	async function logout() {
		await api.logout();
		goto('/login');
	}

	onMount(load);
</script>

<div class="container container--wide dashboard">
	<div class="dashboard__layout">
		<aside class="dashboard__account card stagger-in" style="--i: 0" aria-label="Your account">
			{#if user}
				<div class="dashboard__account-head">
					<div class="dashboard__avatar" aria-hidden="true">
						{user.username.slice(0, 1).toUpperCase()}
					</div>
					<div class="dashboard__account-id">
						<p class="dashboard__account-eyebrow">Signed in as</p>
						<h2 class="dashboard__account-name">{user.username}</h2>
						{#if user.is_admin}
							<span class="dashboard__badge">Admin</span>
						{/if}
					</div>
				</div>

				<dl class="dashboard__account-meta">
					<div class="dashboard__meta-row">
						<dt>Timezone</dt>
						<dd>{user.timezone}</dd>
					</div>
					<div class="dashboard__meta-row">
						<dt>Daily digests</dt>
						<dd>{digestLabel}</dd>
					</div>
					<div class="dashboard__meta-row">
						<dt>Edition window</dt>
						<dd>Last {user.feed_window_hours} hours</dd>
					</div>
					<div class="dashboard__meta-row">
						<dt>For you feed</dt>
						<dd>{user.personalized_feed ? 'Personalized' : 'Chronological'}</dd>
					</div>
				</dl>

				<nav class="dashboard__manage" aria-label="Manage household">
					<p class="dashboard__manage-label">Manage</p>
					<div class="dashboard__manage-links">
						<a href="/settings" class="dashboard__manage-link">Settings</a>
						<a href="/settings/feeds" class="dashboard__manage-link">Sources</a>
						<a href="/settings/topics" class="dashboard__manage-link">Topics</a>
						{#if user.is_admin}
							<a href="/settings/admin" class="dashboard__manage-link">Admin</a>
						{/if}
					</div>
				</nav>

				<button type="button" class="btn-secondary btn-sm dashboard__logout" onclick={logout}>
					Sign out
				</button>
			{:else if !loading}
				<p class="muted small">Could not load account info.</p>
				<a href="/login" class="btn-secondary btn-sm">Sign in</a>
			{/if}
		</aside>

		<div class="dashboard__main">
			<header class="dashboard__head stagger-in" style="--i: 1">
				<p class="eyebrow">Today's edition</p>
				<h1 class="display-title">{todayLabel}</h1>
				{#if !loading && fetchedLabel}
					<p class="dashboard__sync muted small">Last pulled {fetchedLabel}</p>
				{/if}
			</header>

			{#if loading}
				<p class="loading-pulse dashboard__loading">Loading your edition</p>
			{:else if error}
				<div class="card dashboard__error">
					<p class="error">{error}</p>
					<button class="btn-secondary btn-sm" style="margin-top: 1rem" onclick={load}>Try again</button>
				</div>
			{:else}
				<section class="dashboard__metrics card stagger-in" style="--i: 2" aria-label="Edition summary">
					<div class="dashboard__metric">
						<span class="dashboard__metric-value" class:dashboard__metric-value--live={unreadCount > 0}>
							{unreadCount}
						</span>
						<span class="dashboard__metric-label">Unread</span>
					</div>
					<div class="dashboard__metric">
						<span class="dashboard__metric-value">{storyCount}</span>
						<span class="dashboard__metric-label">Stories</span>
					</div>
					<div class="dashboard__metric">
						<span class="dashboard__metric-value">{channelCount}</span>
						<span class="dashboard__metric-label">Topics</span>
					</div>
				</section>

				{#if feed && feed.groups.length > 0}
					<div class="dashboard__routes-wrap stagger-in" style="--i: 3">
						<p class="dashboard__routes-label">Routed to</p>
						<div class="dashboard__routes scrollbar-desk" aria-label="Active topics">
							{#each feed.groups as group, i (group.topic_id)}
								<span class="dashboard__route" style="--ch: var(--channel-{i % 4})">
									{group.topic_name}
									{#if group.unread_count > 0}
										<em>{group.unread_count}</em>
									{/if}
								</span>
							{/each}
						</div>
					</div>
				{:else}
					<p class="dashboard__setup stagger-in" style="--i: 3">
						Add a <a href="/settings/feeds">source</a>, create a <a href="/settings/topics">topic</a>,
						then pull stories below.
					</p>
				{/if}

				<nav class="dashboard__tiles stagger-in" style="--i: 4" aria-label="Edition actions">
					<a href="/feed" class="dashboard__tile dashboard__tile--primary">
						<span class="routing-lamp routing-lamp--live" aria-hidden="true"></span>
						<span class="dashboard__tile-text">
							<span class="dashboard__tile-label">Read edition</span>
							<span class="dashboard__tile-hint">Swipe through today's stories</span>
						</span>
						<span class="dashboard__tile-chevron" aria-hidden="true">→</span>
					</a>

					<a href="/feed?view=list" class="dashboard__tile">
						<span class="dashboard__tile-text">
							<span class="dashboard__tile-label">List view</span>
							<span class="dashboard__tile-hint">Scan headlines by topic</span>
						</span>
						<span class="dashboard__tile-chevron" aria-hidden="true">→</span>
					</a>

					<button type="button" class="dashboard__tile" onclick={pollNow} disabled={polling}>
						<span class="dashboard__tile-text">
							<span class="dashboard__tile-label">{polling ? 'Pulling…' : 'Pull latest'}</span>
							<span class="dashboard__tile-hint">Fetch new stories from sources</span>
						</span>
						<span class="dashboard__tile-chevron" aria-hidden="true">{polling ? '…' : '↻'}</span>
					</button>

					<a href="/archive" class="dashboard__tile">
						<span class="dashboard__tile-text">
							<span class="dashboard__tile-label">Archive</span>
							<span class="dashboard__tile-hint">Browse past editions</span>
						</span>
						<span class="dashboard__tile-chevron" aria-hidden="true">→</span>
					</a>
				</nav>
			{/if}
		</div>
	</div>
</div>

{#if pollReport}
	<PollReport result={pollReport} onClose={() => (pollReport = null)} />
{/if}

<style>
	.dashboard {
		padding-bottom: 2.5rem;
	}

	.dashboard__layout {
		display: grid;
		gap: 1.25rem;
		align-items: start;
	}

	@media (min-width: 900px) {
		.dashboard__layout {
			grid-template-columns: minmax(15rem, 17.5rem) 1fr;
			gap: 1.75rem;
		}
	}

	.dashboard__account {
		padding: 1.25rem;
	}

	.dashboard__account-head {
		display: flex;
		align-items: center;
		gap: 0.875rem;
		margin-bottom: 1.125rem;
	}

	.dashboard__avatar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.75rem;
		height: 2.75rem;
		border-radius: var(--radius-md);
		background: var(--press-dim);
		border: 1px solid color-mix(in srgb, var(--press) 35%, var(--rule));
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 700;
		color: var(--press-bright);
		flex-shrink: 0;
	}

	.dashboard__account-id {
		min-width: 0;
	}

	.dashboard__account-eyebrow {
		margin: 0;
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.dashboard__account-name {
		margin: 0.15rem 0 0;
		font-family: var(--font-display);
		font-size: 1.25rem;
		font-weight: 700;
		line-height: 1.2;
		color: var(--chalk);
		word-break: break-word;
	}

	.dashboard__badge {
		display: inline-block;
		margin-top: 0.35rem;
		padding: 0.15rem 0.45rem;
		border-radius: 999px;
		background: var(--route-dim);
		border: 1px solid color-mix(in srgb, var(--route) 35%, var(--rule));
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--route);
	}

	.dashboard__account-meta {
		margin: 0 0 1.125rem;
		padding: 0.875rem 0 0;
		border-top: 1px solid var(--rule);
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}

	.dashboard__meta-row {
		display: grid;
		grid-template-columns: 6.5rem 1fr;
		gap: 0.5rem;
		align-items: baseline;
	}

	.dashboard__meta-row dt {
		margin: 0;
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.dashboard__meta-row dd {
		margin: 0;
		font-size: 0.8125rem;
		line-height: 1.4;
		color: var(--chalk);
		word-break: break-word;
	}

	.dashboard__manage {
		margin-bottom: 1rem;
	}

	.dashboard__manage-label {
		margin: 0 0 0.5rem;
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.dashboard__manage-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
	}

	.dashboard__manage-link {
		display: inline-flex;
		align-items: center;
		padding: 0.35rem 0.65rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--rule);
		background: var(--ink);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--chalk-muted);
		text-decoration: none;
		transition:
			color var(--duration-fast) var(--ease-out),
			border-color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.dashboard__manage-link:hover {
		color: var(--chalk);
		border-color: var(--rule-light);
		background: var(--ink-raised);
	}

	.dashboard__logout {
		width: 100%;
		justify-content: center;
	}

	.dashboard__main {
		min-width: 0;
	}

	.dashboard__head {
		margin-bottom: 1.25rem;
	}

	.dashboard__sync {
		margin: 0.5rem 0 0;
	}

	.dashboard__loading {
		margin: 2rem 0;
	}

	.dashboard__error {
		padding: 1.25rem;
	}

	.dashboard__metrics {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		padding: 0;
		overflow: hidden;
	}

	.dashboard__metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		padding: 1.25rem 0.75rem;
		text-align: center;
	}

	.dashboard__metric:not(:last-child) {
		border-right: 1px solid var(--rule);
	}

	.dashboard__metric-value {
		font-family: var(--font-display);
		font-size: clamp(1.75rem, 5vw, 2.25rem);
		font-weight: 700;
		line-height: 1;
		letter-spacing: -0.03em;
		color: var(--chalk);
		font-variant-numeric: tabular-nums;
	}

	.dashboard__metric-value--live {
		color: var(--press-bright);
		text-shadow: 0 0 24px rgba(232, 163, 23, 0.35);
	}

	.dashboard__metric-label {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.dashboard__routes-wrap {
		margin-top: 1.25rem;
	}

	.dashboard__routes-label {
		margin: 0 0 0.5rem;
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.dashboard__routes {
		display: flex;
		flex-wrap: nowrap;
		gap: 0.5rem;
		overflow-x: auto;
		padding-bottom: 0.25rem;
		-webkit-overflow-scrolling: touch;
		scrollbar-width: none;
	}

	.dashboard__routes::-webkit-scrollbar {
		display: none;
	}

	.dashboard__route {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.4rem 0.75rem;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: var(--ink-soft);
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--chalk-muted);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.dashboard__route::before {
		content: '';
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: var(--ch);
		box-shadow: 0 0 6px color-mix(in srgb, var(--ch) 60%, transparent);
	}

	.dashboard__route em {
		font-style: normal;
		color: var(--press-bright);
		font-weight: 600;
	}

	.dashboard__setup {
		margin: 1.25rem 0 0;
		font-size: 0.875rem;
		line-height: 1.55;
		color: var(--chalk-muted);
	}

	.dashboard__setup a {
		color: var(--route);
	}

	.dashboard__tiles {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.625rem;
		margin-top: 1.5rem;
	}

	.dashboard__tile {
		display: flex;
		align-items: flex-start;
		gap: 0.625rem;
		padding: 1rem 1rem 1rem 0.875rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--rule);
		background: var(--ink-soft);
		color: inherit;
		font: inherit;
		text-align: left;
		text-decoration: none;
		cursor: pointer;
		transition:
			border-color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out),
			transform var(--duration-fast) var(--ease-out);
	}

	.dashboard__tile:hover:not(:disabled) {
		border-color: var(--rule-light);
		background: var(--ink-raised);
		transform: translateY(-1px);
	}

	.dashboard__tile:disabled {
		opacity: 0.65;
		cursor: wait;
	}

	.dashboard__tile--primary {
		border-color: color-mix(in srgb, var(--press) 35%, var(--rule));
		background: linear-gradient(135deg, var(--press-dim) 0%, var(--ink-soft) 55%);
	}

	.dashboard__tile--primary:hover:not(:disabled) {
		border-color: color-mix(in srgb, var(--press) 55%, var(--rule));
		background: linear-gradient(135deg, rgba(232, 163, 23, 0.2) 0%, var(--ink-raised) 55%);
	}

	.dashboard__tile-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
		flex: 1;
	}

	.dashboard__tile-label {
		font-family: var(--font-ui);
		font-size: 0.875rem;
		font-weight: 650;
		color: var(--chalk);
		line-height: 1.25;
	}

	.dashboard__tile-hint {
		font-size: 0.75rem;
		line-height: 1.4;
		color: var(--chalk-muted);
	}

	.dashboard__tile-chevron {
		flex-shrink: 0;
		align-self: center;
		font-family: var(--font-mono);
		font-size: 0.875rem;
		color: var(--chalk-muted);
		opacity: 0.7;
		transition:
			transform var(--duration-fast) var(--ease-out),
			color var(--duration-fast) var(--ease-out);
	}

	.dashboard__tile:hover:not(:disabled) .dashboard__tile-chevron {
		transform: translateX(2px);
		color: var(--press-bright);
	}

	.dashboard__tile--primary .dashboard__tile-chevron {
		color: var(--press-bright);
		opacity: 1;
	}

	@media (min-width: 640px) {
		.dashboard__tiles {
			grid-template-columns: repeat(2, 1fr);
		}

		.dashboard__tile {
			flex-direction: column;
			align-items: stretch;
			min-height: 6.5rem;
			padding: 1.125rem;
		}

		.dashboard__tile-chevron {
			align-self: flex-end;
			margin-top: auto;
		}
	}

	@media (max-width: 639px) {
		.dashboard__tile--primary .routing-lamp {
			margin-top: 0.2rem;
		}

		.dashboard__meta-row {
			grid-template-columns: 1fr;
			gap: 0.15rem;
		}
	}
</style>
