<script lang="ts">
	import { api, type AdminUser } from '$lib/api';
	import { toast } from '$lib/toast.svelte';
	import { onMount } from 'svelte';

	let users = $state<AdminUser[]>([]);
	let error = $state('');
	let loading = $state(true);

	onMount(async () => {
		try {
			users = await api.listAdminUsers();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Admin access required';
		} finally {
			loading = false;
		}
	});

	async function toggleAdmin(user: AdminUser) {
		const wasAdmin = user.is_admin;
		try {
			await api.patchAdminUser(user.id, { is_admin: !wasAdmin });
			users = await api.listAdminUsers();
			toast.success(wasAdmin ? 'Admin revoked' : 'Admin granted');
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Update failed');
		}
	}
</script>

<div class="container container--wide">
	<header class="page-header wire-edge">
		<div>
			<p class="eyebrow">Administration</p>
			<h1 class="display-title">Household users</h1>
			<p class="lead">Manage who has admin access</p>
		</div>
		<a href="/settings" class="btn-secondary">Back to settings</a>
	</header>

	{#if loading}
		<p class="loading-pulse">Loading users</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else}
		<div class="card admin-panel stagger-in" style="--i: 0">
			<table class="admin-table">
				<thead>
					<tr>
						<th>User</th>
						<th>Admin</th>
						<th>Onboarded</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each users as user, i (user.id)}
						<tr class="admin-table__row stagger-in" style="--i: {i + 1}">
							<td class="admin-table__user">{user.username}</td>
							<td>
								<span
									class="admin-table__pill"
									class:admin-table__pill--on={user.is_admin}
								>
									{user.is_admin ? 'Yes' : 'No'}
								</span>
							</td>
							<td>
								<span
									class="admin-table__pill"
									class:admin-table__pill--on={user.onboarded}
								>
									{user.onboarded ? 'Yes' : 'No'}
								</span>
							</td>
							<td class="admin-table__actions">
								<button class="btn-secondary btn-sm" onclick={() => toggleAdmin(user)}>
									{user.is_admin ? 'Revoke admin' : 'Make admin'}
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<style>
	.admin-panel {
		padding: 0;
		overflow: hidden;
	}

	.admin-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.admin-table th,
	.admin-table td {
		text-align: left;
		padding: 0.75rem 1.25rem;
		border-bottom: 1px solid var(--rule);
	}

	.admin-table th {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--chalk-muted);
		background: var(--ink);
	}

	.admin-table__row {
		transition: background var(--duration-fast) var(--ease-out);
	}

	.admin-table__row:hover {
		background: var(--ink-soft);
	}

	.admin-table__row:last-child td {
		border-bottom: none;
	}

	.admin-table__user {
		font-weight: 600;
		color: var(--chalk);
	}

	.admin-table__pill {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.625rem;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		padding: 0.2rem 0.5rem;
		border-radius: 999px;
		background: var(--ink-soft);
		color: var(--chalk-muted);
	}

	.admin-table__pill--on {
		background: var(--route-dim);
		color: var(--route);
	}

	.admin-table__actions {
		text-align: right;
	}
</style>
