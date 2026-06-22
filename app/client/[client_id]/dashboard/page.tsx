'use client';

import React, { useEffect, useState } from 'react';

interface DashboardData {
  ok: boolean;
  client: {
    id: string;
    email: string;
    business_name: string;
    status: string;
    api_key: string;
    created_at: number;
  };
  stripe_connection: {
    connected: boolean;
    account_id: string | null;
    test_mode: boolean;
  };
  setup_progress: {
    step: number;
    completed: string[];
    next: string;
  };
  revenue: {
    test_transactions: number;
    live_transactions: number;
    total_volume: string;
    total_volume_cents: number;
    commission_earned: string;
    commission_earned_cents: number;
    commission_rate: number;
    payout_schedule: string;
  };
  webhook: {
    configured: boolean;
    url: string | null;
  };
  webhook_logs: Array<{
    event_id: string | null;
    transaction_id: string;
    stripe_charge_id: string;
    timestamp: number;
    status: string;
    webhook_delivered: boolean;
    webhook_response_code: number | null;
  }>;
  go_live_checklist: Array<{
    item: string;
    done: boolean;
  }>;
  ready_to_go_live: boolean;
}

export default function ClientDashboard({
  params,
}: {
  params: { client_id: string };
}) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(
          `/api/client/${params.client_id}/dashboard`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch dashboard');
        }

        const dashboardData = await response.json();
        setData(dashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [params.client_id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error || 'Failed to load dashboard'}</p>
        </div>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    signup: 'bg-blue-100 text-blue-800',
    stripe_connected: 'bg-yellow-100 text-yellow-800',
    testing: 'bg-orange-100 text-orange-800',
    live: 'bg-green-100 text-green-800',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {data.client.business_name}
          </h1>
          <p className="text-gray-600 mt-1">{data.client.email}</p>

          <div className="mt-4 flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                statusColors[data.client.status] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {data.client.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Revenue Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Volume</p>
            <p className="text-2xl font-bold text-gray-900">
              ${data.revenue.total_volume}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {data.revenue.test_transactions + data.revenue.live_transactions} transactions
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Commission Earned</p>
            <p className="text-2xl font-bold text-green-600">
              ${data.revenue.commission_earned}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {data.revenue.commission_rate}% of volume
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Test Transactions</p>
            <p className="text-2xl font-bold text-blue-600">
              {data.revenue.test_transactions}
            </p>
            <p className="text-xs text-gray-500 mt-1">In test mode</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Live Transactions</p>
            <p className="text-2xl font-bold text-purple-600">
              {data.revenue.live_transactions}
            </p>
            <p className="text-xs text-gray-500 mt-1">In production</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Setup Progress */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Setup Progress
              </h2>

              <div className="space-y-3">
                {data.go_live_checklist.map((item, idx) => (
                  <div key={idx} className="flex items-center">
                    <div
                      className={`h-6 w-6 rounded border-2 flex items-center justify-center ${
                        item.done
                          ? 'bg-green-500 border-green-500'
                          : 'border-gray-300'
                      }`}
                    >
                      {item.done && (
                        <span className="text-white text-sm">✓</span>
                      )}
                    </div>
                    <span
                      className={`ml-3 ${
                        item.done ? 'text-gray-900' : 'text-gray-600'
                      }`}
                    >
                      {item.item}
                    </span>
                  </div>
                ))}
              </div>

              {data.ready_to_go_live && data.client.status !== 'live' && (
                <a
                  href={`/client/${data.client.id}/go-live-confirm`}
                  className="mt-6 block w-full text-center bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                >
                  🚀 Go Live Now
                </a>
              )}

              {data.client.status === 'live' && (
                <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-green-800 font-semibold">
                    ✅ You&apos;re Live!
                  </p>
                  <p className="text-green-700 text-sm mt-2">
                    Accepting real customer payments
                  </p>
                </div>
              )}
            </div>

            {/* Webhook Status */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Webhook Configuration
              </h2>

              <div className="space-y-2">
                {data.webhook.configured ? (
                  <div>
                    <p className="text-sm text-green-600 font-semibold">✅ Configured</p>
                    <p className="text-xs text-gray-600 mt-1 break-all">
                      {data.webhook.url}
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm text-yellow-600 font-semibold">⚠️ Not Configured</p>
                    <p className="text-xs text-gray-600 mt-1">
                      Configure your webhook to receive payment events
                    </p>
                    <a
                      href={`/client/${data.client.id}/configure-webhook`}
                      className="mt-3 block text-center text-sm bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded transition"
                    >
                      Configure Webhook
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* API Key */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                API Key
              </h2>

              <div className="bg-gray-50 rounded border border-gray-200 p-3">
                <code className="text-xs text-gray-700 break-all">
                  {data.client.api_key}
                </code>
              </div>

              <p className="text-xs text-gray-600 mt-3">
                Use this to authenticate webhook requests from your integration
              </p>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Connection Status */}
            {!data.stripe_connection.connected && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <p className="text-yellow-800 font-semibold">
                  Connect Your Stripe Account
                </p>
                <p className="text-yellow-700 text-sm mt-1">
                  You need to connect your Stripe account to start accepting payments.
                </p>
                <a
                  href={`/client/${data.client.id}/connect-stripe`}
                  className="mt-3 inline-block text-sm bg-yellow-600 hover:bg-yellow-700 text-white py-1 px-3 rounded transition"
                >
                  Connect Stripe
                </a>
              </div>
            )}

            {/* Stripe Connection Info */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Stripe Connection
              </h2>

              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="text-sm font-semibold text-gray-900 mt-1">
                    {data.stripe_connection.connected ? (
                      <span className="text-green-600">✅ Connected</span>
                    ) : (
                      <span className="text-yellow-600">⚠️ Not Connected</span>
                    )}
                  </p>
                </div>

                {data.stripe_connection.account_id && (
                  <div>
                    <p className="text-sm text-gray-600">Account ID</p>
                    <p className="text-sm font-mono text-gray-900 mt-1">
                      {data.stripe_connection.account_id}
                    </p>
                  </div>
                )}

                <div>
                  <p className="text-sm text-gray-600">Mode</p>
                  <p className="text-sm font-semibold text-gray-900 mt-1">
                    {data.stripe_connection.test_mode ? (
                      <span className="text-orange-600">🧪 Test Mode</span>
                    ) : (
                      <span className="text-green-600">🚀 Production Mode</span>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Transaction Log */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Recent Transactions
              </h2>

              {data.webhook_logs.length === 0 ? (
                <p className="text-gray-600 text-sm">No transactions yet</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-gray-200">
                      <tr>
                        <th className="text-left text-gray-600 font-semibold py-2">
                          Charge ID
                        </th>
                        <th className="text-left text-gray-600 font-semibold py-2">
                          Status
                        </th>
                        <th className="text-left text-gray-600 font-semibold py-2">
                          Webhook
                        </th>
                        <th className="text-left text-gray-600 font-semibold py-2">
                          Date
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.webhook_logs.map((log) => (
                        <tr
                          key={log.transaction_id}
                          className="border-b border-gray-100 hover:bg-gray-50"
                        >
                          <td className="py-2 font-mono text-gray-900">
                            {log.stripe_charge_id.substring(0, 20)}...
                          </td>
                          <td className="py-2">
                            <span
                              className={`px-2 py-1 rounded text-xs font-semibold ${
                                log.status === 'succeeded'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {log.status}
                            </span>
                          </td>
                          <td className="py-2">
                            {log.webhook_delivered ? (
                              <span className="text-green-600 text-sm">
                                ✅ Delivered
                              </span>
                            ) : (
                              <span className="text-yellow-600 text-sm">
                                ⏳ Pending
                              </span>
                            )}
                          </td>
                          <td className="py-2 text-gray-600">
                            {new Date(log.timestamp).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
