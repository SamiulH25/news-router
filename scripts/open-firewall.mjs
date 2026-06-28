/**
 * Open Windows Firewall for News Router dev ports.
 * Run once as Administrator: npm run open-firewall
 */
import { ensureWindowsFirewall, PORT_RANGES } from './lib.mjs';

const result = ensureWindowsFirewall({ force: true });
if (result.ok) {
	console.log('Firewall rules ready — other devices on your network can reach News Router.');
	if (result.created?.length) {
		for (const rule of result.created) console.log(`  + ${rule}`);
	}
	process.exit(0);
}

console.error('\nCould not update Windows Firewall (Administrator required).\n');
console.error('Run this instead — it opens an elevated window (UAC prompt):\n');
console.error('  npm run fix-lan\n');
console.error('Or right-click Terminal → Run as administrator, then:\n');
console.error('  npm run open-firewall\n');
if (result.error) console.error(result.error);
process.exit(1);
