import { commandCenterStatus } from '@/app/command-center/statusData';

export type Role = 'admin' | 'operator' | 'auditor';

export const ROLES: Role[] = ['admin', 'operator', 'auditor'];

export const ROLE_ACCESS: Record<Role, string[]> = {
  admin: Object.keys(commandCenterStatus),
  operator: ['agents', 'logs', 'workflows', 'changelog'],
  auditor: ['security', 'costs', 'approvals', 'changelog', 'connectors'],
};

export function normalizeRole(role?: string | null): Role {
  return role && ROLES.includes(role as Role) ? (role as Role) : 'operator';
}

export function canAccess(role: Role | string, section: string): boolean {
  const r = normalizeRole(role);
  return ROLE_ACCESS[r].includes(section);
}
