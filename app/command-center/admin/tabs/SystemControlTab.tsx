'use client';

import { useState, useEffect } from 'react';

interface SystemControlProps {
  session: any;
  lastUpdate: Date;
}

interface SystemState {
  systemA: { enabled: boolean; status: string };
  systemB: { enabled: boolean; status: string };
  portfolio: {
    balance: number;
    positions: Array<{ symbol: string; quantity: number; value: number }>;
  };
  dailyDrawdown: number;
  riskGateOverride: { active: boolean; expiresAt?: number };
}

const SystemControlTab = ({ session, lastUpdate }: SystemControlProps) => {
  const [systemState, setSystemState] = useState<SystemState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchSystemState = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/system-state', {
        cache: 'no-store',
      });

      if (!res.ok) throw new Error(`Failed to fetch system state: ${res.status}`);
      const data = await res.json();
      setSystemState(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system state');
    } finally {
      setLoading(false);
    }
  };

  const executeAction = async (action: string, params: any = {}) => {
    try {
      setActionLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/execute-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, params, timestamp: new Date().toISOString() }),
        cache: 'no-store',
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `Action failed: ${res.status}`);
      }

      const result = await res.json();
      setConfirmAction(null);
      await fetchSystemState();
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemState();
    const interval = setInterval(fetchSystemState, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !systemState) {
    return (
      <div
        style={{
          padding: 24,
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          background: 'rgba(15, 23, 42, 0.72)',
          textAlign: 'center',
          color: '#a8bed0',
        }}
      >
        Loading system state...
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      {error && (
        <div
          style={{
            padding: 16,
            border: '1px solid rgba(248, 113, 113, 0.5)',
            borderRadius: 12,
            background: 'rgba(127, 29, 29, 0.15)',
            color: '#f87171',
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {/* Trading Systems Control */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Trading Systems</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          {/* System A */}
          <div
            style={{
              padding: 16,
              border: '1px solid rgba(125, 211, 252, 0.15)',
              borderRadius: 8,
              background: 'rgba(15, 23, 42, 0.4)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 16 }}>System A (Primary)</h3>
                <p style={{ margin: '8px 0 0 0', color: '#a8bed0', fontSize: 12 }}>
                  Status:{' '}
                  <span style={{ color: systemState?.systemA.enabled ? '#4ade80' : '#f87171', fontWeight: 600 }}>
                    {systemState?.systemA.status || 'Unknown'}
                  </span>
                </p>
              </div>
              <span
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: systemState?.systemA.enabled ? '#4ade80' : '#f87171',
                }}
              />
            </div>
            <button
              onClick={() => executeAction('toggle-system', { system: 'A' })}
              disabled={actionLoading}
              style={{
                marginTop: 12,
                width: '100%',
                padding: '8px 12px',
                background: systemState?.systemA.enabled
                  ? 'rgba(248, 113, 113, 0.2)'
                  : 'rgba(74, 222, 128, 0.2)',
                color: systemState?.systemA.enabled ? '#f87171' : '#4ade80',
                border: `1px solid ${systemState?.systemA.enabled ? '#f87171' : '#4ade80'}`,
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 500,
                opacity: actionLoading ? 0.5 : 1,
              }}
            >
              {actionLoading ? 'Updating...' : systemState?.systemA.enabled ? 'Disable System' : 'Enable System'}
            </button>
          </div>

          {/* System B */}
          <div
            style={{
              padding: 16,
              border: '1px solid rgba(125, 211, 252, 0.15)',
              borderRadius: 8,
              background: 'rgba(15, 23, 42, 0.4)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 16 }}>System B (Secondary)</h3>
                <p style={{ margin: '8px 0 0 0', color: '#a8bed0', fontSize: 12 }}>
                  Status:{' '}
                  <span style={{ color: systemState?.systemB.enabled ? '#4ade80' : '#f87171', fontWeight: 600 }}>
                    {systemState?.systemB.status || 'Unknown'}
                  </span>
                </p>
              </div>
              <span
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: systemState?.systemB.enabled ? '#4ade80' : '#f87171',
                }}
              />
            </div>
            <button
              onClick={() => executeAction('toggle-system', { system: 'B' })}
              disabled={actionLoading}
              style={{
                marginTop: 12,
                width: '100%',
                padding: '8px 12px',
                background: systemState?.systemB.enabled
                  ? 'rgba(248, 113, 113, 0.2)'
                  : 'rgba(74, 222, 128, 0.2)',
                color: systemState?.systemB.enabled ? '#f87171' : '#4ade80',
                border: `1px solid ${systemState?.systemB.enabled ? '#f87171' : '#4ade80'}`,
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 500,
                opacity: actionLoading ? 0.5 : 1,
              }}
            >
              {actionLoading ? 'Updating...' : systemState?.systemB.enabled ? 'Disable System' : 'Enable System'}
            </button>
          </div>
        </div>
      </div>

      {/* Portfolio Status */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Portfolio Status</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 20 }}>
          <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
            <p style={{ margin: 0, color: '#a8bed0', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Total Balance
            </p>
            <p style={{ margin: '8px 0 0 0', color: '#4ade80', fontSize: 24, fontWeight: 700 }}>
              ${(systemState?.portfolio.balance || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
            </p>
          </div>

          <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
            <p style={{ margin: 0, color: '#a8bed0', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Daily Drawdown
            </p>
            <p
              style={{
                margin: '8px 0 0 0',
                color: (systemState?.dailyDrawdown || 0) > 2 ? '#f87171' : '#4ade80',
                fontSize: 24,
                fontWeight: 700,
              }}
            >
              {(systemState?.dailyDrawdown || 0).toFixed(2)}%
            </p>
          </div>

          <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
            <p style={{ margin: 0, color: '#a8bed0', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Open Positions
            </p>
            <p style={{ margin: '8px 0 0 0', color: '#7dd3fc', fontSize: 24, fontWeight: 700 }}>
              {systemState?.portfolio.positions.length || 0}
            </p>
          </div>
        </div>

        {systemState?.portfolio.positions.length ? (
          <div>
            <h3 style={{ margin: '0 0 12px 0', fontSize: 14, color: '#a8bed0' }}>Open Positions</h3>
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 13,
                  color: '#e5f7ff',
                }}
              >
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(125, 211, 252, 0.25)' }}>
                    <th style={{ padding: '8px', textAlign: 'left', color: '#7dd3fc', fontWeight: 600 }}>
                      Symbol
                    </th>
                    <th style={{ padding: '8px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                      Quantity
                    </th>
                    <th style={{ padding: '8px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                      Value
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {systemState.portfolio.positions.map((pos, idx) => (
                    <tr
                      key={idx}
                      style={{
                        borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
                        background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.3)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '8px' }}>{pos.symbol}</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{pos.quantity}</td>
                      <td style={{ padding: '8px', textAlign: 'right', color: '#4ade80' }}>
                        ${pos.value.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p style={{ color: '#a8bed0', fontSize: 12, margin: 0 }}>No open positions</p>
        )}
      </div>

      {/* Risk Controls */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Risk Management</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          {/* Risk Gate Override */}
          <div
            style={{
              padding: 16,
              border: '1px solid rgba(125, 211, 252, 0.15)',
              borderRadius: 8,
              background: 'rgba(15, 23, 42, 0.4)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
              <div>
                <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 14 }}>Risk Gate Override</h3>
                <p style={{ margin: '4px 0 0 0', color: '#a8bed0', fontSize: 11 }}>
                  Temporarily allow higher risk trading
                </p>
              </div>
              <span
                style={{
                  display: 'inline-block',
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: systemState?.riskGateOverride.active ? '#f59e0b' : '#6b7280',
                }}
              />
            </div>

            {systemState?.riskGateOverride.active && systemState?.riskGateOverride.expiresAt && (
              <p style={{ margin: '0 0 12px 0', color: '#f59e0b', fontSize: 11 }}>
                Active until{' '}
                {new Date(systemState.riskGateOverride.expiresAt).toLocaleTimeString()}
              </p>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <button
                onClick={() => {
                  if (!systemState?.riskGateOverride.active) {
                    setConfirmAction('risk-override-enable');
                  } else {
                    executeAction('toggle-risk-override', { enable: false });
                  }
                }}
                disabled={actionLoading}
                style={{
                  padding: '8px 12px',
                  background: systemState?.riskGateOverride.active
                    ? 'rgba(74, 222, 128, 0.2)'
                    : 'rgba(245, 158, 11, 0.2)',
                  color: systemState?.riskGateOverride.active ? '#4ade80' : '#f59e0b',
                  border: `1px solid ${systemState?.riskGateOverride.active ? '#4ade80' : '#f59e0b'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: 11,
                  fontWeight: 500,
                }}
              >
                {systemState?.riskGateOverride.active ? 'Active' : 'Enable'}
              </button>
              {systemState?.riskGateOverride.active && (
                <button
                  onClick={() => executeAction('toggle-risk-override', { enable: false })}
                  disabled={actionLoading}
                  style={{
                    padding: '8px 12px',
                    background: 'rgba(248, 113, 113, 0.2)',
                    color: '#f87171',
                    border: '1px solid #f87171',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontSize: 11,
                    fontWeight: 500,
                  }}
                >
                  Disable
                </button>
              )}
            </div>
          </div>

          {/* Emergency Shutdown */}
          <div
            style={{
              padding: 16,
              border: '1px solid rgba(248, 113, 113, 0.25)',
              borderRadius: 8,
              background: 'rgba(127, 29, 29, 0.1)',
            }}
          >
            <h3 style={{ margin: '0 0 12px 0', color: '#f87171', fontSize: 14 }}>Emergency Shutdown</h3>
            <p style={{ margin: '0 0 12px 0', color: '#a8bed0', fontSize: 11 }}>
              Immediately close all positions and halt trading (2 second guaranteed)
            </p>
            <button
              onClick={() => setConfirmAction('emergency-shutdown')}
              disabled={actionLoading}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: 'rgba(248, 113, 113, 0.3)',
                color: '#f87171',
                border: '1px solid #f87171',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
                opacity: actionLoading ? 0.5 : 1,
              }}
            >
              EMERGENCY SHUTDOWN
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {confirmAction && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#080b12',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 12,
              padding: 32,
              maxWidth: 400,
            }}
          >
            <h2 style={{ margin: '0 0 12px 0', fontSize: 18, color: '#e5f7ff' }}>
              {confirmAction === 'emergency-shutdown' ? 'Confirm Emergency Shutdown' : 'Enable Risk Override'}
            </h2>
            <p style={{ margin: '0 0 24px 0', color: '#a8bed0', lineHeight: 1.6, fontSize: 14 }}>
              {confirmAction === 'emergency-shutdown'
                ? 'This will immediately close ALL positions and halt all trading systems. This action cannot be undone.'
                : 'This will temporarily allow higher risk trading. Be cautious with capital allocation.'}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <button
                onClick={() => setConfirmAction(null)}
                disabled={actionLoading}
                style={{
                  padding: '10px',
                  background: 'rgba(125, 211, 252, 0.1)',
                  color: '#7dd3fc',
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 500,
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (confirmAction === 'emergency-shutdown') {
                    executeAction('emergency-shutdown');
                  } else if (confirmAction === 'risk-override-enable') {
                    executeAction('toggle-risk-override', { enable: true, durationMinutes: 30 });
                  }
                }}
                disabled={actionLoading}
                style={{
                  padding: '10px',
                  background: confirmAction === 'emergency-shutdown' ? 'rgba(248, 113, 113, 0.3)' : 'rgba(245, 158, 11, 0.2)',
                  color: confirmAction === 'emergency-shutdown' ? '#f87171' : '#f59e0b',
                  border: `1px solid ${confirmAction === 'emergency-shutdown' ? '#f87171' : '#f59e0b'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 600,
                  opacity: actionLoading ? 0.5 : 1,
                }}
              >
                {actionLoading ? 'Executing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemControlTab;
