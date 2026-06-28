<script lang="ts">
	import { api, type Feed, type Topic } from '$lib/api';
	import { describeMatching, suggestKeywords } from '$lib/topicKeywords';
	import { confirmStore } from '$lib/confirm.svelte';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let topics = $state<Topic[]>([]);
	let feeds = $state<Feed[]>([]);
	let name = $state('');
	let keywords = $state('');
	let excludeKeywords = $state('');
	let selectedFeeds = $state<number[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');
	let editingId = $state<number | null>(null);
	let editKeywords = $state('');
	let editExcludeKeywords = $state('');
	let editFeeds = $state<number[]>([]);
	let updatingId = $state<number | null>(null);

	const matchHint = $derived(describeMatching(name, keywords));

	async function load() {
		loading = true;
		try {
			[topics, feeds] = await Promise.all([api.getTopics(), api.getFeeds()]);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	function onNameInput() {
		if (keywords.trim()) return;
		const suggested = suggestKeywords(name);
		if (suggested) keywords = suggested;
	}

	async function addTopic(e: Event) {
		e.preventDefault();
		saving = true;
		error = '';
		try {
			await api.createTopic({
				name: name.trim(),
				keywords: keywords.trim(),
				exclude_keywords: excludeKeywords.trim(),
				feed_ids: selectedFeeds
			});
			name = '';
			keywords = '';
			excludeKeywords = '';
			selectedFeeds = [];
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not create topic';
		} finally {
			saving = false;
		}
	}

	async function removeTopic(topic: Topic) {
		const ok = await confirmStore.confirm({
			title: 'Delete topic?',
			message: `Remove "${topic.name}" and stop routing stories to this channel.`,
			confirmLabel: 'Delete'
		});
		if (!ok) return;
		try {
			await api.deleteTopic(topic.id);
			if (editingId === topic.id) editingId = null;
			toast.success(`Deleted ${topic.name}`);
			await load();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Could not delete topic');
		}
	}

	function toggleFeed(id: number) {
		selectedFeeds = selectedFeeds.includes(id)
			? selectedFeeds.filter((f) => f !== id)
			: [...selectedFeeds, id];
	}

	function startEdit(topic: Topic) {
		editingId = topic.id;
		editKeywords = topic.keywords;
		editExcludeKeywords = topic.exclude_keywords || '';
		editFeeds = [...topic.feed_ids];
	}

	function cancelEdit() {
		editingId = null;
	}

	function toggleEditFeed(id: number) {
		editFeeds = editFeeds.includes(id)
			? editFeeds.filter((f) => f !== id)
			: [...editFeeds, id];
	}

	async function saveEdit(topicId: number) {
		updatingId = topicId;
		error = '';
		try {
			await api.updateTopic(topicId, {
				keywords: editKeywords.trim(),
				exclude_keywords: editExcludeKeywords.trim(),
				feed_ids: editFeeds
			});
			editingId = null;
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not save topic';
		} finally {
			updatingId = null;
		}
	}

	function applySuggestion(topic: Topic) {
		const suggested = suggestKeywords(topic.name);
		if (suggested) {
			if (editingId === topic.id) {
				editKeywords = suggested;
			}
		}
	}

	onMount(load);
</script>

<div class="container container--wide">
	<header class="page-header wire-edge">
		<div>
			<p class="eyebrow">Routing</p>
			<h1 class="display-title">Topics</h1>
			<p class="lead">Channels on your Today page. Link a source, name your topic — we find the right section of the site.</p>
		</div>
	</header>

	<div class="card how-it-works stagger-in" style="--i: 0">
		<p class="eyebrow">How matching works</p>
		<ol>
			<li><strong>Link sources</strong> — on Sources, turn on this topic for each news site you want.</li>
			<li><strong>Set keywords</strong> — we scan article titles and summaries for any keyword you list.</li>
			<li><strong>Fetch latest</strong> — on Today, pull new stories. Matches appear under this channel.</li>
		</ol>
		<p class="how-example muted">
			Add <code>bbc.com</code>, create a Politics topic, turn on Politics under that source — we
			automatically pull from BBC's politics feed. Keywords are optional for extra filtering.
		</p>
	</div>

	<form class="card add-form stagger-in" style="--i: 1" onsubmit={addTopic}>
		<p class="eyebrow">New channel</p>
		<label class="label" for="name">Topic name</label>
		<input
			id="name"
			class="input"
			bind:value={name}
			oninput={onNameInput}
			placeholder="Politics"
			required
		/>
		<label class="label" for="keywords">Keywords</label>
		<input
			id="keywords"
			class="input"
			bind:value={keywords}
			placeholder="politics, election, congress, senate, parliament"
		/>
		<label class="label" for="exclude">Exclude keywords</label>
		<input
			id="exclude"
			class="input"
			bind:value={excludeKeywords}
			placeholder="rumor, gossip, sponsored"
		/>
		<p class="match-hint">{matchHint}</p>
		{#if feeds.length > 0}
			<p class="label" style="margin-top: 0.75rem">Sources for this topic</p>
			<div class="chips">
				{#each feeds as feed (feed.id)}
					<button
						type="button"
						class="chip"
						class:active={selectedFeeds.includes(feed.id)}
						onclick={() => toggleFeed(feed.id)}
					>
						{feed.title}
					</button>
				{/each}
			</div>
		{:else}
			<p class="muted" style="margin-top: 0.5rem">Add sources first, then link them here or on the Sources page.</p>
		{/if}
		<button class="btn" type="submit" disabled={saving} style="margin-top: 1.25rem">
			{saving ? 'Creating…' : 'Create topic'}
		</button>
		{#if error}<p class="error">{error}</p>{/if}
	</form>

	{#if loading}
		<p class="loading-pulse">Loading topics</p>
	{:else if topics.length === 0}
		<div class="card empty-state">
			<p class="eyebrow">No channels yet</p>
			<p class="lead" style="margin: 0 auto">Create a topic to group stories on your Today page.</p>
		</div>
	{:else}
		<ul class="topic-list">
			{#each topics as topic, i (topic.id)}
				<li class="topic-item card stagger-in" style="--channel-color: var(--channel-{i % 4}); --i: {i}">
					<div class="topic-item__stripe" aria-hidden="true"></div>
					<div class="topic-item__body">
						<div class="topic-item__head">
							<div>
								<span class="topic-item__tag">Channel</span>
								<strong class="topic-item__name">{topic.name}</strong>
							</div>
							<div class="topic-item__actions">
								{#if editingId !== topic.id}
									<button class="btn-ghost btn-sm" onclick={() => startEdit(topic)}>Edit</button>
								{/if}
								<button class="btn-ghost btn-sm" onclick={() => removeTopic(topic)}>Delete</button>
							</div>
						</div>

						{#if editingId === topic.id}
							<div class="topic-edit">
								<label class="label" for="edit-kw-{topic.id}">Keywords</label>
								<input
									id="edit-kw-{topic.id}"
									class="input"
									bind:value={editKeywords}
									placeholder="politics, election, congress"
								/>
								<label class="label" for="edit-ex-{topic.id}">Exclude keywords</label>
								<input
									id="edit-ex-{topic.id}"
									class="input"
									bind:value={editExcludeKeywords}
									placeholder="rumor, gossip"
								/>
								<p class="match-hint">{describeMatching(topic.name, editKeywords)}</p>
								{#if suggestKeywords(topic.name) && editKeywords !== suggestKeywords(topic.name)}
									<button type="button" class="btn-ghost btn-sm suggest-btn" onclick={() => applySuggestion(topic)}>
										Use suggested keywords for {topic.name}
									</button>
								{/if}
								{#if feeds.length > 0}
									<p class="label" style="margin-top: 0.75rem">Linked sources</p>
									<div class="chips">
										{#each feeds as feed (feed.id)}
											<button
												type="button"
												class="chip"
												class:active={editFeeds.includes(feed.id)}
												onclick={() => toggleEditFeed(feed.id)}
											>
												{feed.title}
											</button>
										{/each}
									</div>
								{/if}
								<div class="topic-edit__actions">
									<button
										class="btn btn-sm"
										disabled={updatingId === topic.id}
										onclick={() => saveEdit(topic.id)}
									>
										{updatingId === topic.id ? 'Saving…' : 'Save'}
									</button>
									<button class="btn-secondary btn-sm" onclick={cancelEdit}>Cancel</button>
								</div>
							</div>
						{:else}
							<p class="topic-item__keywords">
								{topic.keywords || 'All stories from linked sources (no keyword filter)'}
							</p>
							<p class="topic-item__meta">
								{topic.feed_ids.length} source{topic.feed_ids.length === 1 ? '' : 's'} linked
								{#if topic.feed_ids.length === 0}
									· <a href="/settings/feeds">Link sources</a>
								{/if}
							</p>
						{/if}
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.how-it-works {
		margin-bottom: 1.25rem;
	}

	.how-it-works ol {
		margin: 0.75rem 0;
		padding-left: 1.25rem;
		color: var(--chalk-muted);
		font-size: 0.875rem;
		line-height: 1.65;
	}

	.how-it-works li {
		margin-bottom: 0.375rem;
	}

	.how-it-works strong {
		color: var(--chalk);
	}

	.how-example {
		margin: 0;
		font-size: 0.8125rem;
		line-height: 1.55;
	}

	.match-hint {
		margin: 0.375rem 0 0;
		font-size: 0.8125rem;
		color: var(--route);
	}

	.add-form {
		margin-bottom: 2rem;
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.topic-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}

	.topic-item {
		display: flex;
		gap: 0;
		padding: 0;
		overflow: hidden;
	}

	.topic-item__stripe {
		width: 4px;
		background: var(--channel-color);
		flex-shrink: 0;
	}

	.topic-item__body {
		flex: 1;
		padding: 1rem 1.25rem;
		min-width: 0;
	}

	.topic-item__head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
	}

	.topic-item__actions {
		display: flex;
		gap: 0.25rem;
		flex-shrink: 0;
	}

	.topic-item__tag {
		display: block;
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--channel-color);
		margin-bottom: 0.125rem;
	}

	.topic-item__name {
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--chalk);
	}

	.topic-item__keywords {
		margin: 0.5rem 0 0;
		font-size: 0.875rem;
		color: var(--chalk-muted);
	}

	.topic-item__meta {
		margin: 0.375rem 0 0;
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.04em;
		color: var(--rule-light);
	}

	.topic-edit {
		margin-top: 0.875rem;
		padding-top: 0.875rem;
		border-top: 1px solid var(--rule);
	}

	.topic-edit__actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.suggest-btn {
		margin-top: 0.5rem;
	}
</style>
