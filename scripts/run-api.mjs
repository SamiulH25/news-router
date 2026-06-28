import { spawn } from 'node:child_process';
import { allocateDevPorts, apiEnv, backend, getPython, printBanner } from './lib.mjs';

const { apiPort, webPort } = await allocateDevPorts();
const python = getPython();
const reload = process.argv.includes('--reload');

const args = ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(apiPort)];
if (reload) args.push('--reload');

printBanner({ apiPort, webPort });
console.log('API only — start the frontend separately if needed.\n');

const child = spawn(python, args, {
	cwd: backend,
	env: apiEnv({ apiPort, webPort }),
	stdio: 'inherit',
	shell: process.platform === 'win32'
});

child.on('exit', (code) => process.exit(code ?? 0));
