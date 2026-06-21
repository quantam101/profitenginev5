/**
 * TikTok Dashboard Card Component
 *
 * Renders TikTok Long-form automation metrics in the ProfitEngine dashboard:
 * - Videos published count
 * - Total views and engagement metrics
 * - Engagement rate and average watch time
 * - Real-time status indicator
 * - Recent upload history
 */

'use client';

interface TikTokMetrics {
  videosPublished: number;
  totalViews: number;
  totalLikes: number;
  totalShares: number;
  totalComments: number;
  totalSaves: number;
  averageEngagementRate: number;
  averageWatchTime: number;
  status: 'active' | 'idle' | 'disabled';
  lastPublishedAt?: string;
  lastPublishedTitle?: string;
}

interface TikTokCardProps {
  metrics: TikTokMetrics;
  onPublish?: () => void;
  onViewAnalytics?: () => void;
}

export function TikTokDashboardCard({ metrics, onPublish, onViewAnalytics }: TikTokCardProps) {
  const statusColor =
    metrics.status === 'active' ? '#00ff88' : metrics.status === 'idle' ? '#ffcc00' : '#ff4444';
  const statusLabel =
    metrics.status === 'active' ? 'PUBLISHING' : metrics.status === 'idle' ? 'IDLE' : 'DISABLED';

  return (
    <div
      style={{
        background: '#111',
        border: '1px solid #1e1e1e',
        borderRadius: 8,
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Header with status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🎵</span>
          <div>
            <h3 style={{ color: '#f0f0f0', margin: 0, fontSize: '14px', fontWeight: 700 }}>
              TikTok Long-Form
            </h3>
            <p style={{ color: '#444', margin: '2px 0 0', fontSize: '10px' }}>Video Automation</p>
          </div>
        </div>
        <span
          style={{
            padding: '4px 9px',
            borderRadius: '12px',
            fontSize: '9px',
            fontWeight: 700,
            background: `${statusColor}15`,
            color: statusColor,
            border: `1px solid ${statusColor}40`,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          {statusLabel}
        </span>
      </div>

      {/* Key metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <MetricBox label="Published" value={metrics.videosPublished} color="#00ff88" />
        <MetricBox label="Total Views" value={formatNumber(metrics.totalViews)} color="#00aaff" />
        <MetricBox label="Engagement" value={`${metrics.averageEngagementRate.toFixed(1)}%`} color="#aa00ff" />
        <MetricBox label="Avg Watch" value={`${metrics.averageWatchTime.toFixed(0)}s`} color="#ff6600" />
      </div>

      {/* Engagement breakdown */}
      <div
        style={{
          background: '#0a0a0a',
          borderRadius: '6px',
          padding: '10px',
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '8px',
          fontSize: '11px',
        }}
      >
        <EngagementStat icon="❤️" label="Likes" value={metrics.totalLikes} />
        <EngagementStat icon="📤" label="Shares" value={metrics.totalShares} />
        <EngagementStat icon="💬" label="Comments" value={metrics.totalComments} />
        <EngagementStat icon="⭐" label="Saves" value={metrics.totalSaves} />
      </div>

      {/* Last published */}
      {metrics.lastPublishedAt && (
        <div
          style={{
            background: '#0a0a0a',
            borderRadius: '6px',
            padding: '10px',
            borderLeft: `2px solid #00aaff`,
          }}
        >
          <p style={{ color: '#444', margin: 0, fontSize: '9px', textTransform: 'uppercase' }}>
            Last Published
          </p>
          <p style={{ color: '#ccc', margin: '4px 0 0', fontSize: '11px', fontWeight: 600 }}>
            {metrics.lastPublishedTitle || 'Untitled Video'}
          </p>
          <p style={{ color: '#666', margin: '2px 0 0', fontSize: '9px', fontFamily: 'monospace' }}>
            {new Date(metrics.lastPublishedAt).toLocaleDateString()}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={onPublish}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: '6px',
            background: '#00ff8815',
            border: '1px solid #00ff8830',
            color: '#00ff88',
            cursor: 'pointer',
            fontSize: '11px',
            fontWeight: 600,
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#00ff8825';
            e.currentTarget.style.borderColor = '#00ff8850';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#00ff8815';
            e.currentTarget.style.borderColor = '#00ff8830';
          }}
        >
          Publish
        </button>
        <button
          onClick={onViewAnalytics}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: '6px',
            background: '#00aaff15',
            border: '1px solid #00aaff30',
            color: '#00aaff',
            cursor: 'pointer',
            fontSize: '11px',
            fontWeight: 600,
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#00aaff25';
            e.currentTarget.style.borderColor = '#00aaff50';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#00aaff15';
            e.currentTarget.style.borderColor = '#00aaff30';
          }}
        >
          Analytics
        </button>
      </div>
    </div>
  );
}

interface MetricBoxProps {
  label: string;
  value: string | number;
  color: string;
}

function MetricBox({ label, value, color }: MetricBoxProps) {
  return (
    <div
      style={{
        background: '#0a0a0a',
        borderRadius: '6px',
        padding: '8px 10px',
        borderLeft: `2px solid ${color}`,
      }}
    >
      <p style={{ color: '#444', margin: 0, fontSize: '9px', textTransform: 'uppercase' }}>
        {label}
      </p>
      <p style={{ color, margin: '2px 0 0', fontSize: '14px', fontWeight: 700, fontFamily: 'monospace' }}>
        {value}
      </p>
    </div>
  );
}

interface EngagementStatProps {
  icon: string;
  label: string;
  value: number;
}

function EngagementStat({ icon, label, value }: EngagementStatProps) {
  return (
    <div style={{ textAlign: 'center' }}>
      <p style={{ margin: 0, fontSize: '12px' }}>{icon}</p>
      <p style={{ color: '#666', margin: '2px 0 0', fontSize: '9px' }}>{label}</p>
      <p style={{ color: '#ccc', margin: '2px 0 0', fontSize: '12px', fontWeight: 700 }}>
        {formatNumber(value)}
      </p>
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return String(num);
}

/**
 * Usage Example - Add to dashboard data interface and rendering:
 *
 * // In Data interface:
 * interface Data {
 *   // ... existing fields
 *   tiktokMetrics?: TikTokMetrics;
 * }
 *
 * // In dashboard page.tsx - add to Section function:
 * if (active === 'tiktok') {
 *   return data.tiktokMetrics ? (
 *     <div>
 *       <h2>TikTok Automation</h2>
 *       <TikTokDashboardCard
 *         metrics={data.tiktokMetrics}
 *         onPublish={() => {
 *           // Open publish modal or navigate to publish page
 *         }}
 *         onViewAnalytics={() => {
 *           // Navigate to TikTok analytics page
 *         }}
 *       />
 *     </div>
 *   ) : null;
 * }
 *
 * // Add to NAV array:
 * {
 *   id: 'tiktok',
 *   label: 'TikTok',
 *   icon: '🎵',
 *   group: 'Social'
 * }
 */
