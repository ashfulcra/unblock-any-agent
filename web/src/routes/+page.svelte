<script>
  import { user } from '$lib/user';
  import { onMount } from 'svelte';
  import LoginDeviceFlow from '$lib/components/LoginDeviceFlow.svelte';
  onMount(async () => { await user.init(); });
</script>
<svelte:head><title>Unblock Any Agent</title><meta name="description" content="Help agents get what they need and keep working." /></svelte:head>
{#if !$user.authenticated}
  <LoginDeviceFlow />
{:else}
  <main class="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center gap-6 px-6 py-16 text-fulcra-white">
    <p class="text-sm uppercase tracking-widest text-fulcra-teal">Unblock Any Agent · Hosted baseline</p>
    <h1 class="text-5xl font-medium tracking-tight">Connected to Fulcra.</h1>
    <p class="max-w-xl text-lg text-fulcra-gray">Your account is connected. The next milestone adds needs, human answers, and recovered work to this dashboard.</p>
    <div class="flex flex-wrap gap-4">
      <a class="rounded-lg bg-fulcra-teal/20 px-5 py-3 text-fulcra-teal" href="https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/personal-dashboard.md" target="_blank" rel="noreferrer">Create your own dashboard ↗</a>
      <a class="rounded-lg border border-fulcra-gray/30 px-5 py-3" href="https://github.com/ashfulcra/unblock-any-agent" target="_blank" rel="noreferrer">Source, skills & stars ↗</a>
      <button class="rounded-lg border border-fulcra-gray/30 px-5 py-3 text-fulcra-gray" onclick={user.logout}>Sign out</button>
    </div>
  </main>
{/if}
<footer class="bg-fulcra-black px-6 py-4 text-center text-sm text-fulcra-gray"><a class="underline" href="https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/personal-dashboard.md" target="_blank" rel="noreferrer">Create your own dashboard</a> · <a class="underline" href="https://github.com/ashfulcra/unblock-any-agent" target="_blank" rel="noreferrer">Canonical source & skills</a></footer>
