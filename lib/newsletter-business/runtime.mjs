function runtimeBaseUrl() {
  return String(process.env.RUNTIME_API_URL || '').trim().replace(/\/$/, '');
}

export function newsletterRuntimeConfigured() {
  return Boolean(runtimeBaseUrl());
}

async function runtimeRequest(path, options = {}) {
  const base = runtimeBaseUrl();
  if (!base) {
    return { ok: false, configured: false, error: 'RUNTIME_API_URL is not configured' };
  }

  try {
    const response = await fetch(`${base}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      cache: 'no-store',
      signal: AbortSignal.timeout(options.timeoutMs || 15000),
    });
    const text = await response.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw: text };
    }
    return {
      ok: response.ok && data?.ok !== false,
      configured: true,
      status: response.status,
      data,
      error: response.ok ? data?.error : data?.error || `Runtime returned HTTP ${response.status}`,
    };
  } catch (error) {
    return {
      ok: false,
      configured: true,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function subscribeViaRuntime({ email, firstName = '' }) {
  return runtimeRequest('/newsletter/subscribe', {
    method: 'POST',
    body: JSON.stringify({ email, first_name: firstName }),
    timeoutMs: 20000,
  });
}

export async function getRuntimeNewsletterStats() {
  return runtimeRequest('/newsletter/stats', { method: 'GET', timeoutMs: 15000 });
}

export async function publishViaRuntime({ headline, sections, tags = [], ctaUrl }) {
  return runtimeRequest('/newsletter/publish', {
    method: 'POST',
    body: JSON.stringify({ headline, sections, tags, cta_url: ctaUrl }),
    timeoutMs: 45000,
  });
}
