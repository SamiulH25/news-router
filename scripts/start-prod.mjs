import { spawn, spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { printBanner } from './lib.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const docker = spawnSync('docker', ['info'], { stdio: 'ignore', shell: process.platform === 'win32' });
if (docker.status !== 0) {
	console.error('Docker is required for start:prod. Install Docker or use start:dev for local development.');
	process.exit(1);
}

printBanner();
console.log('Starting with Docker Compose...\n');

const child = spawn('docker', ['compose', '--profile', 'prod', 'up', '--build'], {
	cwd: root,
	stdio: 'inherit',
	shell: process.platform === 'win32'
});

child.on('exit', (code) => process.exit(code ?? 0));
