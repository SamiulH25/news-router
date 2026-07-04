<script lang="ts">
	import { api, type ArticleSummary } from '$lib/api';
	import { toast } from '$lib/toast.svelte';

	let {
		article,
		onclick
	}: {
		article: ArticleSummary;
		onclick?: () => void;
	} = $props();

	let readOverride = $state<boolean | undefined>(undefined);
	let lessSent = $state(false);

	const isRead = $derived(readOverride ?? article.is_read);

	$effect(() => {
		article.user_article_id;
		readOverride = undefined;
	});

	function formatDate(value: string | null) {
		if (!value) return '';
		return new Date(value).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function cleanSummary(html: string) {
		return html.replace(/<[^>]+>/g, '').slice(0, 200);
	}

	async function markUnread(e: MouseEvent) {
		e.stopPropagation();
		try {
			await api.markUnread(article.user_article_id);
			readOverride = false;
			toast.info('Marked unread');
		} catch {
			toast.error('Could not mark unread');
		}
	}

	async function recordLess(e: MouseEvent) {
		e.stopPropagation();
		if (lessSent) return;
		lessSent = true;
		try {
			await api.engage(article.user_article_id, { event: 'less' });
			toast.info('We will show fewer stories like this');
		} catch {
			lessSent = false;
			toast.error('Could not save your preference');
		}
	}
</script>

<article class="story-card" class:unread={!isRead}>
	<div class="story-card__route" aria-hidden="true"></div>
	<button type="button" class="story-card__main" onclick={onclick}>
		<div class="story-card__meta">
			{#if article.favicon_url}
				<img src={article.favicon_url} alt="" class="story-card__favicon" />
			{/if}
			<span class="story-card__source">{article.feed_title}</span>
			{#if article.published_at}
				<span class="story-card__time">{formatDate(article.published_at)}</span>
			{/if}
			{#if !isRead}
				<span class="story-card__badge" aria-label="Unread">New</span>
			{/if}
		</div>
		<h3 class="story-card__title">{article.title}</h3>
		{#if article.summary}
			<p class="story-card__summary">{cleanSummary(article.summary)}</p>
		{/if}
	</button>
	<div class="story-card__actions">
		{#if isRead}
			<button type="button" class="story-card__action" onclick={markUnread}>Mark unread</button>
		{/if}
		<button type="button" class="story-card__action" disabled={lessSent} onclick={recordLess}>
			{lessSent ? 'Noted' : 'Less like this'}
		</button>
	</div>
</article>

<style>
	.story-card {
		display: flex;
		flex-direction: column;
		width: 100%;
		background: var(--ink-soft);
		color: var(--chalk);
		border: 1px solid var(--rule);
		border-radius: var(--radius-md);
		box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03) inset;
		transition:
			background var(--duration-fast) var(--ease-out),
			border-color var(--duration-fast) var(--ease-out);
		position: relative;
		overflow: hidden;
	}

	.story-card:hover {
		background: var(--ink-raised);
		border-color: var(--rule-light);
	}

	.story-card__route {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		width: 3px;
		background: linear-gradient(180deg, var(--press), transparent 80%);
		opacity: 0;
		transition: opacity var(--duration-fast) var(--ease-out);
	}

	.story-card.unread .story-card__route {
		opacity: 1;
	}

	.story-card__main {
		display: block;
		width: 100%;
		text-align: left;
		padding: 1.125rem 1.25rem 0.75rem 1.5rem;
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
	}

	.story-card__meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.625rem;
		flex-wrap: wrap;
	}

	.story-card__favicon {
		width: 14px;
		height: 14px;
		border-radius: 2px;
	}

	.story-card__source {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.story-card__time {
		font-size: 0.75rem;
		color: var(--chalk-muted);
		margin-left: auto;
	}

	.story-card__badge {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		padding: 0.125rem 0.4rem;
		border-radius: 2px;
		background: var(--press-dim);
		color: var(--press-bright);
	}

	.story-card__title {
		font-family: var(--font-display);
		font-size: 1.0625rem;
		font-weight: 600;
		line-height: 1.35;
		margin: 0;
		letter-spacing: -0.01em;
		color: var(--chalk);
	}

	.story-card__summary {
		margin: 0.5rem 0 0;
		font-family: var(--font-read);
		font-size: 0.875rem;
		line-height: 1.55;
		color: var(--chalk-muted);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.story-card__actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.375rem;
		padding: 0 1.25rem 0.875rem 1.5rem;
	}

	.story-card__action {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		padding: 0.3rem 0.55rem;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: transparent;
		color: var(--chalk-muted);
		cursor: pointer;
	}

	.story-card__action:hover:not(:disabled) {
		border-color: var(--rule-light);
		color: var(--chalk);
	}

	.story-card__action:disabled {
		opacity: 0.55;
		cursor: default;
	}
</style>
