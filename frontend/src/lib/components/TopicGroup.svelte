<script lang="ts">
	import FeedCard from './FeedCard.svelte';
	import type { TopicFeedGroup } from '$lib/api';

	let {
		group,
		onArticleClick,
		channelIndex = 0
	}: {
		group: TopicFeedGroup;
		onArticleClick: (articleId: number) => void;
		channelIndex?: number;
	} = $props();

	const channelColor = $derived(`var(--channel-${channelIndex % 4})`);
</script>

<section class="channel" style="--channel-color: {channelColor}; --channel-i: {channelIndex}">
	<header class="channel__header">
		<div class="channel__stripe" aria-hidden="true"></div>
		<div class="channel__label">
			<span class="channel__tag">Channel</span>
			<h2 class="channel__name">{group.topic_name}</h2>
		</div>
		{#if group.unread_count > 0}
			<span class="channel__count">{group.unread_count} new</span>
		{/if}
	</header>
	<div class="channel__stories">
		{#each group.articles as article, i (article.user_article_id)}
			<div class="stagger-in" style="--i: {i}">
				<FeedCard article={article} onclick={() => onArticleClick(article.id)} />
			</div>
		{/each}
	</div>
</section>

<style>
	.channel {
		margin-bottom: 2.5rem;
	}

	.channel__header {
		display: flex;
		align-items: center;
		gap: 0.875rem;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid var(--rule);
	}

	.channel__stripe {
		width: 4px;
		height: 2rem;
		border-radius: 2px;
		background: var(--channel-color);
		flex-shrink: 0;
	}

	.channel__label {
		flex: 1;
		min-width: 0;
	}

	.channel__tag {
		display: block;
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--channel-color);
		margin-bottom: 0.125rem;
	}

	.channel__name {
		font-family: var(--font-display);
		font-size: 1.25rem;
		font-weight: 700;
		margin: 0;
		letter-spacing: -0.02em;
		color: var(--chalk);
	}

	.channel__count {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		padding: 0.25rem 0.625rem;
		border-radius: 999px;
		background: var(--press-dim);
		color: var(--press-bright);
		flex-shrink: 0;
	}

	.channel__stories {
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}
</style>
