import { createHash, createHmac, randomUUID, timingSafeEqual } from 'node:crypto';

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}

export function canonicalJson(value) {
  return JSON.stringify(stable(value));
}

export function payloadDigest(value) {
  return createHash('sha256').update(canonicalJson(value)).digest('hex');
}

function encode(value) {
  return Buffer.from(value, 'utf8').toString('base64url');
}

function decode(value) {
  return Buffer.from(value, 'base64url').toString('utf8');
}

function asDate(value) {
  return value instanceof Date ? value : new Date(value);
}

function assertSecret(secret) {
  if (!secret || String(secret).length < 32) throw new Error('PASSIVE_INCOME_APPROVAL_SECRET must contain at least 32 characters');
}

export class InMemoryExecutionStore {
  constructor() {
    this.durable = false;
    this.leases = new Map();
    this.idempotency = new Map();
    this.nonces = new Set();
    this.circuits = new Map();
    this.budgets = new Map();
  }

  async acquireLease(key, owner, ttlMs, now = new Date()) {
    const current = this.leases.get(key);
    if (current && current.owner !== owner && current.expiresAt > now) return null;
    const lease = { key, owner, expiresAt: new Date(now.getTime() + ttlMs) };
    this.leases.set(key, lease);
    return lease;
  }

  async releaseLease(key, owner) {
    const current = this.leases.get(key);
    if (current?.owner === owner) this.leases.delete(key);
  }

  async getIdempotency(key) {
    return this.idempotency.get(key) || null;
  }

  async putIdempotency(key, record) {
    this.idempotency.set(key, structuredClone(record));
    return record;
  }

  async consumeNonce(nonce) {
    if (this.nonces.has(nonce)) return false;
    this.nonces.add(nonce);
    return true;
  }

  async getCircuit(key) {
    return structuredClone(this.circuits.get(key) || null);
  }

  async putCircuit(key, state) {
    this.circuits.set(key, structuredClone(state));
    return state;
  }

  async reserveBudget(key, amountUsd, maxUsd) {
    const current = Number(this.budgets.get(key) || 0);
    const amount = Number(amountUsd || 0);
    if (current + amount > maxUsd + Number.EPSILON) return { allowed: false, spentUsd: current };
    const spentUsd = current + amount;
    this.budgets.set(key, spentUsd);
    return { allowed: true, spentUsd };
  }
}

export class MongoExecutionStore {
  constructor(db, { prefix = 'passive_income' } = {}) {
    if (!db) throw new Error('MongoExecutionStore requires a MongoDB Db instance');
    this.durable = true;
    this.leases = db.collection(`${prefix}_leases`);
    this.idempotency = db.collection(`${prefix}_idempotency`);
    this.nonces = db.collection(`${prefix}_approval_nonces`);
    this.circuits = db.collection(`${prefix}_circuits`);
    this.budgets = db.collection(`${prefix}_budgets`);
  }

  async ensureIndexes() {
    await Promise.all([
      this.leases.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 }),
      this.idempotency.createIndex({ createdAt: 1 }),
      this.nonces.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 }),
      this.circuits.createIndex({ updatedAt: 1 }),
      this.budgets.createIndex({ updatedAt: 1 }),
    ]);
  }

  async acquireLease(key, owner, ttlMs, now = new Date()) {
    const expiresAt = new Date(now.getTime() + ttlMs);
    try {
      const result = await this.leases.findOneAndUpdate(
        { _id: key, $or: [{ expiresAt: { $lte: now } }, { owner }] },
        { $set: { owner, expiresAt, updatedAt: now }, $setOnInsert: { createdAt: now } },
        { upsert: true, returnDocument: 'after' },
      );
      return result ? { key, owner: result.owner, expiresAt: asDate(result.expiresAt) } : null;
    } catch (error) {
      if (error?.code === 11000) return null;
      throw error;
    }
  }

  async releaseLease(key, owner) {
    await this.leases.deleteOne({ _id: key, owner });
  }

  async getIdempotency(key) {
    return this.idempotency.findOne({ _id: key });
  }

  async putIdempotency(key, record) {
    await this.idempotency.updateOne(
      { _id: key },
      { $set: { ...record, updatedAt: new Date() }, $setOnInsert: { createdAt: new Date() } },
      { upsert: true },
    );
    return record;
  }

  async consumeNonce(nonce, expiresAt) {
    try {
      await this.nonces.insertOne({ _id: nonce, expiresAt: asDate(expiresAt), createdAt: new Date() });
      return true;
    } catch (error) {
      if (error?.code === 11000) return false;
      throw error;
    }
  }

  async getCircuit(key) {
    return this.circuits.findOne({ _id: key });
  }

  async putCircuit(key, state) {
    await this.circuits.updateOne(
      { _id: key },
      { $set: { ...state, updatedAt: new Date() }, $setOnInsert: { createdAt: new Date() } },
      { upsert: true },
    );
    return state;
  }

  async reserveBudget(key, amountUsd, maxUsd) {
    const now = new Date();
    const amount = Number(amountUsd || 0);
    await this.budgets.updateOne(
      { _id: key },
      { $setOnInsert: { spentUsd: 0, createdAt: now }, $set: { updatedAt: now } },
      { upsert: true },
    );
    const result = await this.budgets.findOneAndUpdate(
      { _id: key, spentUsd: { $lte: Math.max(0, maxUsd - amount) } },
      { $inc: { spentUsd: amount }, $set: { updatedAt: now } },
      { returnDocument: 'after' },
    );
    if (!result) {
      const current = await this.budgets.findOne({ _id: key });
      return { allowed: false, spentUsd: Number(current?.spentUsd || 0) };
    }
    return { allowed: true, spentUsd: Number(result.spentUsd || 0) };
  }
}

