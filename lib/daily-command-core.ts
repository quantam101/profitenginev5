/**
 * Already Here LLC — Daily Command Guarded Revenue Engine
 *
 * This module is intentionally pure: no network calls, no secrets, no writes.
 * Live connectors feed raw signals into this core through server-side adapters.
 * The core normalizes, quarantines, ranks, scores, routes, and exports the
 * owner-facing Daily Command snapshot.
 */

export const DAILY_REVENUE_TARGET_USD = 500;
export const LABOR_FLOOR_USD_PER_HOUR = 65;

export const VALID_SIGNAL_SOURCES = [
  'GMAIL',
  'GOOGLE_CALENDAR',
  'GITHUB',
  'VERCEL',
  'WORKMARKET',
  'FIELD_NATION',
  'SQUARE',
  'STRIPE',
  'QUICKBOOKS',
  'DISPATCH_INTAKE',
  'RFQ',
  'DRONE_UAS',
  'MANUAL',
  'UNKNOWN',
] as const;

export const VALID_OPERATING_CATEGORIES = [
  'FIELD_SERVICE',
  'HAULING',
  'AUTOWORKS',
  'PAYMENT_PROTECTION',
  'DRONE_UAS',
  'SYSTEM_HEALTH',
  'PROCUREMENT',
  'DISPATCH_INTAKE',
  'UNKNOWN',
] as const;

export const VALID_ITEM_STATUSES = [
  'NEW',
  'NEEDS_REVIEW',
  'READY_TO_ACT',
  'BOOKED',
  'IN_PROGRESS',
  'INVOICED',
  'PAID',
  'REJECTED',
  'QUARANTINED',
] as const;

export const VALID_REVENUE_STATUSES = [
  'OPPORTUNITY',
  'BOOKABLE',
  'CONFIRMED',
  'INVOICED',
  'COLLECTED',
  'DISPUTED',
  'NON_REVENUE',
] as const;

export const VALID_GRADES = ['A', 'B', 'C', 'D', 'F'] as const;

export type SignalSource = (typeof VALID_SIGNAL_SOURCES)[number];
export type OperatingCategory = (typeof VALID_OPERATING_CATEGORIES)[number];
export type ItemStatus = (typeof VALID_ITEM_STATUSES)[number];
export type RevenueStatus = (typeof VALID_REVENUE_STATUSES)[number];
export type PriorityGrade = (typeof VALID_GRADES)[number];
export type CircuitState = 'OPERATIONAL' | 'DEGRADED' | 'OPEN';
export type RouteStackFit = 'HIGH' | 'MEDIUM' | 'LOW' | 'BLOCKED';
export type ApprovalGate = 'READ_ONLY' | 'DRAFT_ONLY' | 'OWNER_APPROVAL_REQUIRED' | 'BLOCKED';

export interface LocationMatrix {
  address: string;
  zip: string;
  lat: number;
  lng: number;
}

export interface MoneyBreakdown {
  potentialUsd: number;
  confirmedUsd: number;
  invoicedUsd: number;
  collectedUsd: number;
  disputedUsd: number;
}

export interface NormalizedItem {
  id: string;
  source: SignalSource;
  externalId?: string;
  vendorId?: string;
  category: OperatingCategory;
  status: ItemStatus;
  revenueStatus: RevenueStatus;
  timestamp: string;
  deadline: string;
  title: string;
  description: string;
  amounts: MoneyBreakdown;
  location?: LocationMatrix;
  estimatedOnSiteHours: number;
  riskFlags: string[];
  exactNextStep: string;
  grade: PriorityGrade;
  approvalGate: ApprovalGate;
  requiresOwnerApproval: boolean;
  effectiveHourlyValue: number;
  travelTimeHours: number;
  travelCostUsd: number;
  routeStackFit: RouteStackFit;
  score: number;
}

export interface HistoricalFailureSignature {
  vendorId: string;
  failureType: 'SLOW_PAYMENT' | 'SCOPE_CREEP' | 'ROUTE_FRICTION' | 'QUALITY_DISPUTE' | 'CANCELLED_AFTER_ACCEPT';
  severity: number;
}

export interface SourceCircuitStatus {
  source: SignalSource;
  state: CircuitState;
  acceptedCount: number;
  quarantinedCount: number;
  lastError?: string;
}

export interface SystemMetrics {
  dailyTargetUsd: number;
  confirmedUsd: number;
  bookableUsd: number;
  opportunityUsd: number;
  paymentProtectionUsd: number;
  revenueGapUsd: number;
  blockedUsd: number;
}

