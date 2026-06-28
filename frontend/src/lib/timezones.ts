const FALLBACK_TIMEZONES = [
	'UTC',
	'America/New_York',
	'America/Chicago',
	'America/Denver',
	'America/Los_Angeles',
	'America/Toronto',
	'America/Vancouver',
	'Europe/London',
	'Europe/Paris',
	'Europe/Berlin',
	'Asia/Tokyo',
	'Asia/Singapore',
	'Australia/Sydney'
];

export function listTimezones(): string[] {
	try {
		const supported = Intl.supportedValuesOf('timeZone');
		return supported.slice().sort((a, b) => a.localeCompare(b));
	} catch {
		return FALLBACK_TIMEZONES;
	}
}

export function defaultTimezone(): string {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
	} catch {
		return 'UTC';
	}
}

export function ensureTimezone(value: string | undefined, zones: string[]): string {
	if (value && zones.includes(value)) return value;
	const detected = defaultTimezone();
	if (zones.includes(detected)) return detected;
	return zones[0] ?? 'UTC';
}
