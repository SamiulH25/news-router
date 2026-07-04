<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { parseArticleChunks, textToChunks, type ArticleChunk } from '$lib/articleChunks';
	import { formatStoryTime, stripHtml, type FlatFeedArticle } from '$lib/feedUtils';
	import { toast } from '$lib/toast.svelte';

	let {
		article,
		index,
		total,
		channelColor,
		isActive = false,
		onReadingChange
	}: {
		article: FlatFeedArticle;
		index: number;
		total: number;
		channelColor: string;
		isActive?: boolean;
		onReadingChange?: (reading: boolean) => void;
	} = $props();

	let contentHtml = $state<string | null>(null);
	let fetchedHeroImage = $state<string | null>(null);
	let imageFailed = $state(false);
	let loadingContent = $state(false);
	let loadFailed = $state(false);
	let readOverride = $state<boolean | undefined>(undefined);
	let lessSent = $state(false);
	let bubblesOpen = $state(false);
	let loadTimer: ReturnType<typeof setTimeout> | undefined;

	const heroImage = $derived(fetchedHeroImage ?? article.image_url ?? null);
	const isRead = $derived(readOverride ?? article.is_read);

	const summaryText = $derived(article.summary ? stripHtml(article.summary, 8000) : '');

	const showHero = $derived(Boolean(heroImage) && !imageFailed);

	const chunks = $derived.by((): ArticleChunk[] => {
		if (contentHtml) return parseArticleChunks(contentHtml);
		if (summaryText) return textToChunks(summaryText);
		return [];
	});

	const canOpenBubbles = $derived(chunks.length > 0 && !loadingContent);

	function recordOpen() {
		if (isRead) return;
		readOverride = true;
		api.engage(article.user_article_id, { event: 'open' }).catch(() => {
			toast.error('Could not save that you opened this story');
		});
	}

	function openBubbles() {
		if (!canOpenBubbles) return;
		bubblesOpen = true;
		onReadingChange?.(true);
		recordOpen();
	}

	function closeBubbles() {
		if (!bubblesOpen) return;
		bubblesOpen = false;
		onReadingChange?.(false);
	}

	function readHere() {
		recordOpen();
		goto(`/read/${article.id}`);
	}

	async function recordLess() {
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

	$effect(() => {
		article.user_article_id;
		readOverride = undefined;
		fetchedHeroImage = null;
		contentHtml = null;
		loadFailed = false;
		loadingContent = false;
		imageFailed = false;
	});

	$effect(() => {
		if (!isActive) {
			if (loadTimer) clearTimeout(loadTimer);
			if (bubblesOpen) {
				bubblesOpen = false;
				onReadingChange?.(false);
			}
			return;
		}

		if (contentHtml !== null || loadingContent || loadFailed) return;

		loadTimer = setTimeout(() => {
			loadingContent = true;
			api
				.readArticle(article.id)
				.then((full) => {
					contentHtml = full.content_html;
					if (full.image_url) {
						fetchedHeroImage = full.image_url;
					}
				})
				.catch(() => {
					loadFailed = true;
				})
				.finally(() => {
					loadingContent = false;
				});
		}, 350);

		return () => {
			if (loadTimer) clearTimeout(loadTimer);
		};
	});
</script>

<article
	class="reel"
	class:reel--unread={!isRead}
	class:reel--bubbles={bubblesOpen}
	style="--channel-color: {channelColor}"
	data-index={index}
	aria-label="Story {index + 1} of {total}: {article.title}"
>
	<div class="reel__stripe" aria-hidden="true"></div>

	<div class="reel__stage" class:reel__stage--no-image={!showHero}>
		{#if showHero}
			<img
				class="reel__hero-img"
				src={heroImage}
				alt=""
				loading={index <= 1 ? 'eager' : 'lazy'}
				decoding="async"
				referrerpolicy="no-referrer"
				onerror={() => (imageFailed = true)}
			/>
		{/if}
		<div class="reel__stage-shade" aria-hidden="true"></div>

		<div class="reel__cover">
			<header class="reel__meta">
				<span class="reel__topic">{article.topic_name}</span>
				<span class="reel__dot" aria-hidden="true">·</span>
				{#if article.favicon_url}
					<img src={article.favicon_url} alt="" class="reel__favicon" />
				{/if}
				<span class="reel__source">{article.feed_title}</span>
				{#if article.published_at}
					<span class="reel__time">{formatStoryTime(article.published_at)}</span>
				{/if}
			</header>

			<h2 class="reel__title">{article.title}</h2>

			{#if !bubblesOpen}
				{#if loadingContent}
					<p class="reel__hint-line">Loading story…</p>
				{:else if loadFailed && !summaryText}
					<p class="reel__hint-line reel__hint-line--muted">Couldn't load the full story.</p>
				{:else if canOpenBubbles}
					<button type="button" class="reel__tap" onclick={openBubbles}>
						Tap to read in parts
						<span class="reel__tap-count">{chunks.length} sections</span>
					</button>
				{:else if summaryText}
					<button type="button" class="reel__tap" onclick={openBubbles}>Tap to read summary</button>
				{/if}
			{/if}
		</div>
	</div>

	{#if bubblesOpen}
		<div class="reel__bubble-layer" role="dialog" aria-label="Story sections">
			<button
				type="button"
				class="reel__bubble-dismiss"
				onclick={closeBubbles}
				aria-label="Close story sections"
			>
				×
			</button>

			<div class="reel__bubble-scroll scrollbar-desk">
				<div class="reel__bubble-grid">
					{#each chunks as chunk, i (chunk.id)}
						<article
							class="reel__bubble"
							class:reel__bubble--heading={chunk.kind === 'heading'}
							style="--bubble-i: {i}"
						>
							{#if chunk.kind === 'heading'}
								<span class="reel__bubble-kicker">Section</span>
							{/if}
							<div class="reel__bubble-body article-content">{@html chunk.html}</div>
						</article>
					{/each}
				</div>
			</div>
		</div>
	{/if}

	<div class="reel__links" class:reel__links--hidden={bubblesOpen}>
		<button type="button" class="reel__read-here" onclick={readHere}>Read full story</button>
		<a
			href={article.url}
			target="_blank"
			rel="noopener noreferrer"
			class="reel__external"
			onclick={recordOpen}
		>
			Open on {article.feed_title} ↗
		</a>
	</div>

	<footer class="reel__footer" class:reel__footer--hidden={bubblesOpen}>
		<button type="button" class="reel__less" disabled={lessSent} onclick={recordLess}>
			{lessSent ? 'Noted' : 'Less like this'}
		</button>
		<span class="reel__counter">{index + 1} / {total}</span>
		{#if index < total - 1}
			<span class="reel__hint">Swipe up for next</span>
		{:else}
			<span class="reel__hint">You're caught up</span>
		{/if}
	</footer>
</article>

<style>
	.reel {
		position: relative;
		min-height: 100dvh;
		height: 100dvh;
		scroll-snap-align: start;
		scroll-snap-stop: always;
		display: flex;
		flex-direction: column;
		background: var(--ink);
		overflow: hidden;
	}

	.reel__stripe {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		width: 3px;
		background: var(--channel-color);
		box-shadow: 0 0 12px color-mix(in srgb, var(--channel-color) 50%, transparent);
		z-index: 3;
	}

	.reel__stage {
		position: relative;
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		overflow: hidden;
		background: var(--ink-soft);
	}

	.reel__stage--no-image {
		background:
			linear-gradient(165deg, color-mix(in srgb, var(--channel-color) 18%, var(--ink)) 0%, var(--ink) 55%),
			var(--ink);
	}

	.reel__hero-img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: center top;
		display: block;
	}

	.reel__stage-shade {
		position: absolute;
		inset: 0;
		background: linear-gradient(
			180deg,
			rgba(8, 9, 12, 0.15) 0%,
			rgba(8, 9, 12, 0.35) 35%,
			rgba(8, 9, 12, 0.92) 72%,
			var(--ink) 100%
		);
		pointer-events: none;
	}

	.reel__cover {
		position: relative;
		z-index: 1;
		padding: 3.5rem 1.25rem 1rem 1.75rem;
	}

	.reel__meta {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.375rem 0.5rem;
		margin-bottom: 0.75rem;
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.reel__topic {
		color: var(--channel-color);
	}

	.reel__dot {
		opacity: 0.4;
	}

	.reel__favicon {
		width: 14px;
		height: 14px;
		border-radius: 2px;
	}

	.reel__source {
		color: var(--chalk-muted);
	}

	.reel__time {
		margin-left: auto;
		color: var(--chalk-muted);
		text-transform: none;
		letter-spacing: 0;
		font-size: 0.75rem;
	}

	.reel__title {
		font-family: var(--font-display);
		font-size: clamp(1.375rem, 4.5vw, 2rem);
		font-weight: 700;
		line-height: 1.15;
		letter-spacing: -0.02em;
		color: var(--chalk);
		margin: 0;
		text-shadow: 0 2px 24px rgba(8, 9, 12, 0.65);
	}

	.reel__hint-line {
		margin: 0.875rem 0 0;
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		color: var(--chalk-muted);
		animation: pulse 1.4s ease-in-out infinite;
	}

	.reel__hint-line--muted {
		animation: none;
		font-style: italic;
	}

	.reel__tap {
		display: inline-flex;
		align-items: center;
		gap: 0.625rem;
		margin-top: 1rem;
		padding: 0.55rem 0.9rem;
		border-radius: 999px;
		border: 1px solid color-mix(in srgb, var(--channel-color) 45%, var(--rule));
		background: color-mix(in srgb, var(--channel-color) 12%, rgba(8, 9, 12, 0.55));
		backdrop-filter: blur(8px);
		color: var(--chalk);
		font-size: 0.8125rem;
		font-weight: 650;
		cursor: pointer;
		transition:
			transform var(--duration-fast) var(--ease-out),
			border-color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.reel__tap:hover {
		transform: translateY(-1px);
		border-color: var(--channel-color);
		background: color-mix(in srgb, var(--channel-color) 20%, rgba(8, 9, 12, 0.65));
	}

	.reel__tap-count {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--chalk-muted);
	}

	.reel__bubble-layer {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		flex-direction: column;
		background: rgba(8, 9, 12, 0.96);
		backdrop-filter: blur(12px);
		animation: bubble-layer-in var(--duration-normal) var(--ease-out) both;
	}

	.reel__bubble-dismiss {
		position: absolute;
		top: max(0.625rem, env(safe-area-inset-top));
		right: max(0.75rem, env(safe-area-inset-right));
		z-index: 2;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.25rem;
		height: 2.25rem;
		padding: 0;
		border-radius: 50%;
		border: 1px solid var(--rule);
		background: rgba(8, 9, 12, 0.72);
		backdrop-filter: blur(8px);
		color: var(--chalk-muted);
		font-size: 1.375rem;
		line-height: 1;
		cursor: pointer;
		transition:
			color var(--duration-fast) var(--ease-out),
			border-color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.reel__bubble-dismiss:hover {
		color: var(--chalk);
		border-color: var(--chalk-muted);
		background: rgba(8, 9, 12, 0.9);
	}

	.reel__bubble-scroll {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		-webkit-overflow-scrolling: touch;
		overscroll-behavior: contain;
		padding: max(3.25rem, calc(env(safe-area-inset-top) + 2.75rem)) 1rem max(1rem, env(safe-area-inset-bottom));
	}

	.reel__bubble-grid {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		max-width: min(36rem, 100%);
		margin: 0 auto;
		padding-bottom: 0.5rem;
	}

	.reel__bubble {
		position: relative;
		display: block;
		width: 100%;
		padding: 1rem 1.125rem;
		border-radius: 1.125rem;
		border: 1px solid var(--rule);
		background: var(--ink-raised);
		color: inherit;
		text-align: left;
		box-shadow: 0 8px 28px rgba(8, 9, 12, 0.35);
		animation: bubble-pop var(--duration-normal) var(--ease-snap) both;
		animation-delay: calc(var(--bubble-i, 0) * 45ms);
	}

	.reel__bubble--heading {
		border-color: color-mix(in srgb, var(--channel-color) 40%, var(--rule));
		background: color-mix(in srgb, var(--channel-color) 8%, var(--ink-raised));
	}

	.reel__bubble-kicker {
		display: block;
		margin-bottom: 0.35rem;
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--channel-color);
	}

	.reel__bubble-body {
		font-family: var(--font-read);
		font-size: 0.9375rem;
		line-height: 1.65;
		color: var(--chalk);
		overflow-wrap: anywhere;
		word-break: break-word;
	}

	.reel__bubble-body :global(p) {
		margin: 0 0 0.75rem;
	}

	.reel__bubble-body :global(p:last-child) {
		margin-bottom: 0;
	}

	.reel__bubble-body :global(a) {
		color: var(--route);
	}

	.reel__links {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem 1rem;
		padding: 0.75rem 1.25rem 0.25rem 1.75rem;
		flex-shrink: 0;
		z-index: 2;
		transition: opacity var(--duration-fast) var(--ease-out);
	}

	.reel__links--hidden,
	.reel__footer--hidden {
		opacity: 0;
		pointer-events: none;
	}

	.reel__read-here {
		padding: 0.5rem 0.875rem;
		border-radius: var(--radius-md);
		border: none;
		background: var(--press);
		color: var(--ink);
		font-size: 0.8125rem;
		font-weight: 700;
		cursor: pointer;
	}

	.reel__read-here:hover {
		background: var(--press-bright);
	}

	.reel__external {
		display: inline-flex;
		align-items: center;
		font-size: 0.8125rem;
		font-weight: 500;
		color: var(--route);
		text-decoration: none;
	}

	.reel__external:hover {
		color: var(--press-bright);
	}

	.reel__footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.625rem 1.25rem max(1rem, env(safe-area-inset-bottom)) 1.75rem;
		border-top: 1px solid var(--rule);
		flex-shrink: 0;
		z-index: 2;
	}

	.reel__less {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		padding: 0.35rem 0.625rem;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: transparent;
		color: var(--chalk-muted);
		cursor: pointer;
		flex-shrink: 0;
	}

	.reel__less:hover:not(:disabled) {
		border-color: var(--chalk-muted);
		color: var(--chalk);
	}

	.reel__less:disabled {
		opacity: 0.55;
		cursor: default;
	}

	.reel__counter {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.1em;
		color: var(--chalk-muted);
	}

	.reel__hint {
		font-size: 0.75rem;
		color: var(--chalk-muted);
		animation: nudge 2.5s ease-in-out infinite;
	}

	.reel--unread .reel__title::after {
		content: '';
		display: inline-block;
		width: 6px;
		height: 6px;
		margin-left: 0.5rem;
		border-radius: 50%;
		background: var(--press);
		box-shadow: 0 0 8px var(--press);
		vertical-align: middle;
	}

	.reel--bubbles .reel__cover {
		opacity: 0.35;
	}

	@keyframes bubble-layer-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes bubble-pop {
		from {
			opacity: 0;
			transform: translateY(10px) scale(0.96);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 0.5;
		}
		50% {
			opacity: 1;
		}
	}

	@keyframes nudge {
		0%,
		100% {
			transform: translateY(0);
			opacity: 0.6;
		}
		50% {
			transform: translateY(-3px);
			opacity: 1;
		}
	}

	@media (max-width: 540px) {
		.reel__cover {
			padding-top: 3rem;
		}

		.reel__hint {
			display: none;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.reel__hint,
		.reel__hint-line {
			animation: none;
		}

		.reel__bubble,
		.reel__bubble-layer {
			animation: none;
		}
	}
</style>
