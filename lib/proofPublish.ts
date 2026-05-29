/**
 * lib/proofPublish.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Thin client for the FastAPI ProofPublish backend.
 *
 * Every blog post and dispatch that arrives via webhook is fingerprinted with a
 * SHA-256 manifest and a publish receipt.  This is the "proof of work" that
 * turns raw events into auditable, client-visible evidence of delivery.
 *
 * Design: fire-and-forget — never throws, never blocks the webhook response.
 * The FastAPI backend is the source of truth; failures are logged and swallowed.
 * ─────────────────────────────────────────────────────────────────────────────
 */

const BACKEND = (process.env.BACKEND_API_URL ?? 'http://backend:8001').replace(/\/$/, '');

/** Timeout for each proof request — short so it never delays the webhook ack */
const PROOF_TIMEOUT_MS = 8_000;

interface ManifestResult {
  manifest_id: string;
  content_hash: string;
  is_duplicate: boolean;
  [key: string]: unknown;
}

interface JobResult {
  job_id: string;
  status: string;
  is_duplicate: boolean;
  [key: string]: unknown;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(PROOF_TIMEOUT_MS),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`ProofPublish ${path} → ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Create a manifest + receipt for a published blog post.
 *
 * @param content  Full article body (or excerpt when full body is unavailable)
 * @param meta     Title, slug, tags, category, url, clientId
 * @returns        { manifest_id, job_id, content_hash } or null on failure
 */
export async function createBlogProof(
  content: string,
  meta: {
    title: string;
    slug: string;
    tags?: string[];
    category?: string;
    url?: string;
    clientId?: string;
  },
): Promise<{ manifest_id: string; job_id: string; content_hash: string } | null> {
  if (!content || !content.trim()) return null;

  try {
    const manifest = await post<ManifestResult>('/api/proof/manifest', {
      content: content.trim(),
      niche: meta.category ?? 'field-service',
      tags: meta.tags ?? [meta.category ?? 'field-service'],
      author_id: 'alreadyherellc.com',
    });

    const job = await post<JobResult>('/api/proof/publish', {
      manifest_id: manifest.manifest_id,
      platform: 'github',
      account_id: 'alreadyherellc',
      client_id: meta.clientId ?? 'alreadyherellc',
      // platform_url provided → backend immediately transitions to PUBLISHED
      // and creates an immutable receipt
      platform_url: meta.url ?? null,
    });

    return {
      manifest_id: manifest.manifest_id,
      job_id: job.job_id,
      content_hash: manifest.content_hash,
    };
  } catch (err) {
    // Proof is best-effort — log and continue
    console.error('[ProofPublish] blog proof failed:', err instanceof Error ? err.message : err);
    return null;
  }
}

/**
 * Create a proof manifest for a field-service dispatch event.
 *
 * Dispatches don't have a "published URL" — the proof records the fact that
 * the event arrived and was processed, creating an auditable trail.
 *
 * @param record   Structured dispatch record (already sanitised by the webhook)
 * @param clientId Client identifier for filtering receipts in the dashboard
 */
export async function createDispatchProof(
  record: {
    dispatchId: string;
    fullName: string;
    company: string;
    siteCity: string;
    serviceType: string;
    submittedAt: string;
    source: string;
  },
  clientId = 'alreadyherellc',
): Promise<{ manifest_id: string; job_id: string; content_hash: string } | null> {
  // Compose a deterministic text representation of the dispatch record
  const content = [
    `Dispatch: ${record.dispatchId}`,
    `Client: ${record.fullName}${record.company ? ` / ${record.company}` : ''}`,
    `Location: ${record.siteCity}`,
    `Service: ${record.serviceType}`,
    `Source: ${record.source}`,
    `Submitted: ${record.submittedAt}`,
  ].join('\n');

  try {
    const manifest = await post<ManifestResult>('/api/proof/manifest', {
      content,
      niche: 'field-service-dispatch',
      tags: ['dispatch', 'field-service', record.serviceType].filter(Boolean),
      author_id: 'alreadyherellc.com',
    });

    const job = await post<JobResult>('/api/proof/publish', {
      manifest_id: manifest.manifest_id,
      platform: 'github',
      account_id: 'alreadyherellc',
      client_id: clientId,
      // No public URL for dispatches — job stays in DRAFT until processed
      platform_url: null,
    });

    return {
      manifest_id: manifest.manifest_id,
      job_id: job.job_id,
      content_hash: manifest.content_hash,
    };
  } catch (err) {
    console.error('[ProofPublish] dispatch proof failed:', err instanceof Error ? err.message : err);
    return null;
  }
}
