<script lang="ts">
	import SwipeCard from './SwipeCard.svelte';
	import type { FlatFeedArticle } from '$lib/feedUtils';

	let {
		articles,
		totalUnread,
		todayLabel,
		editionLabel = '',
		polling = false,
		onRefresh,
		onSearch,
		onToggleView
	}: {
		articles: FlatFeedArticle[];
		totalUnread: number;
		todayLabel: string;
		editionLabel?: string;
		polling?: boolean;
		onRefresh: () => void;
		onSearch?: () => void;
		onToggleView?: () => void;
	} = $props();

	let container = $state<HTMLElement | null>(null);
	let activeIndex = $state(0);
	let readingOpen = $state(false);

	function channelColor(index: number): string {
		return `var(--channel-${index % 4})`;
	}

	function scrollToIndex(index: number) {
		if (!container) return;
		const slides = container.querySelectorAll('.reel');
		slides[index]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowDown' || e.key === 'j') {
			e.preventDefault();
			scrollToIndex(Math.min(activeIndex + 1, articles.length - 1));
		} else if (e.key === 'ArrowUp' || e.key === 'k') {
			e.preventDefault();
			scrollToIndex(Math.max(activeIndex - 1, 0));
		}
	}

	$effect(() => {
		const el = container;
		if (!el) return;

		const slides = el.querySelectorAll('.reel');
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting && entry.intersectionRatio >= 0.55) {
						const idx = Number((entry.target as HTMLElement).dataset.index);
						if (!Number.isNaN(idx)) activeIndex = idx;
					}
				}
			},
			{ root: el, threshold: [0.55] }
		);

		slides.forEach((slide) => observer.observe(slide));
		return () => observer.disconnect();
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="reels-shell">
	<header class="reels-chrome" class:reels-chrome--hidden={readingOpen}>
		<div class="reels-chrome__left">
			<a href="/" class="reels-chrome__home">← Home</a>
			<p class="reels-chrome__edition">{todayLabel}{#if editionLabel} · {editionLabel}{/if}</p>
		</div>
		<div class="reels-chrome__right">
			{#if totalUnread > 0}
				<span class="reels-chrome__unread">{totalUnread} unread</span>
			{/if}
			{#if onSearch}
				<button class="btn-secondary btn-sm" onclick={onSearch}>Search</button>
			{/if}
			{#if onToggleView}
				<button class="btn-secondary btn-sm" onclick={onToggleView}>List</button>
			{/if}
			<button class="btn-secondary btn-sm" onclick={onRefresh} disabled={polling}>
				{polling ? '…' : 'Pull latest'}
			</button>
			<a href="/settings" class="reels-chrome__settings" aria-label="Settings">⚙</a>
		</div>
	</header>

	<div class="reels scrollbar-desk" bind:this={container} role="feed" aria-label="Today's stories">
		{#each articles as article, i (article.user_article_id)}
			<SwipeCard
				{article}
				index={i}
				total={articles.length}
				channelColor={channelColor(article.channel_index)}
				isActive={i === activeIndex}
				onReadingChange={(open) => {
					if (open) readingOpen = true;
					else if (i === activeIndex) readingOpen = false;
				}}
			/>
		{/each}
	</div>
</div>

<style>
	.reels-shell {
		position: relative;
		height: 100dvh;
		overflow: hidden;
		background: var(--ink);
	}

	.reels-chrome {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.75rem 1rem;
		background: var(--ink);
		border-bottom: 1px solid var(--rule);
		box-shadow: 0 8px 24px rgba(8, 9, 12, 0.65);
		transition:
			opacity var(--duration-normal) var(--ease-out),
			transform var(--duration-normal) var(--ease-out);
	}

	.reels-chrome--hidden {
		opacity: 0;
		pointer-events: none;
		transform: translateY(-100%);
	}

	.reels-chrome__left {
		min-width: 0;
	}

	.reels-chrome__home {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--route);
		text-decoration: none;
		transition: color var(--duration-fast) var(--ease-out);
	}

	.reels-chrome__home:hover {
		color: var(--press-bright);
	}

	.reels-chrome__edition {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--chalk-muted);
		margin: 0.25rem 0 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.reels-chrome__right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.reels-chrome__unread {
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		padding: 0.2rem 0.5rem;
		border-radius: 999px;
		background: var(--press-dim);
		color: var(--press-bright);
		border: 1px solid rgba(232, 163, 23, 0.2);
	}

	.reels-chrome__settings {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		border-radius: var(--radius-sm);
		color: var(--chalk-muted);
		text-decoration: none;
		font-size: 1rem;
		transition:
			color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.reels-chrome__settings:hover {
		color: var(--chalk);
		background: var(--ink-soft);
	}

	.reels {
		height: 100dvh;
		overflow-y: auto;
		scroll-snap-type: y mandatory;
		scroll-behavior: smooth;
		-webkit-overflow-scrolling: touch;
		overscroll-behavior-y: contain;
		padding-top: 3.75rem;
		scrollbar-gutter: stable;
	}

	.reels > :global(.reel) {
		scroll-snap-align: start;
	}

	@media (max-width: 540px) {
		.reels-chrome {
			padding: 0.5rem 0.75rem;
			gap: 0.5rem;
		}

		.reels-chrome__right {
			gap: 0.375rem;
		}

		.reels-chrome__unread {
			display: none;
		}

		.reels {
			padding-top: 3.25rem;
		}
	}
</style>
