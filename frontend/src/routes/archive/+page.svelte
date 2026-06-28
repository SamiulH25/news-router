<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, type DailyFeed } from '$lib/api';
	import FeedCard from '$lib/components/FeedCard.svelte';
	import { onMount } from 'svelte';

	let feed = $state<DailyFeed | null>(null);
	let loading = $state(true);
	let error = $state('');

	async function load() {
		loading = true;
		error = '';
		try {
			feed = await api.getArchivedFeed();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load archive';
		} finally {
			loading = false;
		}
	}

	function openArticle(id: number) {
		goto(`/read/${id}`);
	}

	onMount(load);
</script>

<div class="container container--wide">
	<header class="page-header wire-edge">
		<div>
			<p class="eyebrow">Past editions</p>
			<h1 class="display-title">Archive</h1>
			<p class="lead">Stories from previous fetches — your current stories are under Read</p>
		</div>
		<div class="page-header__actions">
			<a href="/feed" class="btn">Read stories</a>
		</div>
	</header>

	{#if loading}
		<p class="loading-pulse">Loading archive</p>
	{:else if error}
		<div class="card animate-in">
			<p class="error">{error}</p>
			<button class="btn-secondary" style="margin-top: 1rem" onclick={load}>Try again</button>
		</div>
	{:else if !feed || feed.groups.length === 0}
		<div class="card empty-state animate-in">
			<p class="eyebrow">Nothing archived yet</p>
			<p class="lead" style="margin: 0 auto">
				When you fetch a new edition, the previous feed moves here.
			</p>
		</div>
	{:else}
		{#each feed.groups as group, gi (group.topic_id)}
			<section class="archive-group" style="--channel-i: {gi}">
				<h2 class="archive-group__title">{group.topic_name}</h2>
				<div class="archive-group__list">
					{#each group.articles as article, ai (article.user_article_id)}
						<div class="stagger-in" style="--i: {ai}">
							<FeedCard {article} onclick={() => openArticle(article.id)} />
						</div>
					{/each}
				</div>
			</section>
		{/each}
	{/if}
</div>
