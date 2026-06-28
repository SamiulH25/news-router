const API_BASE = typeof window !== 'undefined' ? '' : process.env.PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
	status: number;
	constructor(message: string, status: number) {
		super(message);
		this.status = status;
	}
}

async function request<T>(path: string, options: RequestInit = {}, timeoutMs = 30000): Promise<T> {
	const url = `${API_BASE}${path}`;
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);
	try {
		const response = await fetch(url, {
			...options,
			signal: controller.signal,
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
				...(options.headers || {})
			}
		});
		if (!response.ok) {
			let detail = 'Request failed';
			try {
				const body = await response.json();
				detail = body.detail || detail;
			} catch {
				// ignore
			}
			throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status);
		}
		if (response.status === 204) return undefined as T;
		return response.json();
	} catch (err) {
		if (err instanceof Error && err.name === 'AbortError') {
			throw new ApiError('Request timed out — try again or paste a direct RSS link', 408);
		}
		throw err;
	} finally {
		clearTimeout(timer);
	}
}

export interface User {
	id: number;
	username: string;
	is_admin: boolean;
	ntfy_topic: string | null;
	digest_hour: number;
	digest_minute: number;
	digest_evening_hour: number;
	digest_evening_minute: number;
	timezone: string;
	feed_window_hours: number;
	onboarded: boolean;
	personalized_feed: boolean;
}

export interface Feed {
	id: number;
	url: string;
	title: string;
	favicon_url: string | null;
	site_url: string | null;
	last_fetched_at: string | null;
	last_successful_fetch: string | null;
	last_error: string | null;
	topic_ids: number[];
	is_subscribed: boolean;
}

export interface Topic {
	id: number;
	name: string;
	keywords: string;
	exclude_keywords: string;
	feed_ids: number[];
}

export interface ArticleSummary {
	id: number;
	user_article_id: number;
	title: string;
	url: string;
	summary: string | null;
	image_url: string | null;
	published_at: string | null;
	is_read: boolean;
	feed_title: string;
	feed_id: number;
	favicon_url: string | null;
	surfaced_at?: string | null;
	archived_at?: string | null;
	cluster_key?: string | null;
	rank_score?: number | null;
}

export interface TopicFeedGroup {
	topic_id: number;
	topic_name: string;
	articles: ArticleSummary[];
	unread_count: number;
}

export interface DailyFeed {
	groups: TopicFeedGroup[];
	total_unread: number;
	edition_fetched_at?: string | null;
	personalized?: boolean;
	timeline?: ArticleSummary[];
}

export interface ArticleRead {
	id: number;
	user_article_id?: number | null;
	title: string;
	url: string;
	content_html: string | null;
	image_url: string | null;
	feed_title: string;
}

export interface AdminUser {
	id: number;
	username: string;
	is_admin: boolean;
	onboarded: boolean;
	created_at: string | null;
}

export interface PollResponse {
	new_articles: number;
	edition_stories?: number | null;
	feeds: Array<{
		feed_id: number;
		feed_title: string;
		topics: string[];
		poll_urls: string[];
		new_articles: number;
		routed_to_topics: number;
		error: string | null;
		url_results: Array<{
			url: string;
			entries_in_feed: number;
			new_articles: number;
			routed_to_topics: number;
			error?: string;
		}>;
	}>;
}

export interface DefaultOutlet {
	title: string;
	region: string;
	url: string;
}

export interface CatalogOutlet {
	url: string;
	title: string;
	language: string;
	default_selected: boolean;
}

export interface CatalogCountry {
	code: string;
	name: string;
	outlets: CatalogOutlet[];
}

export interface OnboardingCatalog {
	countries: CatalogCountry[];
	default_selected_urls: string[];
}