export interface RuntimeResult {
  systemHealth: 'OPERATIONAL' | 'DEGRADED' | 'CRITICAL';
  currentTimestamp: string;
  metrics: SystemMetrics;
  rankedQueue: NormalizedItem[];
  sourceHealth: SourceCircuitStatus[];
  topActions: NormalizedItem[];
  masterDocumentOutput: string;
}

export interface ProcessOptions {
  dailyTargetUsd?: number;
  generatedAt?: string;
}

type RawRecord = Record<string, unknown>;

const BASE_PHOENIX_GLENDALE: LocationMatrix = {
  address: 'Phoenix/Glendale operating vector',
  zip: '85007',
  lat: 33.5387,
  lng: -112.1860,
};

const GRADE_ORDER: Record<PriorityGrade, number> = {
  A: 0,
  B: 1,
  C: 2,
  D: 3,
  F: 4,
};

function isRecord(value: unknown): value is RawRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  if (typeof value !== 'string') {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function asNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string' && value.trim().length > 0) {
    const normalized = Number(value.replace(/[$,]/g, '').trim());
    return Number.isFinite(normalized) ? normalized : undefined;
  }

  return undefined;
}

function asNonNegativeMoney(value: unknown): number {
  const parsed = asNumber(value);
  if (parsed === undefined || parsed < 0) {
    return 0;
  }

  return Math.round(parsed * 100) / 100;
}

function asPositiveHours(value: unknown): number | undefined {
  const parsed = asNumber(value);
  if (parsed === undefined || parsed <= 0 || parsed > 24) {
    return undefined;
  }

  return Math.round(parsed * 100) / 100;
}

function coerceEnum<T extends readonly string[]>(value: unknown, allowed: T): T[number] | undefined {
  const candidate = asString(value)?.toUpperCase().replace(/[\s-]+/g, '_');
  return allowed.includes(candidate ?? '') ? (candidate as T[number]) : undefined;
}

function toIsoDate(value: unknown, fallbackIso: string): { iso: string; verified: boolean } {
  const raw = asString(value);
  if (!raw) {
    return { iso: fallbackIso, verified: false };
  }

  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) {
    return { iso: fallbackIso, verified: false };
  }

  return { iso: parsed.toISOString(), verified: true };
}

function arrayOfStrings(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((entry) => asString(entry))
    .filter((entry): entry is string => Boolean(entry))
    .map((entry) => entry.toUpperCase().replace(/\s+/g, '_'));
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}

function stableHash(input: string): string {
  let hash = 0x811c9dc5;

  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }

  return hash.toString(36).toUpperCase().padStart(7, '0');
}

function normalizeLocation(value: unknown): { location?: LocationMatrix; riskFlags: string[] } {
  if (!isRecord(value)) {
    return { riskFlags: ['LOCATION_UNVERIFIED'] };
  }

  const lat = asNumber(value.lat);
  const lng = asNumber(value.lng);
  const address = asString(value.address) ?? '';
  const zip = asString(value.zip) ?? '';

  if (
    lat === undefined ||
    lng === undefined ||
    lat < 31 ||
    lat > 38 ||
    lng < -116 ||
    lng > -108
  ) {
    return { riskFlags: ['LOCATION_UNVERIFIED'] };
  }

  return {
    location: {
      address,
      zip,
      lat,
      lng,
    },
    riskFlags: address || zip ? [] : ['LOCATION_LABEL_INCOMPLETE'],
  };
}

function extractMoneyBreakdown(raw: RawRecord): MoneyBreakdown {
  const amounts = isRecord(raw.amounts) ? raw.amounts : {};

  const potentialUsd = asNonNegativeMoney(
    amounts.potentialUsd ??
      raw.potentialUsd ??
      raw.potentialValue ??
      raw.pay ??
      raw.amount ??
      raw.value
  );

  return {
    potentialUsd,
    confirmedUsd: asNonNegativeMoney(amounts.confirmedUsd ?? raw.confirmedUsd),
    invoicedUsd: asNonNegativeMoney(amounts.invoicedUsd ?? raw.invoicedUsd),
    collectedUsd: asNonNegativeMoney(amounts.collectedUsd ?? raw.collectedUsd),
    disputedUsd: asNonNegativeMoney(amounts.disputedUsd ?? raw.disputedUsd),
  };
}

