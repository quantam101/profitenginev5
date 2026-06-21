'use client';

import { useState, useEffect } from 'react';

interface YouTubeMetrics {
  videoId: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  watchTime: number;
}

interface YouTubeLongformStatus {
  status: string;
  lastUpload?: string;
  nextScheduled?: string;
  uploadCount: number;
  metrics?: YouTubeMetrics;
  isLoading: boolean;
  error?: string;
}

interface YouTubeLongformCardProps {
  channelId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const YouTubeLongformCard = ({
  channelId = process.env.NEXT_PUBLIC_YOUTUBE_CHANNEL_ID || 'UCtest123',
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}: YouTubeLongformCardProps) => {
  const [status, setStatus] = useState<YouTubeLongformStatus>({
    status: 'idle',
    uploadCount: 0,
    isLoading: true,
  });

  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch status on mount and optionally refresh
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/automation/youtube/status');
        const data = (await response.json()) as { data?: Record<string, unknown> };

        if (response.ok && data.data) {
          setStatus({
            status: 'ready',
            uploadCount: (data.data as Record<string, number>).uploadCount || 0,
            isLoading: false,
          });
        } else {
          setStatus((prev) => ({
            ...prev,
            isLoading: false,
            error: 'Failed to fetch status',
          }));
        }
      } catch (error) {
        setStatus((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        }));
      }
    };

    fetchStatus();

    if (autoRefresh) {
      const interval = setInterval(fetchStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const handleGenerateVideo = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch('/api/automation/youtube/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          postNumber: 1,
          videoGenerationApi: 'synthesia',
        }),
      });

      const data = (await response.json()) as { data?: { videoId?: string }; success?: boolean };

      if (response.ok && data.success) {
        setStatus((prev) => ({
          ...prev,
          status: 'success',
          uploadCount: (prev.uploadCount || 0) + 1,
          lastUpload: new Date().toISOString(),
        }));
      } else {
        setStatus((prev) => ({
          ...prev,
          status: 'error',
          error: 'Upload failed',
        }));
      }
    } catch (error) {
      setStatus((prev) => ({
        ...prev,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleScheduleVideo = async () => {
    const scheduledTime = new Date(Date.now() + 86400000); // 24 hours from now

    try {
      const response = await fetch('/api/automation/youtube/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          videoId: 'latest',
          publishAt: scheduledTime.toISOString(),
        }),
      });

      if (response.ok) {
        setStatus((prev) => ({
          ...prev,
          status: 'scheduled',
          nextScheduled: scheduledTime.toISOString(),
        }));
      }
    } catch (error) {
      console.error('Schedule error:', error);
    }
  };

  const cardStyle: React.CSSProperties = {
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    border: '1px solid rgba(255, 0, 0, 0.3)',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '20px',
    borderBottom: '1px solid rgba(255, 0, 0, 0.2)',
    paddingBottom: '12px',
  };

  const titleStyle: React.CSSProperties = {
    fontSize: '18px',
    fontWeight: 600,
    color: '#fff',
    margin: 0,
  };

  const badgeStyle: React.CSSProperties = {
    background: status.status === 'success' ? '#10b981' : '#ef4444',
    color: '#fff',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 600,
  };

  const statsStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '16px',
    marginBottom: '20px',
  };

  const statBoxStyle: React.CSSProperties = {
    background: 'rgba(255, 255, 255, 0.05)',
    padding: '16px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  };

  const statLabelStyle: React.CSSProperties = {
    fontSize: '12px',
    color: '#a0aec0',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '8px',
  };

  const statValueStyle: React.CSSProperties = {
    fontSize: '24px',
    fontWeight: 700,
    color: '#fff',
  };

  const buttonStyle: React.CSSProperties = {
    background: '#ef4444',
    color: '#fff',
    border: 'none',
    padding: '10px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    marginRight: '8px',
    marginBottom: '12px',
    transition: 'all 0.2s',
  };

  const buttonHoverStyle: React.CSSProperties = {
    ...buttonStyle,
    background: '#dc2626',
  };

  const errorStyle: React.CSSProperties = {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    color: '#fca5a5',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '13px',
    marginBottom: '12px',
  };

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={{ fontSize: '20px' }}>🎥</span>
        <h3 style={titleStyle}>YouTube Long-Form Automation</h3>
        <div style={badgeStyle}>{status.status.toUpperCase()}</div>
      </div>

      {/* Loading state */}
      {status.isLoading && (
        <div style={{ color: '#a0aec0', textAlign: 'center', padding: '20px' }}>
          Loading status...
        </div>
      )}

      {/* Error message */}
      {status.error && <div style={errorStyle}>{status.error}</div>}

      {/* Stats */}
      {!status.isLoading && (
        <>
          <div style={statsStyle}>
            <div style={statBoxStyle}>
              <div style={statLabelStyle}>Videos Uploaded</div>
              <div style={statValueStyle}>{status.uploadCount}</div>
            </div>

            <div style={statBoxStyle}>
              <div style={statLabelStyle}>Channel</div>
              <div style={{ ...statValueStyle, fontSize: '14px', wordBreak: 'break-all' }}>
                {channelId.slice(0, 8)}...
              </div>
            </div>

            {status.metrics && (
              <>
                <div style={statBoxStyle}>
                  <div style={statLabelStyle}>Total Views</div>
                  <div style={statValueStyle}>{status.metrics.views.toLocaleString()}</div>
                </div>

                <div style={statBoxStyle}>
                  <div style={statLabelStyle}>Total Likes</div>
                  <div style={statValueStyle}>{status.metrics.likes.toLocaleString()}</div>
                </div>
              </>
            )}
          </div>

          {/* Status info */}
          {status.lastUpload && (
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '16px' }}>
              Last upload: {new Date(status.lastUpload).toLocaleString()}
            </div>
          )}

          {status.nextScheduled && (
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '16px' }}>
              Scheduled for: {new Date(status.nextScheduled).toLocaleString()}
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              style={buttonStyle}
              onMouseEnter={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#dc2626';
              }}
              onMouseLeave={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#ef4444';
              }}
              onClick={handleGenerateVideo}
              disabled={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate & Upload'}
            </button>

            <button
              style={{
                ...buttonStyle,
                background: '#1e40af',
              }}
              onMouseEnter={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#1e3a8a';
              }}
              onMouseLeave={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#1e40af';
              }}
              onClick={handleScheduleVideo}
              disabled={isGenerating}
            >
              Schedule
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default YouTubeLongformCard;
