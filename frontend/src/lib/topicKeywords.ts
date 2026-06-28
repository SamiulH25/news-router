/** Suggested keyword sets when the user names a common topic. */
export const KEYWORD_SUGGESTIONS: Record<string, string> = {
	politics:
		'politics, election, parliament, government, minister, pm, mp, commons, westminster, chancellor, starmer, labour, tory, conservative, policy, vote, senate, congress, white house, democrat, republican',
	technology: 'technology, tech, ai, software, chip, startup, apple, google, microsoft, cyber',
	sports: 'sports, football, soccer, basketball, baseball, nfl, nba, premier league, olympics',
	business: 'business, economy, market, stocks, inflation, fed, earnings, trade, ceo',
	science: 'science, space, climate, research, nasa, study, health, vaccine',
	world: 'war, ukraine, gaza, china, europe, nato, united nations, conflict',
	entertainment: 'film, movie, music, celebrity, tv, netflix, hollywood, album'
};

export function suggestKeywords(topicName: string): string | null {
	const key = topicName.trim().toLowerCase();
	return KEYWORD_SUGGESTIONS[key] ?? null;
}

/** Human-readable description of what will match for a topic. */
export function describeMatching(name: string, keywords: string): string {
	const explicit = keywords.trim();
	if (explicit) {
		const count = explicit.split(/[,;\n]/).filter((k) => k.trim()).length;
		return `Matches articles whose title or summary contains any of ${count} keyword${count === 1 ? '' : 's'}.`;
	}
	if (name.trim()) {
		return 'Leave keywords blank to show every story from linked sources.';
	}
	return 'Matches every article from linked sources.';
}
