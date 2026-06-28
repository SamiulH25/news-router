<script lang="ts">
	import type { PollResponse } from '$lib/api';

	let {
		result,
		onClose
	}: {
		result: PollResponse;
		onClose: () => void;
	} = $props();

	const hasErrors = $derived(
		result.feeds.some((f) => f.error || f.url_results.some((u) => u.error))
	);

	const feedCount = $derived(result.feeds.length);
	const okCount = $derived(
		result.feeds.filter((f) => !f.error && !f.url_results.some((u) => u.error)).length
	);

	function urlLabel(url: string): string {
		try {
			const u = new URL(url);
			const path = u.pathname === '/' ? '' : u.pathname;
			const full = `${u.hostname}${path}`;
			return full.length > 48 ? `${full.slice(0, 45)}…` : full;
		} catch {
			return url.length > 48 ? `${url.slice(0, 45)}…` : url;
		}
	}
</script>

<div class="poll-scrim" role="presentation" onclick={onClose}></div>
<div class="poll-report card" role="dialog" aria-labelledby="poll-title" aria-modal="true">
	<header class="poll-report__head">
		<div class="poll-report__summary">
			<p class="eyebrow">Pull report</p>
			<h2 id="poll-title" class="poll-report__title">
				{result.new_articles} new stor{result.new_articles === 1 ? 'y' : 'ies'}
			</h2>
			<p class="poll-report__meta">
				{#if result.edition_stories != null}
					{result.edition_stories} in edition ·
				{/if}
				{okCount}/{feedCount} source{feedCount === 1 ? '' : 's'} OK
			</p>
		</div>
		<button type="button" class="poll-report__close btn-ghost btn-sm" onclick={onClose}>Close</button>
	</header>

	{#if hasErrors}
		<p class="poll-report__warn">Some sources had problems — details below.</p>
	{/if}

	<div class="poll-report__body">
		<ul class="poll-report__list">
			{#each result.feeds as feed (feed.feed_id)}
				<li
					class="poll-report__item"
					class:poll-report__item--error={feed.error || feed.url_results.some((u) => u.error)}
				>
					<div class="poll-report__item-head">
						<strong class="poll-report__feed-name">{feed.feed_title}</strong>
						<span class="poll-report__stat">
							{feed.new_articles} new · {feed.routed_to_topics} routed
						</span>
					</div>
					{#if feed.topics.length > 0}
						<p class="poll-report__topics">{feed.topics.join(' · ')}</p>
					{/if}
					{#if feed.error}
						<p class="poll-report__error">{feed.error}</p>
					{/if}

					{#if feed.url_results.length > 0}
						<ul class="poll-report__urls">
							{#each feed.url_results as url (url.url)}
								<li class="poll-report__url" class:poll-report__url--error={url.error}>
									<span class="poll-report__url-label" title={url.url}>{urlLabel(url.url)}</span>
									{#if url.error}
										<span class="poll-report__url-detail poll-report__url-detail--error">{url.error}</span>
									{:else}
										<span class="poll-report__url-detail">
											{url.entries_in_feed} in feed · {url.new_articles} new · {url.routed_to_topics} routed
										</span>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	.poll-scrim {
		position: fixed;
		inset: 0;
		z-index: 120;
		background: var(--scrim);
	}

	.poll-report {
		position: fixed;
		z-index: 121;
		display: flex;
		flex-direction: column;
		inset: auto 0 0;
		width: 100%;
		max-height: min(92dvh, 40rem);
		border-radius: var(--radius-lg) var(--radius-lg) 0 0;
		padding: 0;
		overflow: hidden;
	}

	.poll-report__head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 1rem 1rem 0.875rem;
		padding-top: max(1rem, env(safe-area-inset-top));
		border-bottom: 1px solid var(--rule);
		flex-shrink: 0;
		background: var(--ink-raised);
	}

	.poll-report__summary {
		min-width: 0;
		flex: 1;
	}

	.poll-report__close {
		flex-shrink: 0;
	}

	.poll-report__title {
		font-family: var(--font-display);
		font-size: 1.125rem;
		font-weight: 700;
		line-height: 1.25;
		margin: 0.2rem 0 0;
		color: var(--chalk);
	}

	.poll-report__meta {
		margin: 0.35rem 0 0;
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.04em;
		color: var(--chalk-muted);
	}

	.poll-report__warn {
		margin: 0;
		padding: 0.625rem 1rem;
		font-size: 0.8125rem;
		line-height: 1.45;
		color: var(--press-bright);
		background: color-mix(in srgb, var(--press) 8%, var(--ink-soft));
		border-bottom: 1px solid var(--rule);
		flex-shrink: 0;
	}

	.poll-report__body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		-webkit-overflow-scrolling: touch;
		overscroll-behavior: contain;
		padding: 0.75rem 1rem max(1rem, env(safe-area-inset-bottom));
	}

	.poll-report__list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}

	.poll-report__item {
		padding: 0.75rem 0.875rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--rule);
		background: var(--ink-soft);
	}

	.poll-report__item--error {
		border-color: color-mix(in srgb, var(--danger) 40%, var(--rule));
	}

	.poll-report__item-head {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 0.25rem;
	}

	.poll-report__feed-name {
		color: var(--chalk);
		font-size: 0.9375rem;
		line-height: 1.35;
	}

	.poll-report__stat {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		color: var(--chalk-muted);
	}

	.poll-report__topics {
		margin: 0.375rem 0 0;
		font-size: 0.75rem;
		line-height: 1.45;
		color: var(--chalk-muted);
	}

	.poll-report__error {
		margin: 0.5rem 0 0;
		font-size: 0.8125rem;
		line-height: 1.45;
		color: var(--danger);
		word-break: break-word;
	}

	.poll-report__urls {
		list-style: none;
		padding: 0;
		margin: 0.625rem 0 0;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		border-top: 1px solid var(--rule);
		padding-top: 0.625rem;
	}

	.poll-report__url {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.5rem 0.625rem;
		border-radius: var(--radius-sm);
		background: var(--ink);
	}

	.poll-report__url--error {
		background: color-mix(in srgb, var(--danger) 6%, var(--ink));
	}

	.poll-report__url-label {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		line-height: 1.4;
		color: var(--route);
		word-break: break-all;
	}

	.poll-report__url-detail {
		font-size: 0.75rem;
		line-height: 1.45;
		color: var(--chalk-muted);
	}

	.poll-report__url-detail--error {
		color: var(--danger);
		word-break: break-word;
	}

	@media (min-width: 540px) {
		.poll-report {
			inset: 50% auto auto 50%;
			transform: translate(-50%, -50%);
			width: min(36rem, calc(100vw - 2rem));
			max-height: min(85dvh, 36rem);
			border-radius: var(--radius-lg);
		}

		.poll-report__head {
			padding: 1.25rem 1.5rem 1rem;
			padding-top: 1.25rem;
			border-radius: var(--radius-lg) var(--radius-lg) 0 0;
		}

		.poll-report__body {
			padding: 0.75rem 1.5rem 1.25rem;
		}

		.poll-report__title {
			font-size: 1.25rem;
		}

		.poll-report__item-head {
			flex-direction: row;
			flex-wrap: wrap;
			align-items: baseline;
			justify-content: space-between;
		}

		.poll-report__url {
			flex-direction: row;
			align-items: baseline;
			justify-content: space-between;
			gap: 0.75rem;
		}

		.poll-report__url-label {
			flex: 1;
			min-width: 0;
		}

		.poll-report__url-detail {
			flex-shrink: 0;
			text-align: right;
			max-width: 55%;
		}
	}
</style>
