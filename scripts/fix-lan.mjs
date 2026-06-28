/**
 * Launch fix-lan-access.ps1 with UAC elevation (Windows only).
 * User clicks Yes on the UAC prompt once.
 */
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const ps1 = path.join(scriptDir, 'fix-lan-access.ps1');

if (process.platform !== 'win32') {
	console.log('LAN firewall fix is only needed on Windows.');
	process.exit(0);
}

console.log('Requesting Administrator access (UAC prompt)…\n');

const child = spawn(
	'powershell.exe',
	[
		'-NoProfile',
		'-ExecutionPolicy',
		'Bypass',
		'-Command',
		`Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','${ps1.replace(/'/g, "''")}'`
	],
	{ stdio: 'inherit', shell: false }
);

child.on('exit', (code) => {
	if (code === 0) {
		console.log('\nIf the elevated window showed "Done", restart: npm run start:dev');
	}
	process.exit(code ?? 1);
});
