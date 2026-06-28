import { spawn } from 'node:child_process';
import path from 'node:path';
import {
	allocateDevPorts,
	apiEnv,
	backend,
	buildAccessUrls,
	checkFirewallRules,
	ensureWindowsFirewall,
	frontend,
	freeDevPorts,
	getPython,
	printBanner,
	probeLanWeb,
	setup,
	startNtfy,
	waitForApi,
	waitForWeb,
	writeDevPorts
} from './lib.mjs';

setup();
startNtfy();

console.log('Clearing leftover dev servers on default ports…');
freeDevPorts();

const { apiPort, webPort } = await allocateDevPorts();
const access = buildAccessUrls({ apiPort, webPort });
const apiProxyTarget = access.api.loopback;

ensureWindowsFirewall();
const firewallStatus = checkFirewallRules().ok;
printBanner({ apiPort, webPort, firewallOk: firewallStatus });
console.log('Starting API on 0.0.0.0…');

const python = getPython();
const api = spawn(
	python,
	['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(apiPort)],
	{
		cwd: backend,
		env: apiEnv({ apiPort, webPort }),
		stdio: 'inherit',
		shell: false
	}
);

const ready = await waitForApi(apiPort);
if (!ready) {
	console.error(`API did not become ready on ${apiProxyTarget} — check logs above.`);
	api.kill('SIGTERM');
	process.exit(1);
}

// Write port files only after API is confirmed up — frontend reads these on startup.
const portsFile = writeDevPorts({ apiPort, webPort });
console.log(`API ready on ${apiProxyTarget} (LAN: ${access.api.lan.join(', ') || 'none'})`);
console.log(`Ports saved to ${portsFile}`);
console.log(`Starting frontend on 0.0.0.0:${webPort} (proxy /api -> ${apiProxyTarget})…\n`);

const viteBin = path.join(frontend, 'node_modules', 'vite', 'bin', 'vite.js');
const web = spawn(
	process.execPath,
	[viteBin, 'dev', '--host', '0.0.0.0', '--port', String(webPort)],
	{
		cwd: frontend,
		env: { ...process.env, API_PROXY_TARGET: apiProxyTarget },
		stdio: 'inherit',
		shell: false
	}
);

const webReady = await waitForWeb(webPort);
if (!webReady) {
	console.error(`Frontend did not become ready on port ${webPort} — check logs above.`);
	shutdownEarly();
}

const lanProbe = access.primaryLan ? await probeLanWeb(webPort, access.primaryLan) : null;
printBanner({ apiPort, webPort, firewallOk: firewallStatus, lanProbe });

function shutdownEarly() {
	api.kill('SIGTERM');
	web.kill('SIGTERM');
	process.exit(1);
}

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
