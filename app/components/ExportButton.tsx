'use client';

import { useState } from 'react';

interface ExportButtonProps {
  format: 'csv' | 'pdf' | 'tax-csv';
  label?: string;
  disabled?: boolean;
  startDate?: string;
  endDate?: string;
  onExport?: (success: boolean) => void;
}

export default function ExportButton({
  format,
  label,
  disabled = false,
  startDate,
  endDate,
  onExport,
}: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    if (!startDate || !endDate) {
      setError('Please select date range');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await fetch('/api/trading/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format,
          startDate,
          endDate,
          dataType: 'all',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Export failed');
      }

      // Create download
      const contentDisposition =
        response.headers.get('content-disposition') || '';
      const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
      const filename = filenameMatch
        ? filenameMatch[1]
        : `trading-export-${Date.now()}`;

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      onExport?.(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      onExport?.(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <button
        onClick={handleExport}
        disabled={disabled || loading}
        style={{
          padding: '10px 20px',
          background: disabled || loading ? '#4b5563' : '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: 8,
          cursor: disabled || loading ? 'not-allowed' : 'pointer',
          fontSize: 14,
          fontWeight: 600,
          opacity: disabled || loading ? 0.5 : 1,
        }}
      >
        {loading ? 'Exporting...' : label || `Export as ${format.toUpperCase()}`}
      </button>
      {error && <p style={{ color: '#f87171', fontSize: 12, margin: 0 }}>{error}</p>}
    </div>
  );
}
