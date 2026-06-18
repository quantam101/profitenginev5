'use client';

import { useState, useEffect } from 'react';

interface SystemHealthProps {
  session: any;
  lastUpdate: Date;
}

interface HealthStatus {
  apiStatus: {
    clientAPI: boolean;
    dailyAlerts: boolean;
    runtime: boolean;
  };
  database: {
    size: number;
    recordCount: number;
    lastBackup: string;
  };
  backup: {
    status: 'active' | 'pending' | 'failed';
    lastBackupTime: string;
    nextBackupTime: string;
  };
  robinhood: {
    connected: boolean;
    accountStatus: string;
    lastSync: string;
  };
  errors: Array<{
    id: string;
    timestamp: string;
    service: string;
    message: string;
    severity: 'warning' | 'error' | 'critical';
  }>;
}

const SystemHealthTab = ({ session, lastUpdate }: SystemHealthProps) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/health', {
        cache: 'no-store',
      });

      if (!res.ok) throw new Error(`Failed to fetch health status: ${res.status}`);
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  const getStatusColor = (status: boolean | string) => {
    if (typeof status === 'boolean') {
      return status ? '#4ade80' : '#f87171';
    }
    switch (status) {
      case 'active':
      case 'connected':
        return '#4ade80';
      case 'pending':
        return '#f59e0b';
      case 'failed':
      case 'error':
        return '#f87171';
      default:
        return '#7dd3fc';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '#f87171';
      case 'error':
        return '#fb923c';
      case 'warning':
        return '#f59e0b';
      default:
        return '#a8bed0';
    }
  };

  if (loading && !health) {
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
        Loading system health...
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

      {/* API Status */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>API Health</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {health?.apiStatus && Object.entries(health.apiStatus).map(([key, status]) => (
            <div
              key={key}
              style={{
                padding: 16,
                border: '1px solid rgba(125, 211, 252, 0.15)',
                borderRadius: 8,
                background: 'rgba(15, 23, 42, 0.4)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 14 }}>
                    {key
                      .replace(/([A-Z])/g, ' $1')
                      .replace(/^./, (str) => str.toUpperCase())}
                  </h3>
                  <p
                    style={{
                      margin: '4px 0 0 0',
                      color: getStatusColor(status),
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {status ? 'OPERATIONAL' : 'DOWN'}
                  </p>
                </div>
                <span
                  style={{
                    display: 'inline-block',
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: getStatusColor(status),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Database Status */}
      {health?.database && (
        <div
          style={{
            border: '1px solid rgba(125, 211, 252, 0.25)',
            borderRadius: 12,
            padding: 24,
            background: 'rgba(15, 23, 42, 0.72)',
          }}
        >
          <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Database Status</h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
              <p style={{ margin: 0, color: '#a8bed0', fontSize: 11, textTransform: 'uppercase' }}>
                Database Size
              </p>
              <p style={{ margin: '8px 0 0 0', color: '#7dd3fc', fontSize: 18, fontWeight: 700 }}>
                {(health.database.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>

            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
              <p style={{ margin: 0, color: '#a8bed0', fontSize: 11, textTransform: 'uppercase' }}>
                Total Records
              </p>
              <p style={{ margin: '8px 0 0 0', color: '#7dd3fc', fontSize: 18, fontWeight: 700 }}>
                {health.database.recordCount.toLocaleString()}
              </p>
            </div>

            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 8 }}>
              <p style={{ margin: 0, color: '#a8bed0', fontSize: 11, textTransform: 'uppercase' }}>
                Last Backup
              </p>
              <p style={{ margin: '8px 0 0 0', color: '#4ade80', fontSize: 13 }}>
                {new Date(health.database.lastBackup).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Backup Status */}
      {health?.backup && (
        <div
          style={{
            border: '1px solid rgba(125, 211, 252, 0.25)',
            borderRadius: 12,
            padding: 24,
            background: 'rgba(15, 23, 42, 0.72)',
          }}
        >
          <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Backup Status</h2>

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
                <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 14 }}>Automated Backups</h3>
                <p
                  style={{
                    margin: '4px 0 0 0',
                    color: getStatusColor(health.backup.status),
                    fontSize: 12,
                    fontWeight: 600,
                    textTransform: 'uppercase',
                  }}
                >
                  {health.backup.status}
                </p>
              </div>
              <span
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: getStatusColor(health.backup.status),
                }}
              />
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
              }}
            >
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.5)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 11 }}>Last Backup</p>
                <p style={{ margin: '4px 0 0 0', color: '#7dd3fc', fontSize: 12 }}>
                  {new Date(health.backup.lastBackupTime).toLocaleString()}
                </p>
              </div>

              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.5)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 11 }}>Next Backup</p>
                <p style={{ margin: '4px 0 0 0', color: '#7dd3fc', fontSize: 12 }}>
                  {new Date(health.backup.nextBackupTime).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Robinhood Connection */}
      {health?.robinhood && (
        <div
          style={{
            border: '1px solid rgba(125, 211, 252, 0.25)',
            borderRadius: 12,
            padding: 24,
            background: 'rgba(15, 23, 42, 0.72)',
          }}
        >
          <h2 style={{ margin: '0 0 20px 0', fontSize: 18, color: '#e5f7ff' }}>Robinhood Connection</h2>

          <div style={{ display: 'grid', gap: 12 }}>
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
                  <h3 style={{ margin: 0, color: '#e5f7ff', fontSize: 14 }}>Connection Status</h3>
                  <p
                    style={{
                      margin: '4px 0 0 0',
                      color: getStatusColor(health.robinhood.connected),
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {health.robinhood.connected ? 'CONNECTED' : 'DISCONNECTED'}
                  </p>
                </div>
                <span
                  style={{
                    display: 'inline-block',
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: getStatusColor(health.robinhood.connected),
                  }}
                />
              </div>
            </div>

            <div
              style={{
                padding: 16,
                border: '1px solid rgba(125, 211, 252, 0.15)',
                borderRadius: 8,
                background: 'rgba(15, 23, 42, 0.4)',
              }}
            >
              <h3 style={{ margin: '0 0 8px 0', color: '#a8bed0', fontSize: 12 }}>Account Status</h3>
              <p style={{ margin: 0, color: '#7dd3fc', fontSize: 13 }}>{health.robinhood.accountStatus}</p>
            </div>

            <div
              style={{
                padding: 16,
                border: '1px solid rgba(125, 211, 252, 0.15)',
                borderRadius: 8,
                background: 'rgba(15, 23, 42, 0.4)',
              }}
            >
              <h3 style={{ margin: '0 0 8px 0', color: '#a8bed0', fontSize: 12 }}>Last Sync</h3>
              <p style={{ margin: 0, color: '#7dd3fc', fontSize: 13 }}>
                {new Date(health.robinhood.lastSync).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Log */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18, color: '#e5f7ff' }}>Error Log (Last 50)</h2>

        {health?.errors && health.errors.length === 0 ? (
          <p style={{ color: '#a8bed0', fontSize: 13, margin: 0 }}>No errors recorded</p>
        ) : (
          <div style={{ display: 'grid', gap: 8, maxHeight: '600px', overflowY: 'auto' }}>
            {health?.errors.map((err, idx) => (
              <div
                key={idx}
                style={{
                  padding: 12,
                  border: `1px solid ${getSeverityColor(err.severity)}40`,
                  borderRadius: 6,
                  background: `${getSeverityColor(err.severity)}10`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 4 }}>
                  <div>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 6px',
                        background: getSeverityColor(err.severity) + '30',
                        color: getSeverityColor(err.severity),
                        borderRadius: 3,
                        fontSize: 10,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        marginRight: 8,
                      }}
                    >
                      {err.severity}
                    </span>
                    <span style={{ color: '#7dd3fc', fontSize: 11, fontWeight: 500 }}>
                      {err.service}
                    </span>
                  </div>
                  <span style={{ color: '#a8bed0', fontSize: 10 }}>
                    {new Date(err.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p style={{ margin: '4px 0 0 0', color: '#a8bed0', fontSize: 11, lineHeight: 1.4 }}>
                  {err.message}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Refresh Info */}
      <div
        style={{
          padding: 16,
          border: '1px solid rgba(125, 211, 252, 0.15)',
          borderRadius: 12,
          background: 'rgba(15, 23, 42, 0.4)',
        }}
      >
        <button
          onClick={fetchHealth}
          disabled={loading}
          style={{
            width: '100%',
            padding: '10px',
            background: 'rgba(125, 211, 252, 0.1)',
            color: '#7dd3fc',
            border: '1px solid rgba(125, 211, 252, 0.25)',
            borderRadius: 6,
            cursor: 'pointer',
            fontSize: 13,
            fontWeight: 500,
            opacity: loading ? 0.5 : 1,
          }}
        >
          {loading ? 'Refreshing...' : 'Refresh Health Status'}
        </button>
        <p style={{ margin: '8px 0 0 0', color: '#a8bed0', fontSize: 11 }}>
          Auto-refresh every 30 seconds
        </p>
      </div>
    </div>
  );
};

export default SystemHealthTab;
