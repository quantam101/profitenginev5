'use client';

import { useEffect, useState, useCallback } from 'react';
import AdminDashboard from './AdminDashboard';

export const dynamic = 'force-dynamic';

interface AdminSessionData {
  authenticated: boolean;
  email?: string;
  role?: string;
  ipAddress?: string;
  lastVerified?: number;
}

const AdminPage = () => {
  const [session, setSession] = useState<AdminSessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaCode, setMfaCode] = useState('');

  const verifySession = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });

      if (res.status === 401) {
        setSession(null);
        setError('Unauthorized access. Admin privileges required.');
        return;
      }

      if (res.status === 403) {
        setMfaRequired(true);
        setError('Multi-factor authentication required.');
        return;
      }

      if (!res.ok) {
        throw new Error(`Session verification failed: ${res.status}`);
      }

      const data = await res.json();
      setSession(data);
      setMfaRequired(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Session verification failed');
      setSession(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const submitMFA = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/verify-mfa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: mfaCode }),
        cache: 'no-store',
      });

      if (!res.ok) {
        throw new Error('MFA verification failed');
      }

      const data = await res.json();
      setSession(data);
      setMfaRequired(false);
      setMfaCode('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'MFA verification failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    verifySession();
  }, [verifySession]);

  if (loading && !session) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#080b12',
          color: '#e5f7ff',
          fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          padding: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#a8bed0', fontSize: 16, margin: 0 }}>Loading admin console...</p>
          <div style={{ marginTop: 16, fontSize: 12, color: '#7dd3fc' }}>Verifying credentials</div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#080b12',
          color: '#e5f7ff',
          fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          padding: '32px',
        }}
      >
        <section style={{ maxWidth: 600, margin: '0 auto', paddingTop: 60 }}>
          <div
            style={{
              border: '1px solid rgba(248, 113, 113, 0.5)',
              borderRadius: 18,
              padding: 32,
              background: 'rgba(127, 29, 29, 0.15)',
            }}
          >
            <h1 style={{ fontSize: 28, margin: '0 0 16px 0', color: '#f87171' }}>Access Denied</h1>
            <p style={{ color: '#a8bed0', margin: '0 0 12px 0', lineHeight: 1.6 }}>
              {error || 'Admin access requires valid credentials and IP authorization.'}
            </p>
            <p style={{ color: '#7dd3fc', fontSize: 12, margin: 0 }}>
              If you believe this is an error, contact dispatch@alreadyherellc.com
            </p>
          </div>

          {mfaRequired && (
            <div style={{ marginTop: 24 }}>
              <div
                style={{
                  border: '1px solid rgba(125, 211, 252, 0.25)',
                  borderRadius: 18,
                  padding: 24,
                  background: 'rgba(15, 23, 42, 0.72)',
                }}
              >
                <h2 style={{ margin: '0 0 16px 0', fontSize: 18 }}>Multi-Factor Authentication</h2>
                <p style={{ color: '#a8bed0', margin: '0 0 16px 0' }}>
                  Enter your 6-digit authentication code from your authenticator app.
                </p>
                <input
                  type="text"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: 18,
                    letterSpacing: '4px',
                    textAlign: 'center',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(125, 211, 252, 0.25)',
                    borderRadius: 8,
                    color: '#7dd3fc',
                    marginBottom: 16,
                  }}
                />
                <button
                  onClick={submitMFA}
                  disabled={mfaCode.length !== 6 || loading}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: mfaCode.length === 6 ? '#7dd3fc' : 'rgba(125, 211, 252, 0.3)',
                    color: mfaCode.length === 6 ? '#080b12' : '#a8bed0',
                    border: 'none',
                    borderRadius: 8,
                    fontWeight: 600,
                    cursor: mfaCode.length === 6 ? 'pointer' : 'not-allowed',
                    fontSize: 14,
                  }}
                >
                  {loading ? 'Verifying...' : 'Verify Code'}
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    );
  }

  return <AdminDashboard session={session} />;
};

export default AdminPage;
