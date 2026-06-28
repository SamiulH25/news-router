/** Map IANA timezone to a likely onboarding country code. */
export function guessCountryFromTimezone(timezone: string): string | null {
	const tz = timezone.trim();
	if (!tz) return null;

	const rules: Array<[RegExp | string, string]> = [
		[/^America\/(Toronto|Vancouver|Winnipeg|Edmonton|Halifax|St_Johns|Regina|Yellowknife|Whitehorse|Iqaluit)/, 'CA'],
		[/^America\/(New_York|Chicago|Denver|Los_Angeles|Phoenix|Detroit|Anchorage|Honolulu|Boise|Indianapolis)/, 'US'],
		['Europe/London', 'GB'],
		[/^Australia\//, 'AU'],
		['Asia/Dhaka', 'BD'],
		['Asia/Kolkata', 'IN'],
		['Asia/Karachi', 'PK'],
		[/^Europe\/(Berlin|Vienna|Zurich)/, 'DE'],
		[/^Europe\/(Paris|Brussels)/, 'FR'],
		['Asia/Tokyo', 'JP'],
		['Europe/Dublin', 'IE'],
		['Pacific/Auckland', 'NZ'],
		['Africa/Johannesburg', 'ZA'],
		['Asia/Singapore', 'SG'],
		['Africa/Lagos', 'NG'],
		['America/Mexico_City', 'MX'],
		['Europe/Madrid', 'ES'],
		['Europe/Rome', 'IT'],
		['Europe/Amsterdam', 'NL'],
		['Asia/Manila', 'PH'],
		['Asia/Bangkok', 'TH'],
		['Asia/Kuala_Lumpur', 'MY'],
		['Asia/Hong_Kong', 'HK'],
		['America/Sao_Paulo', 'BR'],
	];

	for (const [pattern, code] of rules) {
		if (typeof pattern === 'string' ? tz === pattern : pattern.test(tz)) {
			return code;
		}
	}
	return null;
}
