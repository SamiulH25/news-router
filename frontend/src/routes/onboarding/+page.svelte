<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, type CatalogCountry } from '$lib/api';
	import { guessCountryFromTimezone } from '$lib/onboardingCatalog';
	import { defaultTimezone, ensureTimezone, listTimezones } from '$lib/timezones';
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';

	let step = $state(1);
	const timezones = listTimezones();
	let timezone = $state(defaultTimezone());

	let topicName = $state('Headlines');
	let extraFeedUrl = $state('');
	let catalog = $state<CatalogCountry[]>([]);
	let selectedUrls = $state<Set<string>>(new Set());
	let activeCountry = $state<string>('CA');
	let saving = $state(false);
	let error = $state('');

	const activeCountryData = $derived(catalog.find((c) => c.code === activeCountry) ?? catalog[0]);
	const selectedCount = $derived(selectedUrls.size);
	const visibleOutlets = $derived(activeCountryData?.outlets ?? []);

	function toggleOutlet(url: string, checked: boolean) {
		const next = new Set(selectedUrls);
		if (checked) next.add(url);
		else next.delete(url);
		selectedUrls = next;
	}

	function selectAllVisible() {
		const next = new Set(selectedUrls);
		for (const outlet of visibleOutlets) next.add(outlet.url);
		selectedUrls = next;
	}

	function clearVisible() {
		const next = new Set(selectedUrls);
		for (const outlet of visibleOutlets) next.delete(outlet.url);
		selectedUrls = next;
	}

	function applyTimezoneCountryHint() {
		const guessed = guessCountryFromTimezone(timezone);
		if (guessed && catalog.some((c) => c.code === guessed)) {
			activeCountry = guessed;
		}
	}

	onMount(async () => {
		try {
			const user = await api.me();
			if (user.onboarded) goto('/');
			timezone = ensureTimezone(user.timezone, timezones);

			const data = await api.getOnboardingCatalog();
			catalog = data.countries;
			selectedUrls = new Set(data.default_selected_urls);
			applyTimezoneCountryHint();
		} catch {
			goto('/login');
		}
	});

	async function finish() {
		if (selectedCount === 0 && !extraFeedUrl.trim()) {
			error = 'Select at least one outlet or add a custom source.';
			return;
		}

		saving = true;
		error = '';
		try {
			await api.completeOnboarding({
				timezone,
				topic_name: topicName.trim() || 'Headlines',
				selected_outlet_urls: [...selectedUrls],
				extra_feed_url: extraFeedUrl.trim() || undefined
			});
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Setup failed';
		} finally {
			saving = false;
		}
	}
</script>

