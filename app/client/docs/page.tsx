'use client';

import React, { useState } from 'react';

export default function ClientDocs() {
  const [activeTab, setActiveTab] = useState<
    'quickstart' | 'api' | 'webhook' | 'nodejs' | 'faq'
  >('quickstart');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Documentation</h1>
          <p className="text-gray-600 mt-2">
            Learn how to integrate with our payment platform
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b border-gray-200 flex">
            {[
              { id: 'quickstart', label: 'Quick Start' },
              { id: 'api', label: 'API Reference' },
              { id: 'webhook', label: 'Webhooks' },
              { id: 'nodejs', label: 'Node.js Example' },
              { id: 'faq', label: 'FAQ' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() =>
                  setActiveTab(
                    tab.id as
                      | 'quickstart'
                      | 'api'
                      | 'webhook'
                      | 'nodejs'
                      | 'faq'
                  )
                }
                className={`px-6 py-3 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* Quick Start */}
            {activeTab === 'quickstart' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">
                    Get Started in 5 Minutes
                  </h2>
                  <ol className="space-y-4 text-gray-600">
                    <li className="flex gap-4">
                      <span className="font-bold text-blue-600 flex-shrink-0">1.</span>
                      <div>
                        <p className="font-semibold text-gray-900">Sign up</p>
                        <p className="text-sm mt-1">
                          Go to{' '}
                          <code className="bg-gray-100 px-2 py-1 rounded">
                            /client/onboard
                          </code>{' '}
                          and create your account
                        </p>
                      </div>
                    </li>
                    <li className="flex gap-4">
                      <span className="font-bold text-blue-600 flex-shrink-0">2.</span>
                      <div>
                        <p className="font-semibold text-gray-900">
                          Connect Stripe
                        </p>
                        <p className="text-sm mt-1">
                          Link your Stripe account (get your account ID from
                          Stripe dashboard)
                        </p>
                      </div>
                    </li>
                    <li className="flex gap-4">
                      <span className="font-bold text-blue-600 flex-shrink-0">3.</span>
                      <div>
                        <p className="font-semibold text-gray-900">Test</p>
                        <p className="text-sm mt-1">
                          Create a $0.99 test charge to verify integration
                        </p>
                      </div>
                    </li>
                    <li className="flex gap-4">
                      <span className="font-bold text-blue-600 flex-shrink-0">4.</span>
                      <div>
                        <p className="font-semibold text-gray-900">
                          Configure Webhook
                        </p>
                        <p className="text-sm mt-1">
                          Tell us where to send payment notifications
                        </p>
                      </div>
                    </li>
                    <li className="flex gap-4">
                      <span className="font-bold text-blue-600 flex-shrink-0">5.</span>
                      <div>
                        <p className="font-semibold text-gray-900">Go Live</p>
                        <p className="text-sm mt-1">
                          Start accepting real customer payments
                        </p>
                      </div>
                    </li>
                  </ol>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-blue-900 font-semibold mb-2">
                    💡 What You Need
                  </p>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>✓ Business email address</li>
                    <li>✓ Stripe account</li>
                    <li>✓ HTTPS webhook URL for your server</li>
                    <li>✓ 5 minutes of setup time</li>
                  </ul>
                </div>
              </div>
            )}

            {/* API Reference */}
            {activeTab === 'api' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    API Endpoints
                  </h2>

                  {/* POST /api/client/register */}
                  <div className="mb-6 border-l-4 border-blue-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      POST /api/client/register
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Create a new client account
                    </p>
                    <div className="bg-gray-50 rounded mt-2 p-3 text-xs font-mono overflow-x-auto">
                      <pre>{`{
  "email": "business@example.com",
  "business_name": "My Company"
}`}</pre>
                    </div>
                    <p className="text-gray-600 text-sm mt-2">
                      Response includes your{' '}
                      <code className="bg-gray-100 px-1 rounded">
                        client_id
                      </code>{' '}
                      and{' '}
                      <code className="bg-gray-100 px-1 rounded">api_key</code>
                    </p>
                  </div>

                  {/* POST /api/client/[client_id]/oauth-callback */}
                  <div className="mb-6 border-l-4 border-green-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      POST /api/client/[client_id]/oauth-callback
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Connect your Stripe account
                    </p>
                    <div className="bg-gray-50 rounded mt-2 p-3 text-xs font-mono overflow-x-auto">
                      <pre>{`{
  "stripe_account_id": "acct_1234567890"
}`}</pre>
                    </div>
                  </div>

                  {/* POST /api/client/[client_id]/test-transaction */}
                  <div className="mb-6 border-l-4 border-purple-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      POST /api/client/[client_id]/test-transaction
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Create a test charge ($0.99 default)
                    </p>
                    <div className="bg-gray-50 rounded mt-2 p-3 text-xs font-mono overflow-x-auto">
                      <pre>{`{
  "amount": 99
}`}</pre>
                    </div>
                  </div>

                  {/* GET /api/client/[client_id]/transaction/[txn_id] */}
                  <div className="mb-6 border-l-4 border-orange-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      GET /api/client/[client_id]/transaction/[txn_id]
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Check transaction status
                    </p>
                  </div>

                  {/* POST /api/client/[client_id]/configure-webhook */}
                  <div className="mb-6 border-l-4 border-red-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      POST /api/client/[client_id]/configure-webhook
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Set your webhook URL for payment events
                    </p>
                    <div className="bg-gray-50 rounded mt-2 p-3 text-xs font-mono overflow-x-auto">
                      <pre>{`{
  "webhook_url": "https://your-app.com/webhooks/stripe",
  "events": ["charge.succeeded", "charge.failed"]
}`}</pre>
                    </div>
                  </div>

                  {/* GET /api/client/[client_id]/dashboard */}
                  <div className="mb-6 border-l-4 border-yellow-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      GET /api/client/[client_id]/dashboard
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Get all dashboard data (transactions, stats, etc)
                    </p>
                  </div>

                  {/* POST /api/client/[client_id]/go-live */}
                  <div className="border-l-4 border-pink-500 pl-4">
                    <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono">
                      POST /api/client/[client_id]/go-live
                    </code>
                    <p className="text-gray-600 text-sm mt-2">
                      Transition to production mode
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Webhooks */}
            {activeTab === 'webhook' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">
                    Understanding Webhooks
                  </h2>
                  <p className="text-gray-600 mb-4">
                    Webhooks are HTTP POST requests sent to your server when
                    payment events happen. This allows you to update your
                    records in real-time.
                  </p>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <p className="text-blue-900 font-semibold mb-2">
                      ✅ Events You'll Receive
                    </p>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>charge.succeeded - Payment processed successfully</li>
                      <li>charge.failed - Payment declined</li>
                      <li>charge.refunded - Payment refunded</li>
                      <li>payment_intent.succeeded - High-level payment event</li>
                    </ul>
                  </div>

                  <h3 className="font-semibold text-gray-900 mt-6 mb-2">
                    Webhook Payload Example
                  </h3>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-x-auto">
                    <pre>{`{
  "id": "evt_1234567890",
  "object": "event",
  "type": "charge.succeeded",
  "data": {
    "object": {
      "id": "ch_1234567890",
      "amount": 9900,
      "currency": "usd",
      "customer": "cus_1234567890"
    }
  },
  "client_id": "your-client-id",
  "stripe_account": "acct_1234567890"
}`}</pre>
                  </div>

                  <h3 className="font-semibold text-gray-900 mt-6 mb-2">
                    Webhook Security
                  </h3>
                  <ul className="text-gray-600 text-sm space-y-2">
                    <li>
                      • Always verify webhook signatures before processing
                    </li>
                    <li>• Use HTTPS only for webhook URLs</li>
                    <li>• Respond with 2xx status code to acknowledge receipt</li>
                    <li>
                      • We'll retry failed webhooks up to 5 times
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {/* Node.js Example */}
            {activeTab === 'nodejs' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">
                    Node.js Integration Example
                  </h2>

                  <h3 className="font-semibold text-gray-900 mt-4 mb-2">
                    1. Webhook Receiver
                  </h3>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-x-auto">
                    <pre>{`// app.js
const express = require('express');
const app = express();

app.post('/webhooks/stripe', express.json(), async (req, res) => {
  const event = req.body;

  console.log('Received webhook:', event.type);

  switch(event.type) {
    case 'charge.succeeded':
      const charge = event.data.object;
      console.log('Payment:', charge.amount, charge.currency);

      // Update your database
      await updatePaymentStatus(charge.id, 'completed');
      break;

    case 'charge.failed':
      console.log('Payment failed');
      break;
  }

  // Always respond with 200 OK
  res.json({ok: true});
});

app.listen(3000);`}</pre>
                  </div>

                  <h3 className="font-semibold text-gray-900 mt-4 mb-2">
                    2. Setup Your Webhook
                  </h3>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-x-auto">
                    <pre>{`const https = require('https');

const options = {
  hostname: 'api.example.com',
  path: '/api/client/YOUR_CLIENT_ID/configure-webhook',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

const req = https.request(options, (res) => {
  res.on('data', (d) => {
    process.stdout.write(d);
  });
});

req.on('error', (error) => {
  console.error(error);
});

req.write(JSON.stringify({
  webhook_url: 'https://your-app.com/webhooks/stripe',
  events: ['charge.succeeded', 'charge.failed']
}));

req.end();`}</pre>
                  </div>

                  <h3 className="font-semibold text-gray-900 mt-4 mb-2">
                    3. Trigger a Test Event
                  </h3>
                  <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-x-auto">
                    <pre>{`// Test webhook receiver locally
const localConfig = {
  webhook_url: 'https://localhost:3000/webhooks/stripe',
  // Will use ngrok or similar to expose local server
};`}</pre>
                  </div>
                </div>
              </div>
            )}

            {/* FAQ */}
            {activeTab === 'faq' && (
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    What is the commission rate?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    We take 2.5% of all successful transactions. This covers
                    payment processing, infrastructure, and support.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    When do I get paid?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Commission is calculated daily and paid out daily at 00:00
                    UTC. Your dashboard shows real-time balances.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Is there a monthly fee?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    No monthly fees. You only pay commission on successful
                    transactions. No volume, no charge.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Can I use test mode in production?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    No. Test mode is only for integration testing. Real
                    customer payments require going live.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    What if my webhook fails?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    We retry failed webhooks up to 5 times. We recommend logging
                    all webhooks for audit purposes. Check your webhook logs in
                    the dashboard.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    How do I test my integration?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Use the test transaction endpoint to create a $0.99 charge.
                    This will trigger a real webhook to your configured URL.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Is HTTPS required for webhooks?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Yes. All webhook URLs must be HTTPS for security. HTTP is
                    not accepted.
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    How do I revoke my API key?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Contact support. We'll generate a new API key and invalidate
                    the old one immediately.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Support */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Need Help?
          </h2>
          <p className="text-gray-600 mb-4">
            Can't find what you're looking for? Check out our support
            resources:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="mailto:support@example.com"
              className="text-center py-2 px-4 border border-blue-300 rounded-lg text-blue-600 hover:bg-blue-50 transition"
            >
              Email Support
            </a>
            <a
              href="#"
              className="text-center py-2 px-4 border border-blue-300 rounded-lg text-blue-600 hover:bg-blue-50 transition"
            >
              GitHub Issues
            </a>
            <a
              href="#"
              className="text-center py-2 px-4 border border-blue-300 rounded-lg text-blue-600 hover:bg-blue-50 transition"
            >
              Live Chat
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
