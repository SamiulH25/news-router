import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		host: '0.0.0.0',
		port: 5173,
		strictPort: false,
		allowedHosts: true
		// /api/* is proxied by src/routes/api/[...path]/+server.ts (reads .dev-ports.json).
		// Do not add a Vite proxy here — it bypasses SvelteKit and often hits a stale port.
	},
});
