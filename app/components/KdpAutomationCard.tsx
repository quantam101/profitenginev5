'use client';

/**
 * KDP Automation Dashboard Card
 * Displays publication stats, upcoming books, and recent activity
 * Integrates with /api/automation/kdp endpoint
 */

import { useEffect, useState } from 'react';

interface PublicationStats {
  totalPublished: number;
  totalEarnings: string;
  activeListings: number;
  monthlyRoyalties: string;
}

interface BookStatus {
  title: string;
  platforms: string[];
  status: 'pending' | 'publishing' | 'published' | 'failed';
  asin?: string;
  publishedDate?: string;
}

interface KdpCardData {
  stats: PublicationStats;
  recentBooks: BookStatus[];
  nextScheduled?: {
    count: number;
    estimatedTime: string;
  };
  lastRun?: {
    timestamp: string;
    duration: number;
    booksProcessed: number;
  };
}

interface CardProps {
  refreshInterval?: number; // milliseconds
  isMinified?: boolean;
}

interface AutomationError {
  message: string;
}

function StatCard({ value, label, trend }: { value: string | number; label: string; trend?: string }) {
  return (
    <div style={styles.statCard}>
      <div style={styles.statValue}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
      {trend && <div style={styles.statTrend}>{trend}</div>}
    </div>
  );
}

