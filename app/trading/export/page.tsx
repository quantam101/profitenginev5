'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

interface ExportFormat {
  id: string;
  name: string;
  description: string;
  mimeType: string;
}

interface ExportMetadata {
  formats: ExportFormat[];
  dataTypes: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  defaultDateRange: {
    days: number;
    description: string;
  };
}

export default function ExportPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [metadata, setMetadata] = useState<ExportMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  // Form state
  const [format, setFormat] = useState<string>('csv');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [dataType, setDataType] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/sign-in');
    }
  }, [status, router]);

  // Load export metadata
  useEffect(() => {
    async function loadMetadata() {
      try {
        setLoading(true);
        const res = await fetch('/api/trading/export');
        if (!res.ok) throw new Error('Failed to load export options');

        const data = await res.json();
        setMetadata(data);

        // Set default date range
        const today = new Date();
        const defaultStart = new Date(today);
        defaultStart.setDate(today.getDate() - data.defaultDateRange.days);

        setEndDate(today.toISOString().split('T')[0]);
        setStartDate(defaultStart.toISOString().split('T')[0]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load options');
      } finally {
        setLoading(false);
      }
    }

    if (status === 'authenticated') {
      loadMetadata();
    }
  }, [status]);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }

    try {
      setExporting(true);

      const response = await fetch('/api/trading/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format,
          startDate,
          endDate,
          dataType,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Export failed');
      }

      // Get the filename from content-disposition or generate one
      const contentDisposition =
        response.headers.get('content-disposition') || '';
      const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
      const filename = filenameMatch
        ? filenameMatch[1]
        : `trading-export-${Date.now()}`;

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSuccessMessage(
        `Export completed! ${filename} has been downloaded.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <main style={styles.container}>
        <div style={styles.loadingBox}>
          <p style={{ color: '#a8bed0', fontSize: 16 }}>
            Loading export options...
          </p>
        </div>
      </main>
    );
  }

  if (status === 'unauthenticated') {
    return null;
  }

  return (
    <main style={styles.container}>
      <section style={styles.section}>
        {/* Header */}
        <div style={styles.header}>
          <p style={styles.breadcrumb}>Trading Tools</p>
          <h1 style={styles.title}>Export Trading Data</h1>
          <p style={styles.subtitle}>
            Download your trading history, performance reports, and tax data
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div style={styles.alertError}>
            <p style={styles.alertTitle}>Error</p>
            <p style={styles.alertText}>{error}</p>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div style={styles.alertSuccess}>
            <p style={styles.alertTitle}>Success</p>
            <p style={styles.alertText}>{successMessage}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleExport} style={styles.form}>
          {/* Export Format Selection */}
          <fieldset style={styles.fieldset}>
            <legend style={styles.legend}>Export Format</legend>
            <p style={styles.description}>
              Choose the format that best fits your needs
            </p>

            <div style={styles.optionGrid}>
              {metadata?.formats.map((fmt) => (
                <label
                  key={fmt.id}
                  style={{
                    ...styles.radioLabel,
                    ...(format === fmt.id ? styles.radioLabelActive : {}),
                  }}
                >
                  <input
                    type="radio"
                    name="format"
                    value={fmt.id}
                    checked={format === fmt.id}
                    onChange={(e) => setFormat(e.target.value)}
                    style={styles.radioInput}
                  />
                  <div style={styles.radioContent}>
                    <strong style={{ color: '#e5f7ff' }}>{fmt.name}</strong>
                    <p style={{ margin: '5px 0 0 0', color: '#a8bed0', fontSize: '0.85em' }}>
                      {fmt.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Date Range Selection */}
          <fieldset style={styles.fieldset}>
            <legend style={styles.legend}>Date Range</legend>
            <p style={styles.description}>
              Select the period of trading data to include
            </p>

            <div style={styles.dateGrid}>
              <div style={styles.dateField}>
                <label style={styles.label}>Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={styles.input}
                  required
                />
              </div>
              <div style={styles.dateField}>
                <label style={styles.label}>End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={styles.input}
                  required
                />
              </div>
            </div>

            {/* Quick Range Buttons */}
            <div style={styles.quickRangeButtons}>
              {[
                { label: 'Last 30 Days', days: 30 },
                { label: 'Last 90 Days', days: 90 },
                { label: 'Last 6 Months', days: 180 },
                { label: 'Last Year', days: 365 },
              ].map(({ label, days }) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => {
                    const today = new Date();
                    const start = new Date(today);
                    start.setDate(today.getDate() - days);
                    setStartDate(start.toISOString().split('T')[0]);
                    setEndDate(today.toISOString().split('T')[0]);
                  }}
                  style={styles.quickRangeButton}
                >
                  {label}
                </button>
              ))}
            </div>
          </fieldset>

          {/* Data Type Selection */}
          <fieldset style={styles.fieldset}>
            <legend style={styles.legend}>Data Type</legend>
            <p style={styles.description}>
              Choose what data to include in your export
            </p>

            <div style={styles.optionGrid}>
              {metadata?.dataTypes.map((dtype) => (
                <label
                  key={dtype.id}
                  style={{
                    ...styles.radioLabel,
                    ...(dataType === dtype.id ? styles.radioLabelActive : {}),
                  }}
                >
                  <input
                    type="radio"
                    name="dataType"
                    value={dtype.id}
                    checked={dataType === dtype.id}
                    onChange={(e) => setDataType(e.target.value)}
                    style={styles.radioInput}
                  />
                  <div style={styles.radioContent}>
                    <strong style={{ color: '#e5f7ff' }}>{dtype.name}</strong>
                    <p style={{ margin: '5px 0 0 0', color: '#a8bed0', fontSize: '0.85em' }}>
                      {dtype.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={exporting}
            style={{
              ...styles.submitButton,
              ...(exporting ? styles.submitButtonDisabled : {}),
            }}
          >
            {exporting ? 'Generating Export...' : 'Download Export'}
          </button>
        </form>

        {/* Information Cards */}
        <div style={styles.infoGrid}>
          <div style={styles.infoCard}>
            <div style={styles.infoIcon}>📊</div>
            <h3 style={styles.infoTitle}>CSV Format</h3>
            <p style={styles.infoText}>
              Compatible with Excel, Google Sheets, and accounting software.
              Perfect for custom analysis.
            </p>
          </div>

          <div style={styles.infoCard}>
            <div style={styles.infoIcon}>📈</div>
            <h3 style={styles.infoTitle}>PDF Reports</h3>
            <p style={styles.infoText}>
              Professional reports with performance summaries, charts, and
              trade-by-trade details.
            </p>
          </div>

          <div style={styles.infoCard}>
            <div style={styles.infoIcon}>💰</div>
            <h3 style={styles.infoTitle}>Tax Data</h3>
            <p style={styles.infoText}>
              Categorized capital gains/losses and wash sale tracking for easy
              tax reporting.
            </p>
          </div>

          <div style={styles.infoCard}>
            <div style={styles.infoIcon}>🔒</div>
            <h3 style={styles.infoTitle}>Your Data Only</h3>
            <p style={styles.infoText}>
              All exports are encrypted and contain only your trading data.
              Nothing is shared.
            </p>
          </div>
        </div>

        {/* FAQ Section */}
        <div style={styles.faqSection}>
          <h2 style={styles.faqTitle}>Frequently Asked Questions</h2>

          <div style={styles.faqItem}>
            <h4 style={styles.faqQuestion}>
              How long does it take to generate an export?
            </h4>
            <p style={styles.faqAnswer}>
              Most exports complete within seconds. Large exports with thousands
              of trades may take up to 5 seconds.
            </p>
          </div>

          <div style={styles.faqItem}>
            <h4 style={styles.faqQuestion}>
              Can I use the CSV export in TurboTax or tax software?
            </h4>
            <p style={styles.faqAnswer}>
              Yes! Use the &quot;Tax Report CSV&quot; format which includes cost basis,
              proceeds, and holding period. Consult your tax software for import
              instructions.
            </p>
          </div>

          <div style={styles.faqItem}>
            <h4 style={styles.faqQuestion}>
              What are wash sales and why do they matter?
            </h4>
            <p style={styles.faqAnswer}>
              Wash sales occur when you sell an investment at a loss and buy a
              substantially identical one within 30 days. The IRS disallows the
              loss deduction. Our reports automatically detect these.
            </p>
          </div>

          <div style={styles.faqItem}>
            <h4 style={styles.faqQuestion}>
              Is my data secure?
            </h4>
            <p style={styles.faqAnswer}>
              All exports are generated server-side and delivered over secure
              HTTPS. Only your account can access your exports. Files are not
              stored after download.
            </p>
          </div>

          <div style={styles.faqItem}>
            <h4 style={styles.faqQuestion}>
              Can I export data older than 1 year?
            </h4>
            <p style={styles.faqAnswer}>
              Yes! You can select any date range available in your trading
              history. Use the date picker to go back to your first trade.
            </p>
          </div>
        </div>

        {/* Footer Notice */}
        <div style={styles.footerNotice}>
          <p style={styles.noticeTitle}>Tax Disclaimer</p>
          <p style={styles.noticeText}>
            This export is provided for informational purposes to assist with
            record-keeping and tax preparation. Please consult with a qualified
            tax professional to ensure your trades are reported correctly and
            in compliance with all applicable tax regulations. ProfitEngine is
            not a tax advisor.
          </p>
        </div>
      </section>
    </main>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    background: '#080b12',
    color: '#e5f7ff',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
    padding: '32px 16px',
  },

  section: {
    maxWidth: 1040,
    margin: '0 auto',
  },

  header: {
    marginBottom: 40,
  },

  breadcrumb: {
    color: '#7dd3fc',
    textTransform: 'uppercase',
    letterSpacing: 2,
    fontSize: 12,
    margin: 0,
  },

  title: {
    fontSize: 'clamp(32px, 5vw, 48px)',
    fontWeight: 700,
    margin: '12px 0 16px 0',
    lineHeight: 1.2,
  },

  subtitle: {
    color: '#a8bed0',
    fontSize: 16,
    margin: 0,
  },

  alertError: {
    border: '1px solid rgba(248, 113, 113, 0.5)',
    borderRadius: 12,
    padding: 20,
    background: 'rgba(127, 29, 29, 0.15)',
    marginBottom: 24,
  },

  alertSuccess: {
    border: '1px solid rgba(5, 150, 105, 0.5)',
    borderRadius: 12,
    padding: 20,
    background: 'rgba(5, 150, 105, 0.15)',
    marginBottom: 24,
  },

  alertTitle: {
    color: '#7dd3fc',
    fontWeight: 600,
    margin: '0 0 8px 0',
  },

  alertText: {
    color: '#a8bed0',
    margin: 0,
    fontSize: 14,
  },

  form: {
    background: 'rgba(15, 23, 42, 0.5)',
    border: '1px solid rgba(125, 211, 252, 0.1)',
    borderRadius: 16,
    padding: 32,
    marginBottom: 32,
  },

  fieldset: {
    border: 'none',
    padding: 0,
    margin: '0 0 32px 0',
  },

  legend: {
    fontSize: 18,
    fontWeight: 600,
    color: '#e5f7ff',
    margin: '0 0 12px 0',
    padding: 0,
  },

  description: {
    color: '#a8bed0',
    fontSize: 14,
    margin: '0 0 16px 0',
  },

  optionGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: 16,
  },

  radioLabel: {
    display: 'flex',
    alignItems: 'flex-start',
    padding: 16,
    border: '1px solid rgba(125, 211, 252, 0.25)',
    borderRadius: 12,
    background: 'rgba(15, 23, 42, 0.3)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },

  radioLabelActive: {
    borderColor: '#7dd3fc',
    background: 'rgba(125, 211, 252, 0.15)',
  },

  radioInput: {
    marginRight: 12,
    marginTop: 2,
    cursor: 'pointer',
    width: 20,
    height: 20,
    flexShrink: 0,
  },

  radioContent: {
    flex: 1,
  },

  dateGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
    marginBottom: 16,
  },

  dateField: {
    display: 'flex',
    flexDirection: 'column',
  } as React.CSSProperties,

  label: {
    color: '#7dd3fc',
    fontSize: 14,
    fontWeight: 500,
    marginBottom: 8,
  },

  input: {
    padding: '10px 12px',
    border: '1px solid rgba(125, 211, 252, 0.25)',
    borderRadius: 8,
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#e5f7ff',
    fontSize: 14,
  },

  quickRangeButtons: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
  } as React.CSSProperties,

  quickRangeButton: {
    padding: '8px 16px',
    border: '1px solid rgba(125, 211, 252, 0.25)',
    borderRadius: 8,
    background: 'rgba(125, 211, 252, 0.1)',
    color: '#7dd3fc',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.2s ease',
  },

  submitButton: {
    width: '100%',
    padding: '16px 24px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: 12,
    color: 'white',
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    marginTop: 24,
  },

  submitButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },

  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 16,
    marginBottom: 40,
  },

  infoCard: {
    padding: 24,
    border: '1px solid rgba(125, 211, 252, 0.1)',
    borderRadius: 12,
    background: 'rgba(15, 23, 42, 0.3)',
  },

  infoIcon: {
    fontSize: 32,
    marginBottom: 12,
  },

  infoTitle: {
    color: '#e5f7ff',
    fontSize: 16,
    fontWeight: 600,
    margin: '0 0 8px 0',
  },

  infoText: {
    color: '#a8bed0',
    fontSize: 13,
    margin: 0,
    lineHeight: 1.6,
  },

  faqSection: {
    background: 'rgba(15, 23, 42, 0.5)',
    border: '1px solid rgba(125, 211, 252, 0.1)',
    borderRadius: 16,
    padding: 32,
    marginBottom: 24,
  },

  faqTitle: {
    fontSize: 24,
    fontWeight: 700,
    color: '#e5f7ff',
    margin: '0 0 24px 0',
  },

  faqItem: {
    marginBottom: 24,
    paddingBottom: 24,
    borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
  },

  faqQuestion: {
    color: '#7dd3fc',
    fontSize: 15,
    fontWeight: 600,
    margin: '0 0 8px 0',
  },

  faqAnswer: {
    color: '#a8bed0',
    fontSize: 14,
    margin: 0,
    lineHeight: 1.6,
  },

  footerNotice: {
    background: 'rgba(245, 158, 11, 0.15)',
    border: '1px solid rgba(245, 158, 11, 0.3)',
    borderRadius: 12,
    padding: 24,
    marginTop: 32,
  },

  noticeTitle: {
    color: '#f59e0b',
    fontWeight: 600,
    margin: '0 0 8px 0',
  },

  noticeText: {
    color: '#a8bed0',
    fontSize: 13,
    margin: 0,
    lineHeight: 1.6,
  },

  loadingBox: {
    padding: 40,
    textAlign: 'center',
  },
};
