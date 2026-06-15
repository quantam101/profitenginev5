'use client';

import { useState } from 'react';
import { loadStripe } from '@stripe/js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '');

interface StripeCheckoutProps {
  jobId: string;
  jobTitle: string;
  pay: number;
  contractorId: string;
  customerEmail: string;
  onSuccess?: (intentId: string) => void;
  onError?: (error: string) => void;
}

function CheckoutForm({
  jobId,
  jobTitle,
  pay,
  contractorId,
  customerEmail,
  onSuccess,
  onError,
}: StripeCheckoutProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      setError('Stripe not loaded');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Step 1: Create PaymentIntent
      const intentRes = await fetch('/api/payments/intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobId,
          jobTitle,
          pay,
          contractorId,
          customerEmail,
        }),
      });

      if (!intentRes.ok) {
        const data = await intentRes.json();
        throw new Error(data.error || 'Failed to create payment');
      }

      const { clientSecret, intentId } = await intentRes.json();

      // Step 2: Confirm payment with Stripe
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) throw new Error('Card element not found');

      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            email: customerEmail,
          },
        },
      });

      if (result.error) {
        setError(result.error.message || 'Payment failed');
        onError?.(result.error.message || 'Payment failed');
      } else if (result.paymentIntent?.status === 'succeeded') {
        onSuccess?.(intentId);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Payment failed';
      setError(message);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="border border-gray-300 rounded p-3">
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                  color: '#aab7c4',
                },
              },
              invalid: {
                color: '#9e2146',
              },
            },
          }}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || loading}
        className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded transition-colors"
      >
        {loading ? 'Processing...' : `Pay $${pay.toFixed(2)}`}
      </button>

      <p className="text-xs text-gray-500 text-center">
        Secure payment powered by Stripe
      </p>
    </form>
  );
}

export function StripeCheckout(props: StripeCheckoutProps) {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm {...props} />
    </Elements>
  );
}