export const api = {
	authConfig: () => request<{ allow_registration: boolean }>('/api/auth/config'),
	register: (username: string, password: string) =>
		request<User>('/api/auth/register', { method: 'POST', body: JSON.stringify({ username, password }) }),
	login: (username: string, password: string) =>
		request<User>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
	logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
	me: () => request<User>('/api/auth/me'),
	changePassword: (current_password: string, new_password: string) =>
		request('/api/auth/change-password', {
			method: 'POST',
			body: JSON.stringify({ current_password, new_password })
		}),
	getFeeds: () => request<Feed[]>('/api/feeds'),
	previewFeed: (url: string) =>
		request<{ feed_url: string; title: string; site_url: string | null; input_url: string; sections: string[] }>(
			'/api/feeds/preview',
			{ method: 'POST', body: JSON.stringify({ url }) },
			45000
		),
	createFeed: (data: { url: string; topic_ids?: number[] }) =>
		request<Feed>('/api/feeds', { method: 'POST', body: JSON.stringify(data) }),
	updateFeed: (id: number, data: { title?: string; topic_ids?: number[] }) =>
		request<Feed>(`/api/feeds/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	deleteFeed: (id: number) => request(`/api/feeds/${id}`, { method: 'DELETE' }),
	getTopics: () => request<Topic[]>('/api/topics'),
	createTopic: (data: { name: string; keywords?: string; exclude_keywords?: string; feed_ids?: number[] }) =>
		request<Topic>('/api/topics', { method: 'POST', body: JSON.stringify(data) }),
	updateTopic: (
		id: number,
		data: { name?: string; keywords?: string; exclude_keywords?: string; feed_ids?: number[] }
	) => request<Topic>(`/api/topics/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	deleteTopic: (id: number) => request(`/api/topics/${id}`, { method: 'DELETE' }),
	getDailyFeed: (opts?: { hours?: number; topicId?: number; q?: string }) => {
		const params = new URLSearchParams();
		if (opts?.hours != null) params.set('hours', String(opts.hours));
		if (opts?.topicId != null) params.set('topic_id', String(opts.topicId));
		if (opts?.q) params.set('q', opts.q);
		const qs = params.toString();
		return request<DailyFeed>(`/api/articles/feed${qs ? `?${qs}` : ''}`);
	},
	searchArticles: (q: string, includeArchived = false) =>
		request<DailyFeed>(
			`/api/articles/search?q=${encodeURIComponent(q)}&include_archived=${includeArchived ? 'true' : 'false'}`
		),
	getArchivedFeed: () => request<DailyFeed>('/api/articles/archive'),
	readArticle: (id: number) => request<ArticleRead>(`/api/articles/${id}/read`),
	markRead: (userArticleId: number) =>
		request(`/api/articles/user-articles/${userArticleId}/read`, { method: 'POST' }),
	markUnread: (userArticleId: number) =>
		request(`/api/articles/user-articles/${userArticleId}/unread`, { method: 'POST' }),
	engage: (userArticleId: number, data: { event: 'open' | 'less' }) =>
		request(`/api/articles/user-articles/${userArticleId}/engage`, {
			method: 'POST',
			body: JSON.stringify(data)
		}),
	updateSettings: (data: {
		digest_hour?: number;
		digest_minute?: number;
		digest_evening_hour?: number;
		digest_evening_minute?: number;
		timezone?: string;
		feed_window_hours?: number;
		onboarded?: boolean;
		personalized_feed?: boolean;
		regenerate_ntfy_topic?: boolean;
	}) => request<User>('/api/settings', { method: 'PATCH', body: JSON.stringify(data) }),
	getOnboardingCatalog: () => request<OnboardingCatalog>('/api/onboarding/catalog'),
	getOnboardingDefaults: () => request<DefaultOutlet[]>('/api/onboarding/defaults'),
	completeOnboarding: (data: {
		timezone: string;
		topic_name: string;
		selected_outlet_urls?: string[];
		extra_feed_url?: string;
	}) => request<User>('/api/onboarding/complete', { method: 'POST', body: JSON.stringify(data) }),
	triggerPoll: () => request<PollResponse>('/api/digest/poll', { method: 'POST' }),
	pollFeed: (id: number) =>
		request<{
			feed_id: number;
			feed_title: string;
			new_articles: number;
			routed_to_topics: number;
			error: string | null;
			url_results: PollResponse['feeds'][0]['url_results'];
		}>(`/api/feeds/${id}/poll`, { method: 'POST' }),
	testNotify: () => request<{ sent: boolean }>('/api/digest/notify-me', { method: 'POST' }),
	listAdminUsers: () => request<AdminUser[]>('/api/admin/users'),
	patchAdminUser: (id: number, data: { is_admin?: boolean }) =>
		request<AdminUser>(`/api/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	exportOpml: async () => {
		const response = await fetch(`${API_BASE}/api/opml/export`, { credentials: 'include' });
		if (!response.ok) throw new ApiError('Export failed', response.status);
		return response.blob();
	},
	importOpml: async (file: File, topicId?: number) => {
		const form = new FormData();
		form.append('file', file);
		const qs = topicId ? `?topic_id=${topicId}` : '';
		const response = await fetch(`${API_BASE}/api/opml/import${qs}`, {
			method: 'POST',
			credentials: 'include',
			body: form
		});
		if (!response.ok) {
			const body = await response.json().catch(() => ({}));
			throw new ApiError(body.detail || 'Import failed', response.status);
		}
		return response.json() as Promise<{ imported: number }>;
	}
};
