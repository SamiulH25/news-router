<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api, type DailyFeed, type PollResponse, type Topic, type User } from '$lib/api';
	import PollReport from '$lib/components/PollReport.svelte';
	import SwipeFeed from '$lib/components/SwipeFeed.svelte';
	import TopicGroup from '$lib/components/TopicGroup.svelte';
	import { flattenFeed } from '$lib/feedUtils';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let feed = $state<DailyFeed | null>(null);
	let topics = $state<Topic[]>([]);
	let user = $state<User | null>(null);
	let loading = $state(true);
	let polling = $state(false);
	let error = $state('');
	let viewMode = $state<'reels' | 'list'>('reels');
	let selectedTopicId = $state<number | null>(null);
	let searchQuery = $state('');
	let searchOpen = $state(false);
	let includeArchived = $state(false);
	let pollReport = $state<PollResponse | null>(null);

	const todayLabel = new Intl.DateTimeFormat(undefined, {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	}).format(new Date());

	const editionLabel = $derived.by(() => {
		if (feed?.edition_fetched_at) {
			return `Fetched ${new Date(feed.edition_fetched_at).toLocaleString(undefined, {
				month: 'short',
				day: 'numeric',
				hour: 'numeric',
				minute: '2-digit'
			})}`;
		}
		return `Last ${user?.feed_window_hours ?? 12}h`;
	});

	const articles = $derived(feed ? flattenFeed(feed) : []);
	const filteredGroups = $derived(
		selectedTopicId == null
			? (feed?.groups ?? [])
			: (feed?.groups.filter((g) => g.topic_id === selectedTopicId) ?? [])
	);

	async function load() {
		loading = true;
		error = '';
		try {
			const q = searchQuery.trim();
			if (q && includeArchived) {
				feed = await api.searchArticles(q, true);
				topics = await api.getTopics();
				user = await api.me();
			} else {
				const [feedData, topicData, me] = await Promise.all([
					api.getDailyFeed({
						topicId: selectedTopicId ?? undefined,
						q: q || undefined
					}),
					api.getTopics(),
					api.me()
				]);
				feed = feedData;
				topics = topicData;
				user = me;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load your feed';
		} finally {
			loading = false;
		}
	}

	async function pollNow() {
		polling = true;
		error = '';
		try {
			pollReport = await api.triggerPoll();
			await load();
			toast.success(`Pulled ${pollReport.new_articles} new stories`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Pull failed';
			toast.error(error);
		} finally {
			polling = false;
		}
	}

	function openArticle(id: number) {
		const suffix = viewMode === 'list' ? '?from=list' : '';
		goto(`/read/${id}${suffix}`);
	}

	function toggleTopic(id: number) {
		selectedTopicId = id < 0 ? null : selectedTopicId === id ? null : id;
		load();
	}

	async function runSearch() {
		searchOpen = false;
		await load();
	}

	function setViewMode(mode: 'reels' | 'list') {
		const hadFilter = selectedTopicId != null;
		viewMode = mode;
		if (mode === 'reels' && hadFilter) {
			selectedTopicId = null;
			load();
		}
		goto(mode === 'list' ? '/feed?view=list' : '/feed', { replaceState: true, noScroll: true });
	}

	onMount(() => {
		if ($page.url.searchParams.get('view') === 'list') {
			viewMode = 'list';
		}
		load();
	});
</script>

{#if loading}
	<div class="feed-empty">
		<p class="loading-pulse">Pulling in today's stories</p>
		<p class="feed-empty__sub">{editionLabel}</p>
	</div>
{:else if error}
	<div class="feed-empty">
		<div class="card">
			<p class="error">{error}</p>
			<button class="btn-secondary" style="margin-top: 1rem" onclick={load}>Try again</button>
		</div>
	</div>
{:else if !feed || articles.length === 0}
	<div class="feed-empty">
		<div class="card empty-state">
			<p class="eyebrow">Edition empty</p>
			<h2 class="display-title">No stories yet</h2>
			<p class="lead" style="margin: 0.75rem auto 0">
				Stories appear from the last {user?.feed_window_hours ?? 12} hours. Add a source, link it to a
				topic, then fetch the latest.
			</p>
			<div class="actions">
				<a href="/settings/feeds" class="btn">Add a source</a>
				<a href="/settings/topics" class="btn-secondary">Set up topics</a>
			</div>
		</div>
	</div>
{:else if viewMode === 'reels'}
	<SwipeFeed
		{articles}
		totalUnread={feed.total_unread}
		{todayLabel}
		{editionLabel}
		{polling}
		onRefresh={pollNow}
		onSearch={() => (searchOpen = true)}
		onToggleView={() => setViewMode('list')}
	/>
{:else}
	<div class="container container--wide list-feed">
		<header class="list-feed__header wire-edge">
			<div>
				<a href="/" class="list-feed__back">← Home</a>
				<p class="eyebrow">Read · list view</p>
				<h1 class="display-title">{todayLabel}</h1>
				<p class="muted">{editionLabel} · {feed.total_unread} unread</p>
			</div>
			<div class="list-feed__actions">
				<a href="/" class="btn-secondary btn-sm">Dashboard</a>
				<button class="btn-secondary btn-sm" onclick={() => (searchOpen = true)}>Search</button>
				<button class="btn-secondary btn-sm" onclick={() => setViewMode('reels')}>Reels</button>
				<button class="btn btn-sm" onclick={pollNow} disabled={polling}>
					{polling ? '…' : 'Pull latest'}
				</button>
			</div>
		</header>

		{#if topics.length > 0}
			<div class="topic-chips" role="tablist" aria-label="Filter by topic">
				<button
					class="topic-chip"
					class:topic-chip--active={selectedTopicId == null}
					onclick={() => toggleTopic(-1)}
				>
					All
				</button>
				{#each topics as topic (topic.id)}
					<button
						class="topic-chip"
						class:topic-chip--active={selectedTopicId === topic.id}
						onclick={() => toggleTopic(topic.id)}
					>
						{topic.name}
					</button>
				{/each}
			</div>
		{/if}

		{#each filteredGroups as group, i (group.topic_id)}
			<TopicGroup {group} channelIndex={i} onArticleClick={openArticle} />
		{/each}
	</div>
{/if}

{#if searchOpen}
	<div class="search-overlay" role="dialog" aria-label="Search stories">
		<form
			class="search-overlay__box card"
			onsubmit={(e) => {
				e.preventDefault();
				runSearch();
			}}
		>
			<label class="label" for="feed-search">Search headlines</label>
			<input id="feed-search" class="input" bind:value={searchQuery} placeholder="e.g. climate, Apple" />
			<label class="toggle-row" style="margin-top: 0.75rem">
				<input type="checkbox" bind:checked={includeArchived} />
				<span>Include past editions</span>
			</label>
			<div class="search-overlay__actions">
				<button type="button" class="btn-secondary" onclick={() => (searchOpen = false)}>Cancel</button>
				<button type="submit" class="btn">Search</button>
			</div>
		</form>
	</div>
{/if}

{#if pollReport}
	<PollReport result={pollReport} onClose={() => (pollReport = null)} />
{/if}