export function createExecutionControl({
  store,
  approvalSecret = '',
  clock = () => new Date(),
  leaseTtlMs = 60_000,
  circuitFailureThreshold = 3,
  circuitResetMs = 300_000,
} = {}) {
  if (!store) throw new Error('Execution control requires a store');
  const probeTtlMs = Math.max(1, Math.min(circuitResetMs, 60_000));

  function signApproval({ action, resource, payload, expiresAt, nonce = randomUUID() }) {
    assertSecret(approvalSecret);
    const body = {
      v: 1,
      action: String(action),
      resource: String(resource),
      digest: payloadDigest(payload),
      exp: asDate(expiresAt).toISOString(),
      nonce: String(nonce),
    };
    const encoded = encode(canonicalJson(body));
    const signature = createHmac('sha256', approvalSecret).update(encoded).digest('base64url');
    return `${encoded}.${signature}`;
  }

  async function verifyAndConsumeApproval(token, { action, resource, payload }) {
    assertSecret(approvalSecret);
    const [encoded, suppliedSignature, extra] = String(token || '').split('.');
    if (!encoded || !suppliedSignature || extra) return { ok: false, reason: 'malformed_approval' };
    const expectedSignature = createHmac('sha256', approvalSecret).update(encoded).digest('base64url');
    const a = Buffer.from(suppliedSignature);
    const b = Buffer.from(expectedSignature);
    if (a.length !== b.length || !timingSafeEqual(a, b)) return { ok: false, reason: 'invalid_signature' };

    let body;
    try {
      body = JSON.parse(decode(encoded));
    } catch {
      return { ok: false, reason: 'invalid_payload' };
    }
    if (body.v !== 1) return { ok: false, reason: 'unsupported_version' };
    if (body.action !== String(action) || body.resource !== String(resource)) return { ok: false, reason: 'approval_scope_mismatch' };
    if (body.digest !== payloadDigest(payload)) return { ok: false, reason: 'approval_digest_mismatch' };
    const expiresAt = asDate(body.exp);
    if (!Number.isFinite(expiresAt.getTime()) || expiresAt <= clock()) return { ok: false, reason: 'approval_expired' };
    const consumed = await store.consumeNonce(body.nonce, expiresAt);
    if (!consumed) return { ok: false, reason: 'approval_replay' };
    return { ok: true, approval: body };
  }

  async function runOnce({ key, payload, execute, ttlMs = leaseTtlMs }) {
    const digest = payloadDigest(payload);
    const existing = await store.getIdempotency(key);
    if (existing) {
      if (existing.digest !== digest) throw new Error(`Idempotency key collision for ${key}`);
      if (existing.status === 'completed') return { ...existing, replayed: true };
    }

    const owner = randomUUID();
    const lease = await store.acquireLease(`action:${key}`, owner, ttlMs, clock());
    if (!lease) return { status: 'busy', key, digest, replayed: false };
    try {
      const afterLock = await store.getIdempotency(key);
      if (afterLock?.status === 'completed') {
        if (afterLock.digest !== digest) throw new Error(`Idempotency key collision for ${key}`);
        return { ...afterLock, replayed: true };
      }
      await store.putIdempotency(key, { status: 'running', digest, startedAt: clock().toISOString() });
      try {
        const result = await execute();
        const record = { status: 'completed', digest, result, completedAt: clock().toISOString() };
        await store.putIdempotency(key, record);
        return { ...record, replayed: false };
      } catch (error) {
        await store.putIdempotency(key, {
          status: 'failed',
          digest,
          error: error instanceof Error ? error.message : String(error),
          failedAt: clock().toISOString(),
        });
        throw error;
      }
    } finally {
      await store.releaseLease(`action:${key}`, owner);
    }
  }

  async function acquireHalfOpenProbe(key, state, now) {
    const probeOwner = randomUUID();
    const lease = await store.acquireLease(`circuit-probe:${key}`, probeOwner, probeTtlMs, now);
    if (!lease) return { allowed: false, mode: 'HALF_OPEN_BUSY' };
    const probeUntil = new Date(now.getTime() + probeTtlMs).toISOString();
    await store.putCircuit(key, { ...state, mode: 'HALF_OPEN', probeOwner, probeUntil, openUntil: null });
    return { allowed: true, mode: 'HALF_OPEN', probeOwner, probeUntil };
  }

  async function beforeCircuitCall(key) {
    let state = await store.getCircuit(key);
    if (!state || state.mode === 'CLOSED') return { allowed: true, mode: 'CLOSED' };
    const now = clock();

    if (state.mode === 'OPEN' && asDate(state.openUntil) > now) {
      return { allowed: false, mode: 'OPEN', openUntil: state.openUntil };
    }

    if (state.mode === 'HALF_OPEN') {
      const probeUntil = asDate(state.probeUntil);
      if (Number.isFinite(probeUntil.getTime()) && probeUntil > now) {
        return { allowed: false, mode: 'HALF_OPEN_BUSY', probeUntil: state.probeUntil };
      }
      if (state.probeOwner) await store.releaseLease(`circuit-probe:${key}`, state.probeOwner);
      state = { ...state, mode: 'OPEN', openUntil: now.toISOString(), probeOwner: null, probeUntil: null };
      await store.putCircuit(key, state);
    }

    if (state.mode === 'OPEN') return acquireHalfOpenProbe(key, state, now);
    return { allowed: false, mode: state.mode };
  }

  async function recordCircuitFailure(key, probeOwner) {
    const current = (await store.getCircuit(key)) || { failures: 0, mode: 'CLOSED' };
    const failures = Number(current.failures || 0) + 1;
    const shouldOpen = current.mode === 'HALF_OPEN' || failures >= circuitFailureThreshold;
    const next = {
      failures,
      mode: shouldOpen ? 'OPEN' : 'CLOSED',
      openUntil: shouldOpen ? new Date(clock().getTime() + circuitResetMs).toISOString() : null,
      probeOwner: null,
      probeUntil: null,
    };
    await store.putCircuit(key, next);
    if (probeOwner) await store.releaseLease(`circuit-probe:${key}`, probeOwner);
    return next;
  }

  async function recordCircuitSuccess(key, probeOwner) {
    const next = { failures: 0, mode: 'CLOSED', openUntil: null, probeOwner: null, probeUntil: null };
    await store.putCircuit(key, next);
    if (probeOwner) await store.releaseLease(`circuit-probe:${key}`, probeOwner);
    return next;
  }

  async function reserveBudget({ bucket, amountUsd, maxUsd, zeroSpend = false }) {
    const amount = Number(amountUsd || 0);
    if (amount < 0) throw new Error('Budget reservation cannot be negative');
    if (zeroSpend && amount > 0) return { allowed: false, reason: 'zero_spend_policy', spentUsd: 0 };
    return store.reserveBudget(bucket, amount, Number(maxUsd || 0));
  }

  return {
    signApproval,
    verifyAndConsumeApproval,
    runOnce,
    beforeCircuitCall,
    recordCircuitFailure,
    recordCircuitSuccess,
    reserveBudget,
  };
}

export function assertProductionControl({ production = false, externalWrite = false, store }) {
  if (production && externalWrite && store?.durable !== true) {
    throw new Error('Production external writes require a durable execution-control store');
  }
  return true;
}
