export type HealthStatus = 'pass' | 'fail';

export interface HealthPayload {
  ok: boolean;
  service: string;
  version: string;
  mode: string;
  healthScore: number;
  paidAdaptersEnabled: boolean;
  externalExecutionEnabled: boolean;
  staleSourcePresent: boolean;
  deploymentBlockers: string[];
  checks: Record<string, HealthStatus>;
  timestamp: string;
}

export function buildHealthPayload(options?: { root?: string }): HealthPayload;
