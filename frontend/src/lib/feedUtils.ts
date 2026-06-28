import type { ArticleSummary, DailyFeed, TopicFeedGroup } from '$lib/api';

export interface FlatFeedArticle extends ArticleSummary {
	topic_name: string;
	channel_index: number;
}

/** Flatten topic groups into a single timeline for the reels feed. */
export function flattenFeed(feed: DailyFeed | TopicFeedGroup[]): FlatFeedArticle[] {
	const groups = Array.isArray(feed) ? feed : feed.groups;
	const timeline = Array.isArray(feed) ? undefined : feed.timeline;

	if (timeline && timeline.length > 0) {
		const topicIndex = new Map(groups.map((g, i) => [g.topic_id, i]));
		const topicNames = new Map(groups.map((g) => [g.topic_id, g.topic_name]));
		return timeline.map((article) => {
			const group = groups.find((g) => g.articles.some((a) => a.user_article_id === article.user_article_id));
			const topicId = group?.topic_id ?? 0;
			return {
				...article,
				topic_name: group?.topic_name ?? 'News',
				channel_index: topicIndex.get(topicId) ?? 0
			};
		});
	}

	const flat = groups.flatMap((group, channel_index) =>
		group.articles.map((article) => ({
			...article,
			topic_name: group.topic_name,
			channel_index
		}))
	);
	return flat.sort((a, b) => {
		const ta = a.published_at ? new Date(a.published_at).getTime() : 0;
		const tb = b.published_at ? new Date(b.published_at).getTime() : 0;
		return tb - ta;
	});
}

export function stripHtml(html: string, max = 400): string {
	return html.replace(/<[^>]+>/g, '').trim().slice(0, max);
}

export function formatStoryTime(value: string | null): string {
	if (!value) return '';
	return new Date(value).toLocaleString(undefined, {
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	});
}
