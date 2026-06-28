<script lang="ts">
	import { api, type Feed, type Topic } from '$lib/api';
	import { confirmStore } from '$lib/confirm.svelte';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let feeds = $state<Feed[]>([]);
	let topics = $state<Topic[]>([]);
	let siteUrl = $state('');
	let detected = $state<{
		title: string;
		feed_url: string;
		site_url: string | null;
		sections: string[];
	} | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let detecting = $state(false);
	let error = $state('');
	let message = $state('');

	async function load() {
		loading = true;
		try {
			[feeds, topics] = await Promise.all([api.getFeeds(), api.getTopics()]);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	let detectTimer: ReturnType<typeof setTimeout> | undefined;
	let detectPromise: Promise<void> | null = null;

	function onSiteInput() {
		detected = null;
		error = '';
		clearTimeout(detectTimer);
		if (!siteUrl.trim()) return;
		detectTimer = setTimeout(() => {
			detectPromise = detectSite();
		}, 600);
	}

	function onSitePaste() {
		clearTimeout(detectTimer);
		detectTimer = setTimeout(() => {
			detectPromise = detectSite();
		}, 100);
	}

	async function ensureDetected(): Promise<boolean> {
		clearTimeout(detectTimer);
		if (detecting && detectPromise) {
			await detectPromise;
		} else if (!detected && siteUrl.trim()) {
			await detectSite();
		}
		return detected !== null;
	}

	async function detectSite() {
		if (!siteUrl.trim()) return;
		detecting = true;
		error = '';
		try {
			const meta = await api.previewFeed(siteUrl.trim());
			detected = {
				title: meta.title,
				feed_url: meta.feed_url,
				site_url: meta.site_url,
				sections: meta.sections ?? []
			};
		} catch (err) {
			detected = null;
			error = err instanceof Error ? err.message : 'Could not find news from that site';
		} finally {
			detecting = false;
		}
	}

	async function addFeed(e: Event) {
		e.preventDefault();
		if (!siteUrl.trim()) return;
		if (!(await ensureDetected())) return;
		saving = true;
		error = '';
		message = '';
		try {
			const feed = await api.createFeed({ url: siteUrl.trim(), topic_ids: selectedTopics });
			siteUrl = '';
			detected = null;
			selectedTopics = [];
			message = `Added ${feed.title}`;
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not add that site';
		} finally {
			saving = false;
		}
	}

	let selectedTopics = $state<number[]>([]);

	async function exportOpml() {
		const blob = await api.exportOpml();
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = 'news-router.opml';
		a.click();
	}

	async function importOpml(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		try {
			const result = await api.importOpml(file);
			message = `Imported ${result.imported} sources`;
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Import failed';
		}
		input.value = '';
	}

	function toggleTopic(id: number) {
		selectedTopics = selectedTopics.includes(id)
			? selectedTopics.filter((t) => t !== id)
			: [...selectedTopics, id];
	}

	let updatingFeedId = $state<number | null>(null);
	let retryingFeedId = $state<number | null>(null);

	async function removeFeed(feed: Feed) {
		const ok = await confirmStore.confirm({
			title: 'Remove source?',
			message: `Stop receiving stories from ${feed.title}. You can add it again later.`,
			confirmLabel: 'Remove'
		});
		if (!ok) return;
		try {
			await api.deleteFeed(feed.id);
			toast.success(`Removed ${feed.title}`);
			await load();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Could not remove source');
		}
	}

	async function retryFeed(feed: Feed) {
		retryingFeedId = feed.id;
		try {
			const result = await api.pollFeed(feed.id);
			if (result.error) {
				toast.error(`${feed.title}: ${result.error}`);
			} else {
				toast.success(`${feed.title}: ${result.new_articles} new, ${result.routed_to_topics} routed`);
			}
			await load();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Retry failed');
		} finally {
			retryingFeedId = null;
		}
	}

	async function toggleSourceTopic(feed: Feed, topicId: number) {
		updatingFeedId = feed.id;
		error = '';
		const next = feed.topic_ids.includes(topicId)
			? feed.topic_ids.filter((id) => id !== topicId)
			: [...feed.topic_ids, topicId];
		try {
			await api.updateFeed(feed.id, { topic_ids: next });
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not update routing';
		} finally {
			updatingFeedId = null;
		}
	}

	function isRouting(feed: Feed) {
		return feed.topic_ids.length > 0;
	}

	onMount(load);
</script>

<div class="container container--wide">
	<header class="page-header wire-edge">
		<div>
			<p class="eyebrow">Input</p>
			<h1 class="display-title">News sources</h1>
			<p class="lead">Paste a website — we find the feed and match sections to your topics automatically</p>
		</div>
		<div class="page-header__actions">
			<button class="btn-secondary btn-sm" onclick={exportOpml}>Export</button>
			<label class="btn-secondary btn-sm file-btn">
				Import
				<input type="file" accept=".opml,.xml" onchange={importOpml} hidden />
			</label>
		</div>
	</header>

	<form class="card add-form stagger-in" style="--i: 0" onsubmit={addFeed}>
		<p class="eyebrow">Add source</p>
		<label class="label" for="site">Website</label>
		<input
			id="site"
			class="input"
			bind:value={siteUrl}
			oninput={onSiteInput}
			onpaste={onSitePaste}
			placeholder="bbc.com or nytimes.com"
			required
			autocomplete="url"
		/>
		{#if detecting}
			<p class="loading-pulse" style="margin-top: 1rem">Checking site…</p>
		{:else if detected}
			<div class="detected">
				<span class="detected__label">Ready to add</span>
				<strong class="detected__title">{detected.title}</strong>
				<span class="detected__url">{detected.site_url ?? siteUrl}</span>
				{#if detected.sections.length > 0}
					<span class="detected__sections">
						Sections we can route: {detected.sections.join(', ')}
					</span>
				{/if}
			</div>
		{:else if siteUrl.trim() && error}
			<p class="error">{error}</p>
		{/if}
		{#if topics.length > 0}
			<p class="label" style="margin-top: 1.25rem">Route to topics (optional — you can also do this after adding)</p>
			<div class="chips">
				{#each topics as topic (topic.id)}
					<button
						type="button"
						class="chip"
						class:active={selectedTopics.includes(topic.id)}
						onclick={() => toggleTopic(topic.id)}
					>
						{topic.name}
					</button>
				{/each}
			</div>
		{/if}
		<button
			class="btn"
			type="submit"
			disabled={saving || detecting || !siteUrl.trim()}
			style="margin-top: 1.25rem"
		>
			{saving ? 'Adding…' : detecting ? 'Checking…' : 'Add source'}
		</button>
		{#if error && !(siteUrl.trim() && !detected && !detecting)}
			<p class="error">{error}</p>
		{/if}
		{#if message}<p class="success">{message}</p>{/if}
	</form>

	{#if loading}
		<p class="loading-pulse">Loading sources</p>
	{:else if feeds.length === 0}
		<div class="card empty-state">
			<p class="eyebrow">No sources yet</p>
			<p class="lead" style="margin: 0 auto">Paste a news site above to start your first channel.</p>
		</div>
	{:else}
		<ul class="source-list">
			{#each feeds as feed, i (feed.id)}
				<li class="source-item card stagger-in" class:source-item--inactive={!isRouting(feed)} style="--i: {i}">
					<div class="source-item__content">
						<div class="source-item__main">
							{#if feed.favicon_url}
								<img src={feed.favicon_url} alt="" class="source-item__icon" />
							{:else}
								<div class="source-item__icon source-item__icon--placeholder" aria-hidden="true"></div>
							{/if}
							<div class="source-item__info">
								<div class="source-item__head">
									<strong class="source-item__name">{feed.title}</strong>
									<span
										class="source-item__badge"
										class:source-item__badge--active={isRouting(feed)}
									>
										{isRouting(feed) ? 'Routing' : 'Not routing'}
									</span>
								</div>
								<span class="source-item__url">{feed.site_url ?? feed.url}</span>
								{#if feed.last_error}
									<span class="source-item__status source-item__status--error">{feed.last_error}</span>
								{:else if feed.last_successful_fetch}
									<span class="source-item__status"
										>Updated {new Date(feed.last_successful_fetch).toLocaleString()}</span
									>
								{/if}
							</div>
						</div>

						{#if topics.length > 0}
							<div class="source-item__routing">
								<p class="source-item__routing-label">
									{isRouting(feed)
										? 'Routed to — we pull the matching site section automatically'
										: 'Turn on — pick topics; we find the right section of the site for each'}
								</p>
								<div class="chips">
									{#each topics as topic (topic.id)}
										<button
											type="button"
											class="chip"
											class:active={feed.topic_ids.includes(topic.id)}
											disabled={updatingFeedId === feed.id}
											onclick={() => toggleSourceTopic(feed, topic.id)}
										>
											{topic.name}
										</button>
									{/each}
								</div>
							</div>
						{:else}
							<p class="source-item__hint muted">
								<a href="/settings/topics">Create a topic</a> to start receiving stories from this source.
							</p>
						{/if}
					</div>
					<div class="source-item__actions">
						{#if feed.last_error}
							<button
								class="btn-secondary btn-sm"
								disabled={retryingFeedId === feed.id}
								onclick={() => retryFeed(feed)}
							>
								{retryingFeedId === feed.id ? '…' : 'Retry'}
							</button>
						{/if}
						<button class="btn-ghost btn-sm" onclick={() => removeFeed(feed)}>Remove</button>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.add-form {
		margin-bottom: 2rem;
	}

	.detected {
		margin-top: 1rem;
		padding: 1rem 1.125rem;
		background: var(--ink);
		border: 1px solid var(--press);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.detected__label {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--press-bright);
	}

	.detected__title {
		font-family: var(--font-display);
		font-size: 1.125rem;
		color: var(--chalk);
	}

	.detected__url {
		font-size: 0.8125rem;
		color: var(--chalk-muted);
		word-break: break-all;
	}

	.detected__sections {
		font-size: 0.75rem;
		color: var(--route);
		margin-top: 0.375rem;
		line-height: 1.45;
	}

	.source-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}

	.source-item {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem 1.25rem;
	}

	.source-item--inactive {
		border-color: color-mix(in srgb, var(--danger) 35%, var(--rule));
	}

	.source-item__content {
		flex: 1;
		min-width: 0;
	}

	.source-item__main {
		display: flex;
		gap: 0.875rem;
		min-width: 0;
		align-items: flex-start;
	}

	.source-item__head {
		display: flex;
		align-items: center;
		gap: 0.625rem;
		flex-wrap: wrap;
	}

	.source-item__badge {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		padding: 0.125rem 0.5rem;
		border-radius: 999px;
		background: var(--danger-dim);
		color: var(--danger);
	}

	.source-item__badge--active {
		background: var(--route-dim);
		color: var(--route);
	}

	.source-item__routing {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid var(--rule);
	}

	.source-item__routing-label {
		margin: 0 0 0.625rem;
		font-size: 0.8125rem;
		color: var(--chalk-muted);
	}

	.source-item__hint {
		margin: 0.75rem 0 0;
		font-size: 0.8125rem;
	}

	.source-item__icon {
		width: 22px;
		height: 22px;
		border-radius: 4px;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.source-item__icon--placeholder {
		background: var(--ink-soft);
		border: 1px solid var(--rule);
	}

	.source-item__info {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		min-width: 0;
	}

	.source-item__name {
		font-family: var(--font-display);
		font-size: 1rem;
		font-weight: 600;
		color: var(--chalk);
	}

	.source-item__url {
		font-size: 0.8125rem;
		color: var(--chalk-muted);
		word-break: break-all;
	}

	.source-item__status {
		font-size: 0.75rem;
		color: var(--chalk-muted);
		margin-top: 0.25rem;
	}

	.source-item__actions {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.375rem;
		flex-shrink: 0;
	}

	.source-item__status--error {
		color: var(--danger);
	}
</style>