<div class="container container--narrow onboarding">
	<header class="page-header wire-edge">
		<p class="eyebrow">Welcome</p>
		<h1 class="display-title">Set up News Router</h1>
		<p class="lead">Three steps to route your first edition</p>
	</header>

	<div class="onboarding-steps" aria-hidden="true">
		<span class:done={step > 1} class:active={step === 1}></span>
		<span class:done={step > 2} class:active={step === 2}></span>
		<span class:active={step === 3}></span>
	</div>

	{#key step}
		<section
			class="card wire-edge"
			in:fly={{ x: 20, duration: 280, opacity: 0 }}
			out:fly={{ x: -12, duration: 180, opacity: 0 }}
		>
			{#if step === 1}
				<h2>Your timezone</h2>
				<p class="muted">Morning and evening digests use this clock.</p>
				<label class="label" for="tz">Timezone</label>
				<select
					id="tz"
					class="input"
					bind:value={timezone}
					onchange={applyTimezoneCountryHint}
				>
					{#each timezones as tz}
						<option value={tz}>{tz}</option>
					{/each}
				</select>
				<div class="actions" style="margin-top: 1rem">
					<button class="btn" onclick={() => (step = 2)}>Continue</button>
				</div>
			{:else if step === 2}
				<h2>First topic</h2>
				<p class="muted">Topics are channels — e.g. Headlines, Local, Sports.</p>
				<label class="label" for="topic">Topic name</label>
				<input id="topic" class="input" bind:value={topicName} />
				<div class="actions" style="margin-top: 1rem">
					<button class="btn-secondary" onclick={() => (step = 1)}>Back</button>
					<button class="btn" onclick={() => (step = 3)}>Continue</button>
				</div>
			{:else}
				<h2>Starting sources</h2>
				<p class="muted">
					Pick outlets by region for <strong>{topicName.trim() || 'Headlines'}</strong>. Popular
					choices are pre-selected — uncheck anything you don't want.
				</p>

				<div class="onboarding-countries" role="tablist" aria-label="News regions">
					{#each catalog as country (country.code)}
						<button
							type="button"
							class="onboarding-country"
							class:onboarding-country--active={activeCountry === country.code}
							role="tab"
							aria-selected={activeCountry === country.code}
							onclick={() => (activeCountry = country.code)}
						>
							{country.name}
						</button>
					{/each}
				</div>

				<div class="actions onboarding-outlet-actions">
					<span class="muted onboarding-outlet-count">{selectedCount} selected</span>
					<button type="button" class="btn-ghost btn-sm" onclick={selectAllVisible}>All in region</button>
					<button type="button" class="btn-ghost btn-sm" onclick={clearVisible}>Clear region</button>
				</div>

				<ul class="onboarding-outlets">
					{#each visibleOutlets as outlet (outlet.url)}
						<li class="onboarding-outlet">
							<label class="onboarding-outlet__label">
								<input
									type="checkbox"
									checked={selectedUrls.has(outlet.url)}
									onchange={(e) => toggleOutlet(outlet.url, e.currentTarget.checked)}
								/>
								<span class="onboarding-outlet__copy">
									<span class="onboarding-outlet__name">{outlet.title}</span>
									{#if outlet.language !== 'en'}
										<span class="onboarding-outlet__lang">{outlet.language.toUpperCase()}</span>
									{/if}
								</span>
							</label>
						</li>
					{/each}
				</ul>

				<label class="label" for="extra-feed">Add another source (optional)</label>
				<input
					id="extra-feed"
					class="input"
					bind:value={extraFeedUrl}
					placeholder="https://www.example.com"
				/>

				{#if error}<p class="error">{error}</p>{/if}
				<div class="actions" style="margin-top: 1rem">
					<button class="btn-secondary" onclick={() => (step = 2)}>Back</button>
					<button class="btn" onclick={finish} disabled={saving}>
						{saving ? 'Setting up…' : 'Finish setup'}
					</button>
				</div>
			{/if}
		</section>
	{/key}
</div>

<style>
	.onboarding-countries {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin: 1rem 0 0.75rem;
		max-height: 9rem;
		overflow-y: auto;
		padding: 0.125rem;
	}

	.onboarding-country {
		padding: 0.35rem 0.65rem;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: var(--ink-soft);
		color: var(--chalk-muted);
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		cursor: pointer;
		transition:
			border-color var(--duration-fast) var(--ease-out),
			color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.onboarding-country:hover {
		border-color: var(--chalk-muted);
		color: var(--chalk);
	}

	.onboarding-country--active {
		border-color: var(--press);
		background: var(--press-dim);
		color: var(--press-bright);
	}

	.onboarding-outlet-actions {
		justify-content: flex-start;
		gap: 0.75rem;
		margin-top: 0.25rem;
		flex-wrap: wrap;
	}

	.onboarding-outlet-count {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.onboarding-outlets {
		list-style: none;
		padding: 0;
		margin: 0.75rem 0 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 16rem;
		overflow-y: auto;
	}

	.onboarding-outlet {
		border-radius: var(--radius-md);
		border: 1px solid var(--rule);
		background: var(--ink-soft);
	}

	.onboarding-outlet__label {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		padding: 0.625rem 0.75rem;
		cursor: pointer;
	}

	.onboarding-outlet__label input {
		margin-top: 0.15rem;
		flex-shrink: 0;
		accent-color: var(--press);
	}

	.onboarding-outlet__copy {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5rem;
		min-width: 0;
	}

	.onboarding-outlet__name {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--chalk);
	}

	.onboarding-outlet__lang {
		font-family: var(--font-mono);
		font-size: 0.5625rem;
		letter-spacing: 0.08em;
		padding: 0.15rem 0.4rem;
		border-radius: 999px;
		border: 1px solid var(--rule);
		color: var(--chalk-muted);
	}

	.muted strong {
		color: var(--chalk);
		font-weight: 600;
	}
</style>
