import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { env } from '$env/dynamic/private';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const portsFile = resolve(repoRoot, '.dev-ports.json');

/** Resolve the backend URL — prefers .dev-ports.json written by npm run start:dev. */
export function getApiProxyTarget(): string {
	if (existsSync(portsFile)) {
		try {
			const data = JSON.parse(readFileSync(portsFile, 'utf-8')) as { apiUrl?: string };
			if (data.apiUrl) {
				return data.apiUrl;
			}
		} catch {
			// fall through
		}
	}
	return env.API_PROXY_TARGET || 'http://127.0.0.1:8000';
}

/** For debugging — which port file was read. */
export function getApiProxyDebugInfo(): { target: string; portsFile: string; exists: boolean } {
	return {
		target: getApiProxyTarget(),
		portsFile,
		exists: existsSync(portsFile)
	};
}
