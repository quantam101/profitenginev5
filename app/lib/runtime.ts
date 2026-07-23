const DEAD_HOSTS = new Set([
  'backend.alreadyherellc.com',
  'profitengine.alreadyherellc.com',
  'api.profitengine.alreadyherellc.com',
  'profitengine-tau.vercel.app',
  '129.146.236.177',
]);

export function getRuntimeBase(envValue = process.env.RUNTIME_API_URL): string {
  const candidate = (envValue || 'https://profitengine-runtime.onrender.com').replace(/\/$/, '');
  try {
    const host = new URL(candidate).hostname;
    if (DEAD_HOSTS.has(host)) return 'https://profitengine-runtime.onrender.com';
  } catch {
    // ignore malformed URLs and fall back to default
  }
  return candidate;
}
