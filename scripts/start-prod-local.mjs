import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import {
	allocateDevPorts,
	apiEnv,
	backend,
	buildAccessUrls,
	frontend,
	getPython,
	isWin,
	printBanner,
	run,
	setup,
	startNtfy,
	waitForApi,
	writeDevPorts
} from './lib.mjs';

setup();
startNtfy();

const { apiPort, webPort } = await allocateDevPorts();
writeDevPorts({ apiPort, webPort });

console.log('Building frontend for production...');
run(isWin ? 'npm.cmd' : 'npm', ['run', 'build'], { cwd: frontend, shell: isWin });

const buildEntry = path.join(frontend, 'build', 'index.js');
if (!existsSync(buildEntry)) {
	console.error('Frontend build failed — expected', buildEntry);
	process.exit(1);
}

printBanner({ apiPort, webPort });
console.log('Running production build (local). Press Ctrl+C to stop.\n');

const python = getPython();
const apiProxyTarget = buildAccessUrls({ apiPort, webPort }).api.loopback;

const api = spawn(
	python,
	['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(apiPort)],
	{
		cwd: backend,
		env: apiEnv({ apiPort, webPort }),
		stdio: 'inherit',
		shell: isWin
	}
);

const ready = await waitForApi(apiPort);
if (!ready) {
	console.error(`API did not become ready on ${apiProxyTarget}`);
	api.kill('SIGTERM');
	process.exit(1);
}

const web = spawn('node', ['build'], {
	cwd: frontend,
	env: {
		...process.env,
		HOST: '0.0.0.0',
		PORT: String(webPort),
		API_PROXY_TARGET: apiProxyTarget
	},
	stdio: 'inherit',
	shell: isWin
});

function shutdown(code = 0) {
	api.kill('SIGTERM');
	web.kill('SIGTERM');
	process.exit(code);
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

api.on('exit', (code) => {
	if (code && code !== 0) shutdown(code);
});
web.on('exit', (code) => {
	if (code && code !== 0) shutdown(code);
});