function BookStatusBadge({ status }: { status: BookStatus['status'] }) {
  const statusStyles = {
    pending: { backgroundColor: '#f0f0f0', color: '#666' },
    publishing: { backgroundColor: '#fff3cd', color: '#856404' },
    published: { backgroundColor: '#d4edda', color: '#155724' },
    failed: { backgroundColor: '#f8d7da', color: '#721c24' },
  };

  return (
    <span style={{ ...styles.badge, ...statusStyles[status] }}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export default function KdpAutomationCard({ refreshInterval = 5 * 60 * 1000, isMinified = false }: CardProps) {
  const [data, setData] = useState<KdpCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(!isMinified);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/automation/kdp?action=status', {
          headers: {
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTOMATION_TOKEN || ''}`,
          },
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const result = (await response.json()) as KdpCardData;
        setData(result);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch KDP data';
        setError(errorMessage);
        console.error('Error fetching KDP automation data:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchData();

    // Set up refresh interval
    const interval = setInterval(fetchData, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading && !data) {
    return (
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h3 style={styles.cardTitle}>KDP Automation</h3>
        </div>
        <div style={styles.skeleton} />
        <div style={styles.skeleton} />
        <div style={styles.skeleton} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h3 style={styles.cardTitle}>KDP Automation</h3>
        </div>
        <div style={styles.errorMessage}>
          <div style={styles.errorIcon}>!</div>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div style={styles.card}>
      {/* Header */}
      <div style={styles.cardHeader}>
        <div>
          <h3 style={styles.cardTitle}>
            <span style={styles.icon}>📚</span> KDP Automation
          </h3>
          {data.lastRun && (
            <div style={styles.lastRun}>
              Last run: {new Date(data.lastRun.timestamp).toLocaleDateString()} ({data.lastRun.duration}ms)
            </div>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={styles.expandButton}
          aria-label="Toggle expansion"
        >
          {expanded ? '−' : '+'}
        </button>
      </div>

      {/* Stats Grid */}
      <div style={styles.statsGrid}>
        <StatCard
          value={data.stats.totalPublished}
          label="Books Published"
          trend="↑ Growing catalog"
        />
        <StatCard
          value={data.stats.activeListings}
          label="Active Listings"
          trend="On 3 platforms"
        />
        <StatCard
          value={data.stats.totalEarnings}
          label="Total Earnings"
          trend="Lifetime royalties"
        />
        <StatCard
          value={data.stats.monthlyRoyalties}
          label="Monthly Royalties"
          trend="Current period"
        />
      </div>

      {/* Expanded Content */}
      {expanded && (
        <>
          {/* Recent Books */}
          {data.recentBooks.length > 0 && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Recent Books</h4>
              <div style={styles.booksList}>
                {data.recentBooks.slice(0, isMinified ? 3 : 5).map((book, idx) => (
                  <div key={idx} style={styles.bookItem}>
                    <div style={styles.bookInfo}>
                      <div style={styles.bookTitle}>{book.title}</div>
                      <div style={styles.bookMeta}>
                        {book.platforms.join(', ')} • {book.publishedDate && new Date(book.publishedDate).toLocaleDateString()}
                      </div>
                    </div>
                    <BookStatusBadge status={book.status} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scheduled Books */}
          {data.nextScheduled && data.nextScheduled.count > 0 && (
            <div style={styles.section}>
              <h4 style={styles.sectionTitle}>Upcoming</h4>
              <div style={styles.upcoming}>
                <div style={styles.upcomingItem}>
                  <span style={styles.upcomingLabel}>{data.nextScheduled.count} books scheduled</span>
                  <span style={styles.upcomingTime}>{data.nextScheduled.estimatedTime}</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div style={styles.actions}>
            <button style={{ ...styles.button, ...styles.primaryButton }}>
              Publish New Book
            </button>
            <button style={{ ...styles.button, ...styles.secondaryButton }}>
              View Analytics
            </button>
          </div>
        </>
      )}

      {/* Footer */}
      <div style={styles.footer}>
        <div style={styles.footerText}>
          Auto-syncs with Amazon, Draft2Digital, Smashwords
        </div>
        <div style={styles.footerTime}>
          Updated {data.lastRun ? 'just now' : 'recently'}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles: Record<string, React.CSSProperties> = {
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },

  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: '1px solid #f0f0f0',
  },

  cardTitle: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: 600,
    color: '#1a1a1a',
  },

  icon: {
    marginRight: '8px',
  },

  lastRun: {
    fontSize: '12px',
    color: '#666',
    marginTop: '4px',
  },

  expandButton: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    cursor: 'pointer',
    color: '#666',
    padding: '0',
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },

  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '12px',
    marginBottom: '20px',
  },

  statCard: {
    padding: '12px',
    backgroundColor: '#f9f9f9',
    borderRadius: '6px',
    border: '1px solid #f0f0f0',
  },

  statValue: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#1a1a1a',
    marginBottom: '4px',
  },

  statLabel: {
    fontSize: '12px',
    color: '#666',
    marginBottom: '4px',
  },

  statTrend: {
    fontSize: '11px',
    color: '#27ae60',
  },

  section: {
    marginBottom: '16px',
  },

  sectionTitle: {
    margin: '0 0 12px 0',
    fontSize: '13px',
    fontWeight: 600,
    color: '#333',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },

  booksList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },

  bookItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 12px',
    backgroundColor: '#fafafa',
    borderRadius: '4px',
    fontSize: '13px',
  },

  bookInfo: {
    flex: 1,
  },

  bookTitle: {
    fontWeight: 500,
    color: '#1a1a1a',
    marginBottom: '4px',
  },

  bookMeta: {
    fontSize: '11px',
    color: '#999',
  },

  badge: {
    padding: '4px 8px',
    borderRadius: '3px',
    fontSize: '11px',
    fontWeight: 500,
  },

  upcoming: {
    padding: '12px',
    backgroundColor: '#f0f8ff',
    borderRadius: '4px',
    border: '1px solid #dce8f6',
  },

  upcomingItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
  },

  upcomingLabel: {
    fontWeight: 500,
    color: '#0066cc',
  },

  upcomingTime: {
    color: '#666',
  },

  actions: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px',
    marginTop: '16px',
    marginBottom: '16px',
  },

  button: {
    padding: '8px 12px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    fontSize: '12px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  primaryButton: {
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
  },

  secondaryButton: {
    backgroundColor: '#fff',
    color: '#0066cc',
    border: '1px solid #0066cc',
  },

  footer: {
    paddingTop: '12px',
    borderTop: '1px solid #f0f0f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '11px',
    color: '#999',
  },

  footerText: {
    flex: 1,
  },

  footerTime: {
    textAlign: 'right',
  },

  skeleton: {
    height: '60px',
    backgroundColor: '#f0f0f0',
    borderRadius: '4px',
    marginBottom: '12px',
    animation: 'pulse 1.5s infinite',
  },

  errorMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#fef1f1',
    borderRadius: '4px',
    color: '#d32f2f',
    fontSize: '13px',
  },

  errorIcon: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: '#d32f2f',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    flexShrink: 0,
  },
};
