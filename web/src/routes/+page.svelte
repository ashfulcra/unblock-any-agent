<script>
  import { user } from '$lib/user';
  import { onMount } from 'svelte';
  import NeedsDashboard from '$lib/components/NeedsDashboard.svelte';
  import LoginDeviceFlow from '$lib/components/LoginDeviceFlow.svelte';
  onMount(async () => { await user.init(); });
</script>
<svelte:head><title>Unblock Any Agent</title><meta name="description" content="Help agents get what they need and keep working." /></svelte:head>
{#if !$user.authenticated}
  <LoginDeviceFlow />
{:else}
  <NeedsDashboard />
  <button class="mx-auto mb-6 block text-sm underline text-fulcra-gray" onclick={user.logout}>Sign out</button>
{/if}
<footer class="bg-fulcra-black px-6 py-4 text-center text-sm text-fulcra-gray"><a class="underline" href="https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/personal-dashboard.md" target="_blank" rel="noreferrer">Create your own dashboard</a> · <a class="underline" href="https://github.com/ashfulcra/unblock-any-agent" target="_blank" rel="noreferrer">Canonical source & skills</a></footer>
