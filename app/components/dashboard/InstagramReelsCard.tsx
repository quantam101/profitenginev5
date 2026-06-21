/**
 * INSTAGRAM REELS AUTOMATION DASHBOARD CARD
 *
 * Displays:
 * - Current reel generation status
 * - Published reels list with engagement metrics
 * - Quick action buttons for manual generation
 * - Batch processing controls
 * - Video generation API selector
 * - Scheduled posting timeline
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';

interface ReelMetadata {
  reelId: string;
  status: 'pending' | 'generating' | 'uploaded' | 'published' | 'failed';
  postId?: string;
  postUrl?: string;
  script?: {
    title: string;
    hook: string;
    cta: string;
  };
  metrics?: {
    views?: number;
    likes?: number;
    comments?: number;
    shares?: number;
    saves?: number;
  };
  publishedTime?: string;
  error?: string;
}

interface DashboardStats {
  totalReels: number;
  publishedCount: number;
  failedCount: number;
  pendingCount: number;
  totalViews: number;
  totalEngagement: number;
}

export function InstagramReelsCard() {
  const [reels, setReels] = useState<ReelMetadata[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalReels: 0,
    publishedCount: 0,
    failedCount: 0,
    pendingCount: 0,
    totalViews: 0,
    totalEngagement: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedApi, setSelectedApi] = useState('synthesia');
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchReels = useCallback(async () => {
    try {
      const response = await fetch('/api/automation/instagram/list');
      const data = (await response.json()) as {
        success: boolean;
        data: { total: number; reels: ReelMetadata[] };
      };

      if (data.success && data.data.reels) {
        setReels(data.data.reels);
        calculateStats(data.data.reels);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reels');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch reel statuses
  useEffect(() => {
    fetchReels();
    const interval = setInterval(fetchReels, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchReels]);

  function calculateStats(reelsList: ReelMetadata[]) {
    let totalViews = 0;
    let totalEngagement = 0;
    let publishedCount = 0;
    let failedCount = 0;
    let pendingCount = 0;

    for (const reel of reelsList) {
      if (reel.metrics) {
        totalViews += reel.metrics.views || 0;
        totalEngagement +=
          (reel.metrics.likes || 0) +
          (reel.metrics.comments || 0) +
          (reel.metrics.shares || 0) +
          (reel.metrics.saves || 0);
      }

      if (reel.status === 'published') publishedCount++;
      else if (reel.status === 'failed') failedCount++;
      else if (reel.status === 'pending' || reel.status === 'generating') pendingCount++;
    }

    setStats({
      totalReels: reelsList.length,
      publishedCount,
      failedCount,
      pendingCount,
      totalViews,
      totalEngagement,
    });
  }

  async function generateReel() {
    setIsGenerating(true);
    try {
      const response = await fetch('/api/automation/instagram/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Quick Generate: ' + new Date().toLocaleDateString(),
          hook: 'Check out this quick insight about building wealth...',
          mainPoints: [
            'Start with what you know best',
            'Build an audience before selling',
            'Create multiple revenue streams',
          ],
          cta: 'Link in bio for details',
          duration: 60,
          hashtags: ['wealth', 'entrepreneurship', 'investing'],
        }),
      });

      if (response.ok) {
        setError(null);
        fetchReels();
      } else {
        const errorData = (await response.json()) as { error?: string };
        setError(errorData.error || 'Failed to generate reel');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'generating':
        return 'text-blue-600';
      case 'pending':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'generating':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Instagram Reels</h2>
          <p className="text-sm text-gray-500">
            Automated video generation and publishing
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-blue-600">{stats.totalReels}</div>
          <div className="text-xs text-gray-500">Total Reels</div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-green-50 rounded p-3">
          <div className="text-2xl font-bold text-green-600">
            {stats.publishedCount}
          </div>
          <div className="text-xs text-gray-600">Published</div>
        </div>
        <div className="bg-yellow-50 rounded p-3">
          <div className="text-2xl font-bold text-yellow-600">
            {stats.pendingCount}
          </div>
          <div className="text-xs text-gray-600">Pending</div>
        </div>
        <div className="bg-red-50 rounded p-3">
          <div className="text-2xl font-bold text-red-600">{stats.failedCount}</div>
          <div className="text-xs text-gray-600">Failed</div>
        </div>
        <div className="bg-blue-50 rounded p-3">
          <div className="text-2xl font-bold text-blue-600">
            {stats.totalViews.toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">Total Views</div>
        </div>
      </div>

      {/* Configuration Section */}
      <div className="mb-6 pb-6 border-b border-gray-200">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Video Generation API
        </label>
        <select
          value={selectedApi}
          onChange={(e) => setSelectedApi(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="synthesia">Synthesia.io (Avatar Video)</option>
          <option value="d-id">D-ID (Avatar Video)</option>
          <option value="replicate">Replicate (Text-to-Video)</option>
          <option value="elevenlabs">ElevenLabs (Voiceover Only)</option>
        </select>
        <p className="text-xs text-gray-500 mt-1">
          Configure VIDEO_GENERATION_API env var to change default
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={generateReel}
          disabled={isGenerating}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 px-4 rounded-md text-sm font-medium transition"
        >
          {isGenerating ? 'Generating...' : 'Generate Single Reel'}
        </button>
        <button
          onClick={() => window.open('/dashboard/instagram/batch', '_blank')}
          className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-md text-sm font-medium transition"
        >
          Batch Generator
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6 text-sm">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8 text-gray-500">
          Loading reel data...
        </div>
      )}

      {/* Reels List */}
      {!loading && reels.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-700 mb-3">Recent Reels</h3>
          {reels.slice(0, 5).map((reel) => (
            <div
              key={reel.reelId}
              className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 text-sm">
                    {reel.script?.title || `Reel ${reel.reelId.slice(0, 8)}`}
                  </h4>
                  <p className="text-xs text-gray-600 mt-1">
                    {reel.script?.hook}
                  </p>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ml-2 ${getStatusBadgeColor(
                    reel.status
                  )}`}
                >
                  {reel.status}
                </span>
              </div>

              {/* Metrics */}
              {reel.metrics && (
                <div className="flex gap-4 mt-3 text-xs text-gray-600">
                  <span>👁️ {reel.metrics.views?.toLocaleString() || 0}</span>
                  <span>❤️ {reel.metrics.likes?.toLocaleString() || 0}</span>
                  <span>💬 {reel.metrics.comments?.toLocaleString() || 0}</span>
                  <span>🔄 {reel.metrics.shares?.toLocaleString() || 0}</span>
                  <span>🔖 {reel.metrics.saves?.toLocaleString() || 0}</span>
                </div>
              )}

              {/* Posted Link */}
              {reel.postUrl && (
                <a
                  href={reel.postUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline mt-2 inline-block"
                >
                  View on Instagram →
                </a>
              )}

              {/* Error Message */}
              {reel.error && (
                <p className="text-xs text-red-600 mt-2">Error: {reel.error}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && reels.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm mb-3">No reels yet</p>
          <button
            onClick={generateReel}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Create your first reel
          </button>
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500">
        <p>
          Configuration: IG_USER_ID, FB_PAGE_ACCESS_TOKEN, VIDEO_GENERATION_API
        </p>
        <p className="mt-1">
          Endpoints: POST /api/automation/instagram/generate, /batch, /webhook
        </p>
      </div>
    </div>
  );
}
