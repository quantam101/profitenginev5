'use client';

import { useState, useEffect } from 'react';

interface TwitterMetrics {
  threadId: string;
  tweetCount: number;
  totalImpressions: number;
  totalEngagement: number;
  likes: number;
  retweets: number;
  replies: number;
  bookmarks: number;
  clicks: number;
  engagementRate: number;
  lastUpdated: string;
}

interface TwitterThreadCardProps {
  threadId?: string;
  status?: 'idle' | 'publishing' | 'published' | 'error';
  metrics?: TwitterMetrics;
  onPublish?: () => void;
}

export function TwitterThreadCard({
  threadId,
  status = 'idle',
  metrics,
  onPublish,
}: TwitterThreadCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const statusColor = {
    idle: '#666',
    publishing: '#ffcc00',
    published: '#00ff88',
    error: '#ff4444',
  };

  const statusLabel = {
    idle: 'Ready',
    publishing: 'Publishing...',
    published: 'Published',
    error: 'Error',
  };

  return (
    <div
      style={{
        background: '#111',
        border: '1px solid #1e1e1e',
        borderRadius: 8,
        padding: '16px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 3,
          height: '100%',
          background: statusColor[status],
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 20, flexShrink: 0 }}>𝕏</span>
        <div style={{ flex: 1 }}>
          <p style={{ color: '#f0f0f0', fontSize: 13, fontWeight: 700, margin: 0 }}>
            Twitter Threads
          </p>
          <p
            style={{
              color: statusColor[status],
              fontSize: 10,
              margin: '2px 0 0',
              fontFamily: 'monospace',
            }}
          >
            ● {statusLabel[status]}
          </p>
        </div>
      </div>

      {metrics ? (
        <div style={{ marginBottom: 12 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
              marginBottom: 10,
            }}
          >
            <div
              style={{
                background: '#0a0a0a',
                border: '1px solid #1a1a1a',
                borderRadius: 6,
                padding: '8px 10px',
              }}
            >
              <p style={{ color: '#666', fontSize: 9, margin: '0 0 3px', fontWeight: 600 }}>
                Engagement
              </p>
              <p style={{ color: '#00ff88', fontSize: 14, margin: 0, fontWeight: 700 }}>
                {metrics.totalEngagement}
              </p>
            </div>
            <div
              style={{
                background: '#0a0a0a',
                border: '1px solid #1a1a1a',
                borderRadius: 6,
                padding: '8px 10px',
              }}
            >
              <p style={{ color: '#666', fontSize: 9, margin: '0 0 3px', fontWeight: 600 }}>
                Rate
              </p>
              <p style={{ color: '#00aaff', fontSize: 14, margin: 0, fontWeight: 700 }}>
                {metrics.engagementRate.toFixed(1)}%
              </p>
            </div>
          </div>

          <div style={{ fontSize: 11, color: '#555', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            <div>
              <span style={{ color: '#666' }}>❤ </span>
              <span style={{ color: '#ccc' }}>{metrics.likes}</span>
            </div>
            <div>
              <span style={{ color: '#666' }}>🔄 </span>
              <span style={{ color: '#ccc' }}>{metrics.retweets}</span>
            </div>
            <div>
              <span style={{ color: '#666' }}>💬 </span>
              <span style={{ color: '#ccc' }}>{metrics.replies}</span>
            </div>
            <div>
              <span style={{ color: '#666' }}>📌 </span>
              <span style={{ color: '#ccc' }}>{metrics.bookmarks}</span>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ color: '#555', fontSize: 11, marginBottom: 10 }}>
          No threads published yet
        </div>
      )}

      {onPublish && (
        <button
          onClick={onPublish}
          disabled={isLoading || status === 'publishing'}
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 6,
            background: '#00ff8818',
            border: '1px solid #00ff8838',
            color: '#00ff88',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: 11,
            fontWeight: 700,
            opacity: isLoading ? 0.5 : 1,
          }}
        >
          {status === 'publishing' ? 'Publishing...' : 'Publish Thread'}
        </button>
      )}

      <p style={{ color: '#444', fontSize: 9, margin: '8px 0 0', fontFamily: 'monospace' }}>
        {threadId ? `ID: ${threadId.slice(0, 12)}...` : 'Not published'}
      </p>
    </div>
  );
}
