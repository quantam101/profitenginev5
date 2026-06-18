'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface KYCStatus {
  status: 'pending' | 'approved' | 'rejected' | 'error';
  message: string;
  submittedAt?: string;
  completedAt?: string;
  nextSteps?: string[];
}

export default function KYCStatusPage() {
  const router = useRouter();
  const [kycStatus, setKycStatus] = useState<KYCStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (!token) {
          router.push('/trading-signup');
          return;
        }

        const response = await fetch('/api/kyc/status', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }

        const data = await response.json();
        setKycStatus(data);
      } catch (error) {
        console.error('Failed to check KYC status:', error);
        setKycStatus({
          status: 'error',
          message: 'Unable to check verification status. Please try again later.',
        });
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
  }, [router]);

  if (loading) {
    return (
      <main
        style={{
          minHeight: '100vh',
          background:
            'radial-gradient(circle at 15% 0%, rgba(90,162,255,.18), transparent 32rem), #050914',
          color: '#eef5ff',
          fontFamily: 'Arial, Helvetica, sans-serif',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>⏳</div>
          <p>Checking verification status...</p>
        </div>
      </main>
    );
  }

  return (
    <main
      style={{
        minHeight: '100vh',
        background:
          'radial-gradient(circle at 15% 0%, rgba(90,162,255,.18), transparent 32rem), #050914',
        color: '#eef5ff',
        fontFamily: 'Arial, Helvetica, sans-serif',
        padding: '20px',
      }}
    >
      {kycStatus && <StatusCard status={kycStatus} />}
    </main>
  );
}

function StatusCard({ status }: { status: KYCStatus }) {
  const getIcon = () => {
    switch (status.status) {
      case 'pending':
        return '⏳';
      case 'approved':
        return '✓';
      case 'rejected':
        return '✕';
      default:
        return '!';
    }
  };

  const getColor = () => {
    switch (status.status) {
      case 'pending':
        return '#5aa2ff';
      case 'approved':
        return '#34d399';
      case 'rejected':
        return '#fb7185';
      default:
        return '#fbbf24';
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'pending':
        return 'Under Review';
      case 'approved':
        return 'Verified & Approved';
      case 'rejected':
        return 'Verification Failed';
      default:
        return 'Error';
    }
  };

  return (
    <div
      style={{
        maxWidth: '600px',
        margin: '100px auto',
        border: `1px solid ${getColor()}`,
        background: `rgba(${hexToRgb(getColor()).join(',')}, 0.05)`,
        borderRadius: '12px',
        padding: '48px 40px',
        boxShadow: '0 20px 40px rgba(0,0,0,.4)',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '64px', marginBottom: '24px', color: getColor() }}>
        {getIcon()}
      </div>

      <h1
        style={{
          fontSize: '28px',
          fontWeight: 700,
          margin: '0 0 8px',
          color: getColor(),
        }}
      >
        {getStatusText()}
      </h1>

      <p style={{ color: '#9fb0c6', fontSize: '16px', lineHeight: '1.6', margin: '16px 0 24px' }}>
        {status.message}
      </p>

      {status.submittedAt && (
        <p style={{ color: '#9fb0c6', fontSize: '13px', margin: '12px 0' }}>
          <strong>Submitted:</strong> {new Date(status.submittedAt).toLocaleDateString()}
        </p>
      )}

      {status.completedAt && (
        <p style={{ color: '#9fb0c6', fontSize: '13px', margin: '12px 0' }}>
          <strong>Completed:</strong> {new Date(status.completedAt).toLocaleDateString()}
        </p>
      )}

      {status.nextSteps && status.nextSteps.length > 0 && (
        <div
          style={{
            margin: '32px 0',
            padding: '20px',
            background: 'rgba(14,23,38,.4)',
            borderRadius: '8px',
            textAlign: 'left',
          }}
        >
          <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 600 }}>
            Next Steps
          </h3>
          <ol style={{ margin: 0, paddingLeft: '20px', color: '#9fb0c6', fontSize: '14px' }}>
            {status.nextSteps.map((step, index) => (
              <li key={index} style={{ marginBottom: '8px' }}>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}

      {status.status === 'approved' && (
        <button
          onClick={() => {
            window.location.href = '/command-center';
          }}
          style={{
            padding: '14px 40px',
            background: '#34d399',
            color: '#050914',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            marginTop: '24px',
            transition: 'all 0.2s',
          }}
          onMouseOver={e => {
            (e.target as HTMLButtonElement).style.transform = 'translateY(-2px)';
            (e.target as HTMLButtonElement).style.boxShadow = '0 8px 16px rgba(52, 211, 153, 0.3)';
          }}
          onMouseOut={e => {
            (e.target as HTMLButtonElement).style.transform = 'translateY(0)';
            (e.target as HTMLButtonElement).style.boxShadow = 'none';
          }}
        >
          Go to Dashboard
        </button>
      )}

      {status.status === 'rejected' && (
        <button
          onClick={() => {
            window.location.href = '/trading-signup/kyc';
          }}
          style={{
            padding: '14px 40px',
            background: '#5aa2ff',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            marginTop: '24px',
            transition: 'all 0.2s',
          }}
          onMouseOver={e => {
            (e.target as HTMLButtonElement).style.background = '#4a8edb';
          }}
          onMouseOut={e => {
            (e.target as HTMLButtonElement).style.background = '#5aa2ff';
          }}
        >
          Try Again
        </button>
      )}

      {status.status === 'pending' && (
        <p style={{ color: '#9fb0c6', fontSize: '13px', marginTop: '24px' }}>
          We typically review submissions within 24 hours. Check back soon!
        </p>
      )}

      {status.status === 'error' && (
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '14px 40px',
            background: '#5aa2ff',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            marginTop: '24px',
            transition: 'all 0.2s',
          }}
          onMouseOver={e => {
            (e.target as HTMLButtonElement).style.background = '#4a8edb';
          }}
          onMouseOut={e => {
            (e.target as HTMLButtonElement).style.background = '#5aa2ff';
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}

function hexToRgb(hex: string): number[] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)]
    : [90, 162, 255];
}
