'use client';

import React, { useState } from 'react';

type Step = 'register' | 'stripe' | 'test' | 'webhook' | 'live' | 'complete';

interface ClientData {
  client_id: string;
  email: string;
  business_name: string;
  status: string;
  api_key: string;
}

export default function ClientOnboarding() {
  const [step, setStep] = useState<Step>('register');
  const [clientData, setClientData] = useState<ClientData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Register
  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const email = formData.get('email') as string;
    const businessName = formData.get('business_name') as string;

    try {
      const response = await fetch('/api/client/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, business_name: businessName }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Registration failed');
      }

      const data = await response.json();
      setClientData(data);
      setStep('stripe');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Connect Stripe
  const handleConnectStripe = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const stripeAccountId = formData.get('stripe_account_id') as string;

    if (!clientData) return;

    try {
      const response = await fetch(
        `/api/client/${clientData.client_id}/oauth-callback`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stripe_account_id: stripeAccountId }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Stripe connection failed');
      }

      setStep('test');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Test Payment
  const handleTestPayment = async () => {
    setLoading(true);
    setError('');

    if (!clientData) return;

    try {
      const response = await fetch(
        `/api/client/${clientData.client_id}/test-transaction`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount: 99 }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Test transaction failed');
      }

      const data = await response.json();
      setStep('webhook');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test payment failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 4: Configure Webhook
  const handleConfigureWebhook = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const webhookUrl = formData.get('webhook_url') as string;

    if (!clientData) return;

    try {
      const response = await fetch(
        `/api/client/${clientData.client_id}/configure-webhook`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            webhook_url: webhookUrl,
            events: [
              'charge.succeeded',
              'charge.failed',
              'charge.refunded',
            ],
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Webhook configuration failed');
      }

      setStep('live');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Webhook configuration failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 5: Go Live
  const handleGoLive = async () => {
    setLoading(true);
    setError('');

    if (!clientData) return;

    try {
      const response = await fetch(
        `/api/client/${clientData.client_id}/go-live`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            confirmation: 'I am ready for live customer payments',
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Go-live failed');
      }

      setStep('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Go-live failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Payment Platform Onboarding
          </h1>
          <p className="text-gray-600 mb-8">
            Complete setup in 5 easy steps
          </p>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between mb-2">
              {['register', 'stripe', 'test', 'webhook', 'live', 'complete'].map(
                (s, i) => (
                  <div
                    key={s}
                    className={`h-2 flex-1 mx-1 rounded ${
                      ['register', 'stripe', 'test', 'webhook', 'live', 'complete'].indexOf(
                        step
                      ) >= i
                        ? 'bg-blue-500'
                        : 'bg-gray-200'
                    }`}
                  ></div>
                )
              )}
            </div>
            <p className="text-sm text-gray-500">
              Step {['register', 'stripe', 'test', 'webhook', 'live', 'complete'].indexOf(step) + 1} of 6
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Step 1: Register */}
          {step === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Step 1: Create Your Account
              </h2>
              <p className="text-gray-600">
                Provide your email and business information to get started.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="your@business.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Name
                </label>
                <input
                  type="text"
                  name="business_name"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Your Company Inc."
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          )}

          {/* Step 2: Connect Stripe */}
          {step === 'stripe' && clientData && (
            <form onSubmit={handleConnectStripe} className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Step 2: Connect Your Stripe Account
              </h2>
              <p className="text-gray-600">
                Link your Stripe account to start accepting payments.
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-900">
                  <strong>Client ID:</strong> {clientData.client_id}
                </p>
                <p className="text-sm text-blue-900 mt-1">
                  <strong>API Key:</strong> {clientData.api_key.substring(0, 20)}...
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stripe Account ID (acct_...)
                </label>
                <input
                  type="text"
                  name="stripe_account_id"
                  required
                  pattern="acct_.*"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="acct_1234567890abcdef"
                />
                <p className="text-xs text-gray-500 mt-2">
                  Get this from your Stripe Dashboard → Settings → Account ID
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                {loading ? 'Connecting...' : 'Connect Stripe'}
              </button>
            </form>
          )}

          {/* Step 3: Test Payment */}
          {step === 'test' && clientData && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Step 3: Make a Test Payment
              </h2>
              <p className="text-gray-600">
                Create a $0.99 test charge to verify your Stripe integration works.
              </p>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-900">
                  ✅ Stripe account connected successfully!
                </p>
              </div>

              <button
                onClick={handleTestPayment}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                {loading ? 'Processing Test Payment...' : 'Process $0.99 Test Payment'}
              </button>

              <p className="text-sm text-gray-600">
                This will create a test charge on your Stripe account to verify
                everything is working correctly.
              </p>
            </div>
          )}

          {/* Step 4: Configure Webhook */}
          {step === 'webhook' && clientData && (
            <form onSubmit={handleConfigureWebhook} className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Step 4: Configure Your Webhook
              </h2>
              <p className="text-gray-600">
                Tell us where to send your payment notifications.
              </p>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-900">
                  ✅ Test payment received! Now configure your webhook URL.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Webhook URL
                </label>
                <input
                  type="url"
                  name="webhook_url"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="https://your-app.com/webhooks/stripe"
                />
                <p className="text-xs text-gray-500 mt-2">
                  This is where we&apos;ll send payment notifications. Must be HTTPS.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                {loading ? 'Configuring...' : 'Configure Webhook'}
              </button>
            </form>
          )}

          {/* Step 5: Go Live */}
          {step === 'live' && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Step 5: Go Live
              </h2>
              <p className="text-gray-600">
                Ready to start accepting real customer payments? Click the button
                below to go live.
              </p>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-900 font-semibold mb-2">
                  ⚠️ Important
                </p>
                <ul className="text-sm text-yellow-800 list-disc list-inside space-y-1">
                  <li>You will be charged 2.5% commission on all transactions</li>
                  <li>Webhooks must be properly configured to receive events</li>
                  <li>Real customer payments will be processed immediately</li>
                </ul>
              </div>

              <button
                onClick={handleGoLive}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                {loading ? 'Going Live...' : '🚀 Go Live'}
              </button>
            </div>
          )}

          {/* Step 6: Complete */}
          {step === 'complete' && clientData && (
            <div className="space-y-4">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-green-600 mb-2">
                  🎉 You&apos;re All Set!
                </h2>
                <p className="text-gray-600">
                  Your payment platform is now live and ready to accept customer
                  payments.
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="space-y-2">
                  <p className="text-sm">
                    <strong>Client ID:</strong>{' '}
                    <code className="bg-white px-2 py-1 rounded">
                      {clientData.client_id}
                    </code>
                  </p>
                  <p className="text-sm">
                    <strong>API Key:</strong>{' '}
                    <code className="bg-white px-2 py-1 rounded text-xs">
                      {clientData.api_key}
                    </code>
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <a
                  href={`/client/${clientData.client_id}/dashboard`}
                  className="block text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                >
                  View Your Dashboard
                </a>
                <a
                  href="/client/docs"
                  className="block text-center bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-4 rounded-lg transition"
                >
                  Read Documentation
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
