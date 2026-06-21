/**
 * Head Videos/Courses Dashboard Card Component
 *
 * Renders Head Videos course automation metrics in the ProfitEngine dashboard:
 * - Total courses and lessons created
 * - Student enrollment and completion metrics
 * - Average course ratings and completion rates
 * - Real-time status indicator
 * - Recent published courses
 */

'use client';

export interface HeadVideosDashboardMetrics {
  totalCourses: number;
  totalLessons: number;
  totalEnrollments: number;
  totalCompletions: number;
  activeStudents: number;
  avgLessonCompletion: number;
  avgCourseRating: number;
  totalCourseRevenue: number;
  status: 'active' | 'idle' | 'disabled';
  lastPublishedAt?: string;
  lastPublishedTitle?: string;
}

interface HeadVideosDashboardCardProps {
  metrics: HeadVideosDashboardMetrics;
  onCreateCourse?: () => void;
  onViewAnalytics?: () => void;
}

export function HeadVideosDashboardCard({
  metrics,
  onCreateCourse,
  onViewAnalytics,
}: HeadVideosDashboardCardProps) {
  const statusColor =
    metrics.status === 'active' ? '#00ff88' : metrics.status === 'idle' ? '#ffcc00' : '#ff4444';
  const statusLabel =
    metrics.status === 'active' ? 'PUBLISHING' : metrics.status === 'idle' ? 'IDLE' : 'DISABLED';

  const completionPercentage = Math.min(
    100,
    Math.round(
      (metrics.totalCompletions / Math.max(1, metrics.totalEnrollments)) * 100
    )
  );

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
          <span style={{ fontSize: '18px' }}>🎓</span>
          <div>
            <h3 style={{ color: '#f0f0f0', margin: 0, fontSize: '14px', fontWeight: 700 }}>
              Head Videos/Courses
            </h3>
            <p style={{ color: '#444', margin: '2px 0 0', fontSize: '10px' }}>Course Automation</p>
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
        <MetricBox label="Courses" value={metrics.totalCourses} color="#00ff88" />
        <MetricBox label="Lessons" value={metrics.totalLessons} color="#00aaff" />
        <MetricBox label="Enrollments" value={formatNumber(metrics.totalEnrollments)} color="#aa00ff" />
        <MetricBox label="Revenue" value={`$${formatNumber(Math.floor(metrics.totalCourseRevenue))}`} color="#ff6600" />
      </div>

      {/* Student engagement breakdown */}
      <div
        style={{
          background: '#0a0a0a',
          borderRadius: '6px',
          padding: '10px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
          fontSize: '11px',
        }}
      >
        <EngagementStat icon="👥" label="Active" value={metrics.activeStudents} />
        <EngagementStat icon="✓" label="Completed" value={metrics.totalCompletions} />
      </div>

      {/* Completion rate progress bar */}
      <div
        style={{
          background: '#0a0a0a',
          borderRadius: '6px',
          padding: '10px',
          borderLeft: '2px solid #00aaff',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <p style={{ color: '#444', margin: 0, fontSize: '9px', textTransform: 'uppercase' }}>
            Completion Rate
          </p>
          <p style={{ color: '#00aaff', margin: 0, fontSize: '11px', fontWeight: 600 }}>
            {completionPercentage}%
          </p>
        </div>
        <div
          style={{
            background: '#1a1a1a',
            borderRadius: '3px',
            height: '6px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              background:
                completionPercentage >= 80
                  ? '#00ff88'
                  : completionPercentage >= 50
                    ? '#ffcc00'
                    : '#ff6600',
              height: '100%',
              width: `${completionPercentage}%`,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Rating and metrics row */}
      <div
        style={{
          background: '#0a0a0a',
          borderRadius: '6px',
          padding: '10px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
          fontSize: '11px',
        }}
      >
        <div style={{ borderLeft: '2px solid #aa00ff', paddingLeft: '8px' }}>
          <p style={{ color: '#444', margin: 0, fontSize: '9px' }}>Avg Rating</p>
          <p style={{ color: '#aa00ff', margin: '4px 0 0', fontSize: '13px', fontWeight: 700 }}>
            {metrics.avgCourseRating.toFixed(1)} / 5.0
          </p>
        </div>
        <div style={{ borderLeft: '2px solid #ff6600', paddingLeft: '8px' }}>
          <p style={{ color: '#444', margin: 0, fontSize: '9px' }}>Avg Completion</p>
          <p style={{ color: '#ff6600', margin: '4px 0 0', fontSize: '13px', fontWeight: 700 }}>
            {metrics.avgLessonCompletion.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Last published */}
      {metrics.lastPublishedAt && (
        <div
          style={{
            background: '#0a0a0a',
            borderRadius: '6px',
            padding: '10px',
            borderLeft: `2px solid #00ff88`,
          }}
        >
          <p style={{ color: '#444', margin: 0, fontSize: '9px', textTransform: 'uppercase' }}>
            Last Published
          </p>
          <p style={{ color: '#ccc', margin: '4px 0 0', fontSize: '11px', fontWeight: 600 }}>
            {metrics.lastPublishedTitle || 'Untitled Course'}
          </p>
          <p style={{ color: '#666', margin: '2px 0 0', fontSize: '9px', fontFamily: 'monospace' }}>
            {new Date(metrics.lastPublishedAt).toLocaleDateString()}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={onCreateCourse}
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
          New Course
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
 *   headVideosMetrics?: HeadVideosDashboardMetrics;
 * }
 *
 * // In dashboard page.tsx - add to Section function:
 * if (active === 'head-videos') {
 *   return data.headVideosMetrics ? (
 *     <div>
 *       <h2>Head Videos/Courses</h2>
 *       <HeadVideosDashboardCard
 *         metrics={data.headVideosMetrics}
 *         onCreateCourse={() => {
 *           // Open course creation modal or navigate to creation page
 *         }}
 *         onViewAnalytics={() => {
 *           // Navigate to Head Videos analytics page
 *         }}
 *       />
 *     </div>
 *   ) : null;
 * }
 *
 * // Add to NAV array:
 * {
 *   id: 'head-videos',
 *   label: 'Head Videos',
 *   icon: '🎓',
 *   group: 'Content'
 * }
 */
