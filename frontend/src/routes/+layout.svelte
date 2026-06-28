<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api, type User } from '$lib/api';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import ToastHost from '$lib/components/ToastHost.svelte';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	let { children } = $props();

	let user = $state<User | null>(null);
	let loading = $state(true);

	const publicPaths = ['/login', '/register'];

	const editionDate = new Intl.DateTimeFormat(undefined, {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	}).format(new Date());

	const scheduleHint = $derived.by(() => {
		if (!user) return '';
		const fmt = (h: number, m: number) =>
			`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
		return `Last ${user.feed_window_hours}h · digests ${fmt(user.digest_hour, user.digest_minute)} & ${fmt(user.digest_evening_hour, user.digest_evening_minute)} (${user.timezone}) · ${editionDate}`;
	});

	onMount(async () => {
		if (publicPaths.includes($page.url.pathname)) {
			loading = false;
			return;
		}
		try {
			user = await api.me();
			if (!user.onboarded && !$page.url.pathname.startsWith('/onboarding')) {
				goto('/onboarding');
				return;
			}
		} catch {
			user = null;
			goto('/login');
		} finally {
			loading = false;
		}
	});

	async function logout() {
		await api.logout();
		user = null;
		goto('/login');
	}

	const isPublic = $derived(publicPaths.includes($page.url.pathname));
	const isReelsFeed = $derived(
		$page.url.pathname === '/feed' && $page.url.searchParams.get('view') !== 'list'
	);
	const isOnboarding = $derived($page.url.pathname.startsWith('/onboarding'));
	const pageKey = $derived($page.url.pathname);
</script>

<svelte:head>
	<title>News Router</title>
	<link rel="manifest" href="/manifest.webmanifest" />
	<meta name="theme-color" content="#08090c" />
</svelte:head>

{#if loading && !isPublic}
	<div class="boot-screen">
		<span class="routing-lamp routing-lamp--live" aria-hidden="true"></span>
		<p class="loading-pulse">Routing your edition</p>
	</div>
{:else}
	{#if user && !isPublic && !isReelsFeed && !isOnboarding}
		<header class="masthead">
			<div class="masthead__inner">
				<div class="masthead__row">
					<a href="/" class="masthead__brand">
						<span class="routing-lamp" aria-hidden="true"></span>
						News Router
					</a>
					<div class="masthead__nav-scroll">
						<nav class="masthead__nav" aria-label="Main">
							<a href="/" class:active={$page.url.pathname === '/'}>Home</a>
							<a href="/feed" class:active={$page.url.pathname === '/feed'}>Read</a>
							<a href="/archive" class:active={$page.url.pathname === '/archive'}>Archive</a>
							<a href="/settings/feeds" class:active={$page.url.pathname.startsWith('/settings/feeds')}
								>Sources</a
							>
							<a href="/settings/topics" class:active={$page.url.pathname.startsWith('/settings/topics')}
								>Topics</a
							>
							<a href="/settings" class:active={$page.url.pathname === '/settings'}>Settings</a>
						</nav>
					</div>
					<div class="masthead__user">
						<span class="masthead__username">{user.username}</span>
						<button class="btn-ghost btn-sm" onclick={logout}>Sign out</button>
					</div>
				</div>
				<p class="masthead__edition">{scheduleHint}</p>
			</div>
		</header>
	{/if}

	<main class="page-shell" class:main--reels={isReelsFeed}>
		{#if isReelsFeed}
			{@render children()}
		{:else}
			{#key pageKey}
				<div
					class="page-content"
					in:fly={{ y: 14, duration: 320, opacity: 0, easing: (t) => 1 - Math.pow(1 - t, 3) }}
					out:fade={{ duration: 140 }}
				>
					{@render children()}
				</div>
			{/key}
		{/if}
	</main>
{/if}

<ToastHost />
<ConfirmDialog />

<style>
	.page-content {
		width: 100%;
	}
</style>