function deriveRevenueStatus(raw: RawRecord, status: ItemStatus, amounts: MoneyBreakdown): RevenueStatus {
  const explicit = coerceEnum(raw.revenueStatus, VALID_REVENUE_STATUSES);
  if (explicit) {
    return explicit;
  }

  if (amounts.collectedUsd > 0 || status === 'PAID') {
    return 'COLLECTED';
  }

  if (amounts.disputedUsd > 0) {
    return 'DISPUTED';
  }

  if (amounts.invoicedUsd > 0 || status === 'INVOICED') {
    return 'INVOICED';
  }

  if (amounts.confirmedUsd > 0 || status === 'BOOKED' || status === 'IN_PROGRESS') {
    return 'CONFIRMED';
  }

  if (status === 'READY_TO_ACT') {
    return 'BOOKABLE';
  }

  if (amounts.potentialUsd <= 0) {
    return 'NON_REVENUE';
  }

  return 'OPPORTUNITY';
}

function deriveApprovalGate(category: OperatingCategory, riskFlags: string[], status: ItemStatus): ApprovalGate {
  if (status === 'QUARANTINED' || riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION')) {
    return 'BLOCKED';
  }

  if (category === 'SYSTEM_HEALTH') {
    return 'READ_ONLY';
  }

  if (category === 'PAYMENT_PROTECTION') {
    return 'DRAFT_ONLY';
  }

  return 'OWNER_APPROVAL_REQUIRED';
}

function hasForbiddenAutoScope(category: OperatingCategory, riskFlags: string[], title: string, description: string): boolean {
  if (category !== 'AUTOWORKS') {
    return false;
  }

  const combined = `${riskFlags.join(' ')} ${title} ${description}`;
  return /\b(DIESEL|HEAVY[-_\s]?DUTY|SEMI|BUS|CONSTRUCTION_EQUIPMENT|COMMERCIAL_DIESEL|FLEET_DIESEL)\b/i.test(combined);
}

function deriveNextStep(category: OperatingCategory, status: ItemStatus, riskFlags: string[]): string {
  if (status === 'QUARANTINED') {
    return 'Quarantine this signal, inspect the source payload, and correct the adapter mapping before using it operationally.';
  }

  if (riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION')) {
    return 'Reject this item. It violates Already Here LLC scope rules and should not be accepted.';
  }

  if (riskFlags.includes('LOCATION_UNVERIFIED')) {
    return 'Verify address, ZIP, latitude/longitude, travel window, and pay before using this item in the route stack.';
  }

  switch (category) {
    case 'FIELD_SERVICE':
      return 'Verify scope, site access, closeout requirements, pay, and schedule; then request owner approval before accepting.';
    case 'HAULING':
      return 'Confirm pickup/drop-off addresses, load size, timing, cash terms, and route fit before accepting.';
    case 'AUTOWORKS':
      return 'Confirm gas/light-duty scope, VIN, photos, parts/payment terms, and written authorization before dispatch.';
    case 'PAYMENT_PROTECTION':
      return 'Assemble invoice, closeout proof, payout status, disputed deductions, and owner-approved follow-up draft.';
    case 'DRONE_UAS':
      return 'Verify cost, eligibility, FAA Part 107 requirement, deliverable value, and deadline before applying or pursuing.';
    case 'PROCUREMENT':
      return 'Confirm eligibility, no-cost status, deadline, documentation requirements, and bid/no-bid fit.';
    case 'DISPATCH_INTAKE':
      return 'Review the lead, verify contact details and service scope, then draft a response for owner approval.';
    case 'SYSTEM_HEALTH':
      return 'Inspect the failing system signal and create a fix plan before any production change.';
    case 'UNKNOWN':
      return 'Quarantine this item until source and category are corrected.';
  }
}

