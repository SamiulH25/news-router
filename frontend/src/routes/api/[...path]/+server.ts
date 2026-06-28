import type { RequestHandler } from './$types';
import { getApiProxyDebugInfo, getApiProxyTarget } from '$lib/server/apiProxyTarget';

let loggedTarget = false;

/** Undici hides Set-Cookie on Response.headers — copy explicitly or auth cookies never reach the browser. */
function forwardResponseHeaders(source: Response): Headers {
	const headers = new Headers(source.headers);
	if (typeof source.headers.getSetCookie === 'function') {
		headers.delete('set-cookie');
		for (const cookie of source.headers.getSetCookie()) {
			headers.append('set-cookie', cookie);
		}
	}
	return headers;
}

const proxy: RequestHandler = async ({ request, params, url }) => {
	const backend = getApiProxyTarget();
	if (!loggedTarget) {
		const info = getApiProxyDebugInfo();
		console.log(
			`[api proxy] /api/* -> ${info.target}` +
				(info.exists ? '' : ' (warning: .dev-ports.json missing — run npm run start:dev)')
		);
		loggedTarget = true;
	}
	const path = params.path ?? '';
	const target = `${backend}/api/${path}${url.search}`;

	const headers = new Headers(request.headers);
	headers.delete('host');
	headers.delete('connection');

	const hasBody = request.method !== 'GET' && request.method !== 'HEAD';
	const body = hasBody ? await request.arrayBuffer() : undefined;

	try {
		const response = await fetch(target, {
			method: request.method,
			headers,
			body: hasBody ? body : undefined
		});

		return new Response(response.body, {
			status: response.status,
			statusText: response.statusText,
			headers: forwardResponseHeaders(response)
		});
	} catch (err) {
		console.error(`[api proxy] ${request.method} /api/${path} -> ${target}`, err);
		return new Response(
			JSON.stringify({
				detail: `API server unreachable at ${backend}. Run npm run start:dev from the project root.`
			}),
			{ status: 502, headers: { 'content-type': 'application/json' } }
		);
	}
};

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
