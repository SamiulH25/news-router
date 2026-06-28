import { stripHtml } from '$lib/feedUtils';

export type ArticleChunkKind = 'heading' | 'paragraph' | 'list';

export interface ArticleChunk {
	id: string;
	kind: ArticleChunkKind;
	html: string;
	preview: string;
}

const BLOCK_SELECTOR = 'p, h2, h3, h4, li, blockquote';
const MIN_CHUNK_LEN = 28;
const MAX_CHUNKS = 32;

function chunkKind(tagName: string): ArticleChunkKind {
	if (tagName === 'LI') return 'list';
	if (/^H[2-4]$/.test(tagName)) return 'heading';
	return 'paragraph';
}

function pushChunk(chunks: ArticleChunk[], el: Element, idx: number): number {
	const text = (el.textContent ?? '').replace(/\s+/g, ' ').trim();
	if (text.length < MIN_CHUNK_LEN) return idx;
	chunks.push({
		id: `chunk-${idx}`,
		kind: chunkKind(el.tagName),
		html: el.outerHTML,
		preview: text
	});
	return idx + 1;
}

/** Split article HTML into readable bubbles for the reels overlay. */
export function parseArticleChunks(html: string): ArticleChunk[] {
	if (!html?.trim()) return [];

	if (typeof DOMParser !== 'undefined') {
		const doc = new DOMParser().parseFromString(html, 'text/html');
		const blocks = doc.body.querySelectorAll(BLOCK_SELECTOR);
		const chunks: ArticleChunk[] = [];
		let idx = 0;
		for (const el of blocks) {
			idx = pushChunk(chunks, el, idx);
		}
		if (chunks.length > 0) return chunks.slice(0, MAX_CHUNKS);
	}

	const fallback = stripHtml(html, 50000);
	return textToChunks(fallback);
}

/** Turn plain summary text into sentence-sized bubbles. */
export function textToChunks(text: string): ArticleChunk[] {
	const cleaned = text.replace(/\s+/g, ' ').trim();
	if (!cleaned) return [];

	const parts =
		cleaned.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g)?.map((part) => part.trim()).filter(Boolean) ??
		[cleaned];

	if (parts.length === 1) {
		return [
			{
				id: 'chunk-0',
				kind: 'paragraph',
				html: `<p>${cleaned}</p>`,
				preview: cleaned
			}
		];
	}

	return parts.slice(0, MAX_CHUNKS).map((part, i) => ({
		id: `chunk-${i}`,
		kind: 'paragraph' as const,
		html: `<p>${part}</p>`,
		preview: part
	}));
}