function calculateSpatialFriction(location?: LocationMatrix): { travelTimeHours: number; travelCostUsd: number; miles: number } {
  if (!location) {
    return { travelTimeHours: 0, travelCostUsd: 0, miles: 0 };
  }

  const radiusMiles = 3958.8;
  const dLat = ((location.lat - BASE_PHOENIX_GLENDALE.lat) * Math.PI) / 180;
  const dLng = ((location.lng - BASE_PHOENIX_GLENDALE.lng) * Math.PI) / 180;
  const baseLat = (BASE_PHOENIX_GLENDALE.lat * Math.PI) / 180;
  const targetLat = (location.lat * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(baseLat) * Math.cos(targetLat) * Math.sin(dLng / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const roadAdjustedMiles = radiusMiles * c * 1.25;
  const travelTimeHours = roadAdjustedMiles / 45;
  const travelCostUsd = roadAdjustedMiles * 0.67;

  return {
    travelTimeHours: Math.round(travelTimeHours * 100) / 100,
    travelCostUsd: Math.round(travelCostUsd * 100) / 100,
    miles: Math.round(roadAdjustedMiles * 10) / 10,
  };
}

function expectedRankValue(item: Pick<NormalizedItem, 'amounts' | 'category' | 'revenueStatus'>): number {
  if (item.category === 'PAYMENT_PROTECTION') {
    return Math.max(
      item.amounts.disputedUsd,
      item.amounts.invoicedUsd,
      item.amounts.confirmedUsd,
      item.amounts.potentialUsd
    );
  }

  if (item.revenueStatus === 'COLLECTED') {
    return item.amounts.collectedUsd;
  }

  if (item.revenueStatus === 'INVOICED') {
    return item.amounts.invoicedUsd || item.amounts.confirmedUsd;
  }

  if (item.revenueStatus === 'CONFIRMED') {
    return item.amounts.confirmedUsd || item.amounts.potentialUsd;
  }

  if (item.revenueStatus === 'BOOKABLE') {
    return item.amounts.potentialUsd;
  }

  return item.amounts.potentialUsd;
}

function calculateRouteStackFit(category: OperatingCategory, riskFlags: string[], effectiveHourlyValue: number, miles: number): RouteStackFit {
  if (riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION') || category === 'UNKNOWN') {
    return 'BLOCKED';
  }

  if (!['FIELD_SERVICE', 'HAULING', 'AUTOWORKS'].includes(category)) {
    return 'LOW';
  }

  if (riskFlags.includes('LOCATION_UNVERIFIED')) {
    return 'LOW';
  }

  if (effectiveHourlyValue >= 75 && miles <= 25) {
    return 'HIGH';
  }

  if (effectiveHourlyValue >= LABOR_FLOOR_USD_PER_HOUR && miles <= 45) {
    return 'MEDIUM';
  }

  return 'LOW';
}

function gradeItem(item: Omit<NormalizedItem, 'grade' | 'score' | 'routeStackFit'>, miles: number, history: HistoricalFailureSignature[]): {
  grade: PriorityGrade;
  riskFlags: string[];
  score: number;
  routeStackFit: RouteStackFit;
} {
  const riskFlags = [...item.riskFlags];

  if (hasForbiddenAutoScope(item.category, riskFlags, item.title, item.description)) {
    riskFlags.push('FORBIDDEN_SCOPE_EXCLUSION');
  }

  const historicalRisk = history.some((failure) => {
    const severity = Number.isFinite(failure.severity) ? failure.severity : 0;
    return item.vendorId === failure.vendorId && severity >= 0.7;
  });

  if (historicalRisk) {
    riskFlags.push('HIGH_RISK_VENDOR_LAG');
  }

  if (item.source === 'UNKNOWN' || item.category === 'UNKNOWN' || item.status === 'QUARANTINED') {
    return {
      grade: 'F',
      riskFlags: unique([...riskFlags, 'QUARANTINED_INPUT']),
      score: -1000,
      routeStackFit: 'BLOCKED',
    };
  }

  if (riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION')) {
    return {
      grade: 'F',
      riskFlags: unique(riskFlags),
      score: -900,
      routeStackFit: 'BLOCKED',
    };
  }

  let grade: PriorityGrade = 'B';
  let score = expectedRankValue(item) / 10;

  if (item.category === 'PAYMENT_PROTECTION') {
    score += 25;
    if (expectedRankValue(item) >= 250) {
      grade = 'A';
    }
  }

  if (item.category === 'SYSTEM_HEALTH') {
    score += riskFlags.includes('PRODUCTION_BLOCKER') ? 30 : 10;
    grade = riskFlags.includes('PRODUCTION_BLOCKER') ? 'A' : 'B';
  }

  if (['FIELD_SERVICE', 'HAULING', 'AUTOWORKS'].includes(item.category)) {
    if (item.effectiveHourlyValue >= 90) {
      grade = 'A';
      score += 30;
    } else if (item.effectiveHourlyValue >= LABOR_FLOOR_USD_PER_HOUR) {
      grade = 'B';
      score += 15;
    } else if (expectedRankValue(item) > 0) {
      grade = 'C';
      riskFlags.push('MARGIN_BELOW_LABOR_FLOOR');
      score -= 15;
    }
  }

  if (item.revenueStatus === 'OPPORTUNITY' && grade === 'A') {
    grade = 'B';
    riskFlags.push('UNCONFIRMED_REVENUE');
  }

  if (riskFlags.includes('LOCATION_UNVERIFIED') && ['FIELD_SERVICE', 'HAULING', 'AUTOWORKS'].includes(item.category)) {
    grade = grade === 'A' ? 'B' : grade;
    score -= 10;
  }

  if (riskFlags.includes('HIGH_RISK_VENDOR_LAG')) {
    grade = grade === 'A' ? 'B' : 'C';
    score -= 20;
  }

  const routeStackFit = calculateRouteStackFit(item.category, riskFlags, item.effectiveHourlyValue, miles);

  if (routeStackFit === 'HIGH') {
    score += 15;
  } else if (routeStackFit === 'MEDIUM') {
    score += 8;
  } else if (routeStackFit === 'LOW' && ['FIELD_SERVICE', 'HAULING', 'AUTOWORKS'].includes(item.category)) {
    score -= 4;
  }

  return {
    grade,
    riskFlags: unique(riskFlags),
    score: Math.round(score * 100) / 100,
    routeStackFit,
  };
}

function buildDeterministicId(source: SignalSource, category: OperatingCategory, raw: RawRecord, index: number, timestamp: string): string {
  const externalId = asString(raw.externalId) ?? asString(raw.id) ?? asString(raw.threadId) ?? asString(raw.workOrderId) ?? `INDEX_${index}`;
  return `DC_${stableHash(`${source}|${category}|${externalId}|${timestamp}`)}`;
}

export function normalizeDailyCommandInputs(rawInputs: unknown[], generatedAt = new Date().toISOString()): NormalizedItem[] {
  return rawInputs.map((rawInput, index) => {
    const raw = isRecord(rawInput) ? rawInput : {};
    const riskFlags = isRecord(rawInput) ? arrayOfStrings(raw.flags ?? raw.riskFlags ?? raw.tags) : ['INVALID_PAYLOAD'];

    const source = coerceEnum(raw.source, VALID_SIGNAL_SOURCES) ?? 'UNKNOWN';
    const category = coerceEnum(raw.category, VALID_OPERATING_CATEGORIES) ?? 'UNKNOWN';
    const status = coerceEnum(raw.status, VALID_ITEM_STATUSES) ?? (source === 'UNKNOWN' || category === 'UNKNOWN' ? 'QUARANTINED' : 'NEW');

    if (source === 'UNKNOWN') {
      riskFlags.push('INVALID_SOURCE');
    }

    if (category === 'UNKNOWN') {
      riskFlags.push('INVALID_CATEGORY');
    }

    const timestamp = toIsoDate(raw.timestamp ?? raw.date ?? generatedAt, generatedAt);
    if (!timestamp.verified) {
      riskFlags.push('TIMESTAMP_UNVERIFIED');
    }

    const deadline = toIsoDate(raw.deadline ?? raw.dueAt ?? raw.scheduledAt ?? generatedAt, generatedAt);
    if (!deadline.verified) {
      riskFlags.push('DEADLINE_UNVERIFIED');
    }

    const locationResult = normalizeLocation(raw.location);
    const routeSensitive = ['FIELD_SERVICE', 'HAULING', 'AUTOWORKS'].includes(category);
    if (routeSensitive) {
      riskFlags.push(...locationResult.riskFlags);
    }

    const estimatedOnSiteHours = asPositiveHours(raw.estimatedOnSiteHours ?? raw.durationHours ?? raw.hours) ?? 1;
    if (!asPositiveHours(raw.estimatedOnSiteHours ?? raw.durationHours ?? raw.hours)) {
      riskFlags.push('DURATION_DEFAULTED');
    }

    const amounts = extractMoneyBreakdown(raw);
    const title = asString(raw.title ?? raw.subject ?? raw.name) ?? `${category} signal`;
    const description = asString(raw.description ?? raw.summary ?? raw.body) ?? '';
    const vendorId = asString(raw.vendorId ?? raw.vendor ?? raw.provider);
    const externalId = asString(raw.externalId ?? raw.id ?? raw.threadId ?? raw.workOrderId);

    const revenueStatus = deriveRevenueStatus(raw, status, amounts);
    const friction = calculateSpatialFriction(locationResult.location);
    const rankValue = expectedRankValue({ amounts, category, revenueStatus });
    const totalHours = estimatedOnSiteHours + friction.travelTimeHours;
    const effectiveHourlyValue = totalHours > 0 ? Math.max(0, (rankValue - friction.travelCostUsd) / totalHours) : 0;

    const itemWithoutRank: Omit<NormalizedItem, 'grade' | 'score' | 'routeStackFit'> = {
      id: buildDeterministicId(source, category, raw, index, timestamp.iso),
      source,
      externalId,
      vendorId,
      category,
      status,
      revenueStatus,
      timestamp: timestamp.iso,
      deadline: deadline.iso,
      title,
      description,
      amounts,
      location: locationResult.location,
      estimatedOnSiteHours,
      riskFlags: unique(riskFlags),
      exactNextStep: asString(raw.exactNextStep ?? raw.nextStep) ?? deriveNextStep(category, status, riskFlags),
      grade: 'B',
      approvalGate: 'OWNER_APPROVAL_REQUIRED',
      requiresOwnerApproval: true,
      effectiveHourlyValue: Math.round(effectiveHourlyValue * 100) / 100,
      travelTimeHours: friction.travelTimeHours,
      travelCostUsd: friction.travelCostUsd,
    };

    const approvalGate = deriveApprovalGate(category, itemWithoutRank.riskFlags, status);

    return {
      ...itemWithoutRank,
      approvalGate,
      requiresOwnerApproval: approvalGate === 'OWNER_APPROVAL_REQUIRED' || approvalGate === 'DRAFT_ONLY',
      grade: 'B',
      score: 0,
      routeStackFit: 'LOW',
    };
  });
}

export function rankDailyCommandItems(items: NormalizedItem[], history: HistoricalFailureSignature[] = []): NormalizedItem[] {
  const ranked = items.map((item) => {
    const friction = calculateSpatialFriction(item.location);
    const result = gradeItem(item, friction.miles, history);
    const approvalGate = deriveApprovalGate(item.category, result.riskFlags, item.status);

    return {
      ...item,
      riskFlags: result.riskFlags,
      grade: result.grade,
      score: result.score,
      routeStackFit: result.routeStackFit,
      approvalGate,
      requiresOwnerApproval: approvalGate === 'OWNER_APPROVAL_REQUIRED' || approvalGate === 'DRAFT_ONLY',
      exactNextStep: result.riskFlags.includes('FORBIDDEN_SCOPE_EXCLUSION')
        ? deriveNextStep(item.category, item.status, result.riskFlags)
        : item.exactNextStep,
    };
  });

  return ranked.sort((left, right) => {
    const gradeDelta = GRADE_ORDER[left.grade] - GRADE_ORDER[right.grade];
    if (gradeDelta !== 0) {
      return gradeDelta;
    }

    const scoreDelta = right.score - left.score;
    if (scoreDelta !== 0) {
      return scoreDelta;
    }

    return right.effectiveHourlyValue - left.effectiveHourlyValue;
  });
}

export function buildSourceHealth(items: NormalizedItem[]): SourceCircuitStatus[] {
  const bySource = new Map<SignalSource, SourceCircuitStatus>();

  for (const source of VALID_SIGNAL_SOURCES) {
    bySource.set(source, {
      source,
      state: 'OPERATIONAL',
      acceptedCount: 0,
      quarantinedCount: 0,
    });
  }

  for (const item of items) {
    const current = bySource.get(item.source);
    if (!current) {
      continue;
    }

    const quarantined = item.status === 'QUARANTINED' || item.riskFlags.includes('QUARANTINED_INPUT');
    current.acceptedCount += quarantined ? 0 : 1;
    current.quarantinedCount += quarantined ? 1 : 0;

    if (quarantined) {
      current.state = current.quarantinedCount >= 3 ? 'OPEN' : 'DEGRADED';
      current.lastError = 'Input quarantine threshold triggered for this source.';
    }
  }

  return Array.from(bySource.values()).filter(
    (status) => status.acceptedCount > 0 || status.quarantinedCount > 0 || status.source === 'UNKNOWN'
  );
}

export function calculateMetrics(items: NormalizedItem[], dailyTargetUsd = DAILY_REVENUE_TARGET_USD): SystemMetrics {
  const confirmedUsd = items.reduce((sum, item) => {
    if (item.grade === 'F') {
      return sum;
    }

    if (item.revenueStatus === 'COLLECTED') {
      return sum + item.amounts.collectedUsd;
    }

    if (item.revenueStatus === 'INVOICED') {
      return sum + item.amounts.invoicedUsd;
    }

    if (item.revenueStatus === 'CONFIRMED') {
      return sum + (item.amounts.confirmedUsd || item.amounts.potentialUsd);
    }

    return sum;
  }, 0);

  const bookableUsd = items.reduce((sum, item) => {
    if (item.grade === 'F') {
      return sum;
    }

    return item.revenueStatus === 'BOOKABLE' ? sum + item.amounts.potentialUsd : sum;
  }, 0);

  const opportunityUsd = items.reduce((sum, item) => {
    if (item.grade === 'F') {
      return sum;
    }

    return item.revenueStatus === 'OPPORTUNITY' ? sum + item.amounts.potentialUsd : sum;
  }, 0);

  const paymentProtectionUsd = items.reduce((sum, item) => {
    if (item.category !== 'PAYMENT_PROTECTION' || item.grade === 'F') {
      return sum;
    }

    return sum + expectedRankValue(item);
  }, 0);

  const blockedUsd = items.reduce((sum, item) => {
    return item.grade === 'F' ? sum + expectedRankValue(item) : sum;
  }, 0);

  return {
    dailyTargetUsd,
    confirmedUsd: Math.round(confirmedUsd * 100) / 100,
    bookableUsd: Math.round(bookableUsd * 100) / 100,
    opportunityUsd: Math.round(opportunityUsd * 100) / 100,
    paymentProtectionUsd: Math.round(paymentProtectionUsd * 100) / 100,
    revenueGapUsd: Math.max(0, Math.round((dailyTargetUsd - confirmedUsd - bookableUsd) * 100) / 100),
    blockedUsd: Math.round(blockedUsd * 100) / 100,
  };
}

export function renderDailyCommandMarkdown(result: Omit<RuntimeResult, 'masterDocumentOutput'>): string {
  const rows = result.rankedQueue
    .map((item) => {
      const riskFlags = item.riskFlags.length > 0 ? item.riskFlags.join(', ') : 'NONE';
      return `| ${item.id} | ${item.source} | ${item.category} | ${item.status} | ${item.revenueStatus} | $${expectedRankValue(item).toFixed(2)} | $${item.effectiveHourlyValue.toFixed(2)}/hr | ${item.routeStackFit} | Grade ${item.grade} | ${riskFlags} |`;
    })
    .join('\n');

  const topActions = result.topActions
    .map((item, index) => `${index + 1}. ${item.title} — Grade ${item.grade}. ${item.exactNextStep}`)
    .join('\n');

  return `# Already Here LLC — Daily Command Engine Export
**System Status:** ${result.systemHealth}  
**Generation Timestamp:** ${result.currentTimestamp}  
**Daily Revenue Target:** $${result.metrics.dailyTargetUsd.toFixed(2)}

## Top Actions
${topActions || 'No actionable items received in this run.'}

## Money Control
- Confirmed revenue: $${result.metrics.confirmedUsd.toFixed(2)}
- Bookable revenue: $${result.metrics.bookableUsd.toFixed(2)}
- Opportunity value not counted as confirmed: $${result.metrics.opportunityUsd.toFixed(2)}
- Payment protection exposure: $${result.metrics.paymentProtectionUsd.toFixed(2)}
- Revenue gap: $${result.metrics.revenueGapUsd.toFixed(2)}
- Blocked/rejected value: $${result.metrics.blockedUsd.toFixed(2)}

## Ranked Queue
| Item ID | Source | Category | Status | Revenue Status | Rank Value | EHV | Route Fit | Grade | Risk Flags |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- | :--- | :--- |
${rows || '| NONE | NONE | NONE | NONE | NONE | $0.00 | $0.00/hr | LOW | F | NO_INPUTS |'}

## Control Boundaries
- Owner approval is required before accepting work, sending messages, submitting forms, moving money, changing books, or modifying production.
- Opportunity value is not counted as confirmed revenue.
- Diesel and heavy-duty AutoWorks scope is blocked by default.
- Invalid source/category payloads are quarantined instead of silently normalized.
`;
}

export class DailyCommandOrchestrator {
  processLiveMatrix(
    rawInputs: unknown[],
    history: HistoricalFailureSignature[] = [],
    options: ProcessOptions = {}
  ): RuntimeResult {
    const currentTimestamp = options.generatedAt ?? new Date().toISOString();

    try {
      const normalized = normalizeDailyCommandInputs(rawInputs, currentTimestamp);
      const rankedQueue = rankDailyCommandItems(normalized, history);
      const metrics = calculateMetrics(rankedQueue, options.dailyTargetUsd ?? DAILY_REVENUE_TARGET_USD);
      const sourceHealth = buildSourceHealth(rankedQueue);
      const hasOpenCircuit = sourceHealth.some((source) => source.state === 'OPEN');
      const hasQuarantined = rankedQueue.some((item) => item.status === 'QUARANTINED');
      const hasCriticalSystemItem = rankedQueue.some(
        (item) => item.category === 'SYSTEM_HEALTH' && item.grade === 'A' && item.riskFlags.includes('PRODUCTION_BLOCKER')
      );

      const systemHealth = hasOpenCircuit || hasCriticalSystemItem ? 'CRITICAL' : hasQuarantined ? 'DEGRADED' : 'OPERATIONAL';
      const topActions = rankedQueue.filter((item) => item.grade !== 'F').slice(0, 3);
      const baseResult = {
        systemHealth,
        currentTimestamp,
        metrics,
        rankedQueue,
        sourceHealth,
        topActions,
      };

      return {
        ...baseResult,
        masterDocumentOutput: renderDailyCommandMarkdown(baseResult),
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown Daily Command core fault';
      const resultWithoutMarkdown = {
        systemHealth: 'CRITICAL' as const,
        currentTimestamp,
        metrics: {
          dailyTargetUsd: options.dailyTargetUsd ?? DAILY_REVENUE_TARGET_USD,
          confirmedUsd: 0,
          bookableUsd: 0,
          opportunityUsd: 0,
          paymentProtectionUsd: 0,
          revenueGapUsd: options.dailyTargetUsd ?? DAILY_REVENUE_TARGET_USD,
          blockedUsd: 0,
        },
        rankedQueue: [],
        sourceHealth: [
          {
            source: 'UNKNOWN' as const,
            state: 'OPEN' as const,
            acceptedCount: 0,
            quarantinedCount: 1,
            lastError: message,
          },
        ],
        topActions: [],
      };

      return {
        ...resultWithoutMarkdown,
        masterDocumentOutput: renderDailyCommandMarkdown(resultWithoutMarkdown),
      };
    }
  }
}

export function createDailyCommandSnapshot(
  rawInputs: unknown[] = [],
  history: HistoricalFailureSignature[] = [],
  options: ProcessOptions = {}
): RuntimeResult {
  return new DailyCommandOrchestrator().processLiveMatrix(rawInputs, history, options);
}

export function buildDailyCommandVerificationFeed(): unknown[] {
  return [
    {
      id: 'WM_01',
      source: 'WORKMARKET',
      category: 'FIELD_SERVICE',
      status: 'READY_TO_ACT',
      revenueStatus: 'BOOKABLE',
      pay: 220,
      durationHours: 2,
      location: { address: 'Gilbert, AZ', zip: '85234', lat: 33.3524, lng: -111.7890 },
      flags: [],
      title: 'Gilbert smart-hands dispatch',
    },
    {
      id: 'AW_02',
      source: 'GMAIL',
      category: 'AUTOWORKS',
      status: 'READY_TO_ACT',
      revenueStatus: 'BOOKABLE',
      pay: 160,
      durationHours: 1.5,
      location: { address: 'Peoria, AZ', zip: '85345', lat: 33.5806, lng: -112.2374 },
      flags: [],
      title: 'Peoria light-duty AutoWorks call',
    },
    {
      id: 'FN_03',
      source: 'FIELD_NATION',
      category: 'FIELD_SERVICE',
      status: 'NEW',
      revenueStatus: 'OPPORTUNITY',
      pay: 90,
      durationHours: 1,
      location: { address: 'Queen Creek, AZ', zip: '85142', lat: 33.2484, lng: -111.6342 },
      flags: [],
      title: 'Queen Creek low-pay printer call',
    },
    {
      id: 'AW_04',
      source: 'GMAIL',
      category: 'AUTOWORKS',
      status: 'NEW',
      revenueStatus: 'OPPORTUNITY',
      pay: 1200,
      durationHours: 8,
      location: { address: 'Phoenix, AZ', zip: '85001', lat: 33.4484, lng: -112.0740 },
      flags: ['DIESEL'],
      title: 'Diesel fleet repair request',
    },
  ];
}
