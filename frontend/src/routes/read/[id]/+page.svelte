<script lang="ts">
	import { page } from '$app/stores';
	import { api, type ArticleRead } from '$lib/api';
	import { sanitizeHtml } from '$lib/sanitize';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let article = $state<ArticleRead | null>(null);
	let loading = $state(true);
	let error = $state('');
	let isRead = $state(true);

	const safeHtml = $derived(article?.content_html ? sanitizeHtml(article.content_html) : '');
	const articleId = $derived(Number($page.params.id));
	const backHref = $derived(
		$page.url.searchParams.get('from') === 'list' ? '/feed?view=list' : '/feed'
	);

	onMount(async () => {
		try {
			article = await api.readArticle(articleId);
			isRead = true;
			if (article.user_article_id) {
				api.engage(article.user_article_id, { event: 'open' }).catch(() => {});
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load this story';
		} finally {
			loading = false;
		}
	});

	async function markUnread() {
		if (!article?.user_article_id) return;
		try {
			await api.markUnread(article.user_article_id);
			isRead = false;
			toast.info('Marked unread');
		} catch {
			toast.error('Could not mark unread');
		}
	}
</script>

<div class="reader">
	<div class="reader__toolbar">
		<a href={backHref} class="reader__back">← Back to feed</a>
		{#if article?.user_article_id && isRead}
			<button type="button" class="btn-ghost btn-sm" onclick={markUnread}>Mark unread</button>
		{/if}
	</div>

	{#if loading}
		<p class="loading-pulse">Opening story</p>
	{:else if error}
		<div class="card animate-in">
			<p class="error">{error}</p>
			<a href={backHref} class="btn-secondary" style="margin-top: 1rem; display: inline-flex">Back to feed</a>
		</div>
	{:else if article}
		<article class="reader__sheet card animate-in">
			<header class="reader__header">
				<p class="reader__source">{article.feed_title}</p>
				<h1 class="reader__title">{article.title}</h1>
				<a
					href={article.url}
					target="_blank"
					rel="noopener noreferrer"
					class="btn-secondary btn-sm reader__external"
				>
					Open on source site ↗
				</a>
			</header>
			{#if safeHtml}
				<div class="article-content reader__body scrollbar-desk scrollbar-desk--inset">
					{@html safeHtml}
				</div>
			{:else}
				<div class="reader__fallback">
					<p>We couldn't pull the full text for this one.</p>
					<a href={article.url} target="_blank" rel="noopener noreferrer" class="btn">
						Open original article
					</a>
				</div>
			{/if}
		</article>
	{/if}
</div>

<style>
	.reader__toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}
</style>
