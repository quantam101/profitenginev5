'use client';

import { useState, useEffect } from 'react';

interface FacelessVideoMetrics {
  videoId: string;
  platform: 'youtube' | 'tiktok' | 'instagram' | 'reddit';
  views: number;
  likes: number;
  comments: number;
  shares: number;
  engagementRate: number;
}

interface FacelessVideoStatus {
  status: string;
  lastGeneration?: string;
  nextScheduled?: string;
  generationCount: number;
  platformStats: {
    youtube: number;
    tiktok: number;
    instagram: number;
    reddit: number;
  };
  isLoading: boolean;
  error?: string;
}

interface FacelessVideosCardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const FacelessVideosCard = ({
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}: FacelessVideosCardProps) => {
  const [status, setStatus] = useState<FacelessVideoStatus>({
    status: 'idle',
    generationCount: 0,
    platformStats: {
      youtube: 0,
      tiktok: 0,
      instagram: 0,
      reddit: 0,
    },
    isLoading: true,
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<
    Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>
  >(['youtube', 'tiktok']);

  // Fetch status on mount and optionally refresh
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/automation/faceless-videos/status');
        const data = (await response.json()) as { data?: Record<string, unknown> };

        if (response.ok && data.data) {
          setStatus({
            status: 'ready',
            generationCount: (data.data as Record<string, number>).generationCount || 0,
            platformStats: {
              youtube: 0,
              tiktok: 0,
              instagram: 0,
              reddit: 0,
            },
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
      const response = await fetch('/api/automation/faceless-videos/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          postNumber: 1,
          videoProvider: 'd-id',
          platforms: selectedPlatforms,
          publishImmediately: true,
        }),
      });

      const data = (await response.json()) as { success?: boolean; data?: Record<string, unknown> };

      if (response.ok && data.success) {
        setStatus((prev) => ({
          ...prev,
          status: 'success',
          generationCount: (prev.generationCount || 0) + 1,
          lastGeneration: new Date().toISOString(),
        }));
      } else {
        setStatus((prev) => ({
          ...prev,
          status: 'error',
          error: 'Generation failed',
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

  const togglePlatform = (platform: 'youtube' | 'tiktok' | 'instagram' | 'reddit') => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform) ? prev.filter((p) => p !== platform) : [...prev, platform]
    );
  };

  const cardStyle: React.CSSProperties = {
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    border: '1px solid rgba(138, 43, 226, 0.3)',
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
    borderBottom: '1px solid rgba(138, 43, 226, 0.2)',
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

  const platformSelectStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '12px',
    marginBottom: '16px',
  };

  const platformButtonStyle: (isSelected: boolean) => React.CSSProperties = (isSelected) => ({
    background: isSelected ? '#8a2be2' : 'rgba(138, 43, 226, 0.2)',
    color: '#fff',
    border: isSelected ? '2px solid #8a2be2' : '1px solid rgba(138, 43, 226, 0.4)',
    padding: '8px 12px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 600,
    transition: 'all 0.2s',
  });

  const actionButtonStyle: React.CSSProperties = {
    background: '#8a2be2',
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

  const errorStyle: React.CSSProperties = {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    color: '#fca5a5',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '13px',
    marginBottom: '12px',
  };

  const platformStats: (platform: 'youtube' | 'tiktok' | 'instagram' | 'reddit') => string = (
    platform
  ) => {
    const icons: Record<string, string> = {
      youtube: '📺',
      tiktok: '🎵',
      instagram: '📷',
      reddit: '🔗',
    };
    const names: Record<string, string> = {
      youtube: 'YouTube',
      tiktok: 'TikTok',
      instagram: 'Instagram',
      reddit: 'Reddit',
    };

    return `${icons[platform]} ${names[platform]}`;
  };

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={{ fontSize: '20px' }}>🤖</span>
        <h3 style={titleStyle}>Faceless Videos Automation</h3>
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
              <div style={statLabelStyle}>Videos Generated</div>
              <div style={statValueStyle}>{status.generationCount}</div>
            </div>

            <div style={statBoxStyle}>
              <div style={statLabelStyle}>Platforms Available</div>
              <div style={statValueStyle}>4</div>
            </div>

            <div style={statBoxStyle}>
              <div style={statLabelStyle}>YouTube Posts</div>
              <div style={statValueStyle}>{status.platformStats.youtube}</div>
            </div>

            <div style={statBoxStyle}>
              <div style={statLabelStyle}>TikTok Posts</div>
              <div style={statValueStyle}>{status.platformStats.tiktok}</div>
            </div>
          </div>

          {/* Status info */}
          {status.lastGeneration && (
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '16px' }}>
              Last generation: {new Date(status.lastGeneration).toLocaleString()}
            </div>
          )}

          {/* Platform selection */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Select Platforms
            </div>
            <div style={platformSelectStyle}>
              {(['youtube', 'tiktok', 'instagram', 'reddit'] as const).map((platform) => (
                <button
                  key={platform}
                  style={platformButtonStyle(selectedPlatforms.includes(platform))}
                  onClick={() => togglePlatform(platform)}
                >
                  {platformStats(platform)}
                </button>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              style={actionButtonStyle}
              onMouseEnter={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#6a1b9a';
              }}
              onMouseLeave={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#8a2be2';
              }}
              onClick={handleGenerateVideo}
              disabled={isGenerating || selectedPlatforms.length === 0}
            >
              {isGenerating ? 'Generating...' : 'Generate & Publish'}
            </button>

            <button
              style={{
                ...actionButtonStyle,
                background: 'rgba(138, 43, 226, 0.3)',
                color: '#c084fc',
              }}
              onMouseEnter={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = 'rgba(138, 43, 226, 0.5)';
              }}
              onMouseLeave={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = 'rgba(138, 43, 226, 0.3)';
              }}
              onClick={() => {
                setSelectedPlatforms(['youtube', 'tiktok']);
              }}
              disabled={isGenerating}
            >
              Reset Platforms
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default FacelessVideosCard;
