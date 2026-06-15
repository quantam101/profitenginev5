'use client';

import { useEffect, useState } from 'react';

interface ProspectSummary {
  total: number;
  pending: number;
  contacted: number;
  replied: number;
  negotiating: number;
  won: number;
  lost: number;
  avgGrade: string;
  conversionRate: string;
}

export default function ProspectsPage() {
  const [summary, setSummary] = useState<ProspectSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch('/api/prospects?action=summary');
        if (!res.ok) throw new Error('Failed to fetch summary');
        const data = await res.json();
        setSummary(data);
      } catch (err) {
        console.error('Error fetching prospect summary:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
    const interval = setInterval(fetchSummary, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading prospect pipeline...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">B2B Sales Pipeline</h1>
          <p className="text-lg text-gray-600">
            Prospect tracking & conversion monitoring • Already Here LLC
          </p>
        </div>

        {/* Pipeline Summary */}
        {summary && (
          <div className="bg-white rounded-lg shadow-md p-8 mb-8">
            <h2 className="text-2xl font-bold mb-6">Pipeline Status</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <p className="text-sm text-blue-600">Total Prospects</p>
                <p className="text-3xl font-bold text-blue-900">{summary.total}</p>
              </div>
              <div className="bg-yellow-50 p-4 rounded">
                <p className="text-sm text-yellow-600">Pending Contact</p>
                <p className="text-3xl font-bold text-yellow-900">{summary.pending}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded">
                <p className="text-sm text-purple-600">Replied</p>
                <p className="text-3xl font-bold text-purple-900">{summary.replied}</p>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <p className="text-sm text-green-600">Won</p>
                <p className="text-3xl font-bold text-green-900">{summary.won}</p>
              </div>
            </div>

            {/* Conversion Metrics */}
            <div className="mt-8 pt-8 border-t grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{summary.conversionRate}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Avg Grade</p>
                <p className="text-2xl font-bold text-gray-900">{summary.avgGrade}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Target Revenue</p>
                <p className="text-2xl font-bold text-gray-900">$500/day</p>
              </div>
            </div>
          </div>
        )}

        {/* Pipeline Stages */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold mb-6">Outreach Status</h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
              <div>
                <p className="font-semibold text-gray-900">Email Drafts Complete</p>
                <p className="text-sm text-gray-600">12 templates ready (see /docs/outreach-email-drafts.md)</p>
              </div>
              <span className="bg-green-100 text-green-800 px-4 py-2 rounded font-semibold">✅ Ready</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
              <div>
                <p className="font-semibold text-gray-900">Top 5 A/A- Prospects Identified</p>
                <p className="text-sm text-gray-600">AZ Mobile Diesel, Code 3, Cam Fleet Care, AZ Junk, Minutemen</p>
              </div>
              <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded font-semibold">📋 Next: Send Emails</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
              <div>
                <p className="font-semibold text-gray-900">Track Replies (Real-time)</p>
                <p className="text-sm text-gray-600">POST /api/prospects with status updates</p>
              </div>
              <span className="bg-purple-100 text-purple-800 px-4 py-2 rounded font-semibold">⏱️ Active</span>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">Quick Start</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-blue-900">
            <li>Review email drafts at <code className="bg-blue-100 px-2 py-1 rounded">/docs/outreach-email-drafts.md</code></li>
            <li>Personalize and send first 5 emails to A/A- grade prospects today</li>
            <li>Track replies via POST to <code className="bg-blue-100 px-2 py-1 rounded">/api/prospects</code></li>
            <li>Target: 5+ replies within 48 hours, schedule calls with interested prospects</li>
            <li>Close: Convert first 2-3 to pilot contracts ($500/day minimum)</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
