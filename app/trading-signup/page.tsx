'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface SignupFormData {
  email: string;
  password: string;
  capitalAmount: number;
  riskPreference: 'conservative' | 'moderate' | 'aggressive';
  agreeToTerms: boolean;
}

export default function TradingSignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<SignupFormData>({
    email: '',
    password: '',
    capitalAmount: 5000,
    riskPreference: 'moderate',
    agreeToTerms: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'intro' | 'form' | 'kyc' | 'success'>('intro');

  const handleFieldChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
      ...(name === 'capitalAmount' && { capitalAmount: parseFloat(value) }),
    }));
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate
      if (!formData.email || !formData.password) {
        throw new Error('Email and password are required');
      }
      if (formData.password.length < 8) {
        throw new Error('Password must be at least 8 characters');
      }
      if (formData.capitalAmount < 1000) {
        throw new Error('Minimum capital amount is $1,000');
      }
      if (!formData.agreeToTerms) {
        throw new Error('You must agree to the terms and conditions');
      }

      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Signup failed');
      }

      const data = await response.json();
      localStorage.setItem('authToken', data.token);
      setStep('success');

      // Redirect after 2 seconds
      setTimeout(() => {
        router.push('/trading-signup/kyc');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      style={{
        minHeight: '100vh',
        background:
          'radial-gradient(circle at 15% 0%, rgba(90,162,255,.18), transparent 32rem), #050914',
        color: '#eef5ff',
        fontFamily: 'Arial, Helvetica, sans-serif',
        padding: '20px',
      }}
    >
      {step === 'intro' && <IntroSection onNext={() => setStep('form')} />}
      {step === 'form' && (
        <SignupForm
          formData={formData}
          error={error}
          loading={loading}
          onFieldChange={handleFieldChange}
          onSubmit={handleSignup}
          onBack={() => setStep('intro')}
        />
      )}
      {step === 'success' && <SuccessSection />}
    </main>
  );
}

function IntroSection({ onNext }: { onNext: () => void }) {
  return (
    <div
      style={{
        maxWidth: '1000px',
        margin: '0 auto',
        paddingTop: '60px',
        paddingBottom: '60px',
        textAlign: 'center',
      }}
    >
      <div style={{ marginBottom: '60px' }}>
        <h1
          style={{
            fontSize: '48px',
            fontWeight: 700,
            margin: '0 0 16px',
            letterSpacing: '-1px',
          }}
        >
          PROFIT<span style={{ color: '#5aa2ff' }}>ENGINE</span> Trading System
        </h1>
        <p style={{ fontSize: '18px', color: '#9fb0c6', margin: '0' }}>
          Start your paper trading journey with 11 AI-powered strategies
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gap: '32px',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          marginBottom: '60px',
        }}
      >
        <FeatureCard
          icon="📊"
          title="11 Trading Strategies"
          description="Access advanced algorithmic trading strategies optimized for different market conditions"
        />
        <FeatureCard
          icon="🎯"
          title="90%+ Win Rate Target"
          description="Backtested strategies designed to maximize consistent profitability"
        />
        <FeatureCard
          icon="📈"
          title="Paper Trading First"
          description="Risk-free simulation with real market data before deploying capital"
        />
        <FeatureCard
          icon="⚙️"
          title="Real-Time Monitoring"
          description="Live dashboard tracking all trades, P&L, and performance metrics"
        />
        <FeatureCard
          icon="🔐"
          title="Secure Accounts"
          description="Bank-grade security with encrypted authentication and data protection"
        />
        <FeatureCard
          icon="💬"
          title="AI Assistant Support"
          description="24/7 AI-powered guidance and strategy optimization"
        />
      </div>

      <button
        onClick={onNext}
        style={{
          padding: '14px 40px',
          background: '#5aa2ff',
          color: '#fff',
          border: 'none',
          borderRadius: '8px',
          fontSize: '16px',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onMouseOver={e => {
          (e.target as HTMLButtonElement).style.background = '#4a8edb';
          (e.target as HTMLButtonElement).style.transform = 'translateY(-2px)';
        }}
        onMouseOut={e => {
          (e.target as HTMLButtonElement).style.background = '#5aa2ff';
          (e.target as HTMLButtonElement).style.transform = 'translateY(0)';
        }}
      >
        Start Free Signup
      </button>

      <p style={{ color: '#9fb0c6', fontSize: '14px', marginTop: '40px' }}>
        No credit card required • Paper trading only • Full access for 30 days
      </p>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div
      style={{
        border: '1px solid #26364f',
        background: 'rgba(14,23,38,.6)',
        borderRadius: '12px',
        padding: '24px',
        textAlign: 'left',
        transition: 'all 0.2s',
        cursor: 'pointer',
      }}
      onMouseOver={e => {
        (e.currentTarget as HTMLDivElement).style.background =
          'rgba(90,162,255,.1)';
        (e.currentTarget as HTMLDivElement).style.borderColor = '#5aa2ff';
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-4px)';
      }}
      onMouseOut={e => {
        (e.currentTarget as HTMLDivElement).style.background =
          'rgba(14,23,38,.6)';
        (e.currentTarget as HTMLDivElement).style.borderColor = '#26364f';
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
      }}
    >
      <div style={{ fontSize: '32px', marginBottom: '12px' }}>{icon}</div>
      <h3
        style={{
          fontSize: '18px',
          fontWeight: 600,
          margin: '0 0 8px',
        }}
      >
        {title}
      </h3>
      <p style={{ color: '#9fb0c6', fontSize: '14px', lineHeight: '1.6', margin: '0' }}>
        {description}
      </p>
    </div>
  );
}

function SignupForm({
  formData,
  error,
  loading,
  onFieldChange,
  onSubmit,
  onBack,
}: {
  formData: SignupFormData;
  error: string | null;
  loading: boolean;
  onFieldChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onBack: () => void;
}) {
  return (
    <div
      style={{
        maxWidth: '500px',
        margin: '80px auto',
        border: '1px solid #26364f',
        background: 'rgba(14,23,38,.95)',
        borderRadius: '12px',
        padding: '48px 40px',
        boxShadow: '0 20px 40px rgba(0,0,0,.4)',
      }}
    >
      <h2
        style={{
          fontSize: '28px',
          fontWeight: 700,
          margin: '0 0 24px',
          textAlign: 'center',
        }}
      >
        Create Account
      </h2>

      {error && (
        <div
          style={{
            background: 'rgba(251, 113, 133, 0.1)',
            border: '1px solid #fb7185',
            borderRadius: '8px',
            padding: '12px 16px',
            marginBottom: '24px',
            color: '#fb7185',
            fontSize: '14px',
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={onSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              color: '#eef5ff',
            }}
          >
            Email Address
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={onFieldChange}
            placeholder="you@example.com"
            required
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(5, 9, 20, 0.5)',
              border: '1px solid #26364f',
              borderRadius: '8px',
              color: '#eef5ff',
              fontSize: '14px',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              color: '#eef5ff',
            }}
          >
            Password (min 8 characters)
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={onFieldChange}
            placeholder="••••••••"
            required
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(5, 9, 20, 0.5)',
              border: '1px solid #26364f',
              borderRadius: '8px',
              color: '#eef5ff',
              fontSize: '14px',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              color: '#eef5ff',
            }}
          >
            Starting Capital ($)
          </label>
          <input
            type="number"
            name="capitalAmount"
            value={formData.capitalAmount}
            onChange={onFieldChange}
            min="1000"
            step="500"
            required
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(5, 9, 20, 0.5)',
              border: '1px solid #26364f',
              borderRadius: '8px',
              color: '#eef5ff',
              fontSize: '14px',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
          <p style={{ color: '#9fb0c6', fontSize: '12px', margin: '6px 0 0' }}>
            Minimum $1,000. This is paper trading capital.
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: 600,
              marginBottom: '8px',
              color: '#eef5ff',
            }}
          >
            Risk Preference
          </label>
          <select
            name="riskPreference"
            value={formData.riskPreference}
            onChange={onFieldChange}
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(5, 9, 20, 0.5)',
              border: '1px solid #26364f',
              borderRadius: '8px',
              color: '#eef5ff',
              fontSize: '14px',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          >
            <option value="conservative">Conservative (1-2% per trade)</option>
            <option value="moderate">Moderate (2-4% per trade)</option>
            <option value="aggressive">Aggressive (4-6% per trade)</option>
          </select>
        </div>

        <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
          <input
            type="checkbox"
            name="agreeToTerms"
            checked={formData.agreeToTerms}
            onChange={onFieldChange}
            required
            style={{ marginTop: '2px' }}
          />
          <label style={{ fontSize: '13px', color: '#9fb0c6', lineHeight: '1.6' }}>
            I agree to the Terms of Service and Privacy Policy. I understand this is
            paper trading and not actual investing.
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: loading ? '#888' : '#5aa2ff',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            marginBottom: '12px',
          }}
          onMouseOver={e => {
            if (!loading) {
              (e.target as HTMLButtonElement).style.background = '#4a8edb';
            }
          }}
          onMouseOut={e => {
            if (!loading) {
              (e.target as HTMLButtonElement).style.background = '#5aa2ff';
            }
          }}
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>

        <button
          type="button"
          onClick={onBack}
          style={{
            width: '100%',
            padding: '14px',
            background: 'transparent',
            color: '#5aa2ff',
            border: '1px solid #26364f',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseOver={e => {
            (e.target as HTMLButtonElement).style.borderColor = '#5aa2ff';
            (e.target as HTMLButtonElement).style.background = 'rgba(90,162,255,.1)';
          }}
          onMouseOut={e => {
            (e.target as HTMLButtonElement).style.borderColor = '#26364f';
            (e.target as HTMLButtonElement).style.background = 'transparent';
          }}
        >
          Back
        </button>
      </form>

      <p style={{ color: '#9fb0c6', fontSize: '12px', marginTop: '24px', textAlign: 'center' }}>
        Already have an account?{' '}
        <a href="/sign-in" style={{ color: '#5aa2ff', textDecoration: 'underline' }}>
          Sign in
        </a>
      </p>
    </div>
  );
}

function SuccessSection() {
  return (
    <div
      style={{
        maxWidth: '500px',
        margin: '100px auto',
        textAlign: 'center',
        border: '1px solid #26364f',
        background: 'rgba(14,23,38,.95)',
        borderRadius: '12px',
        padding: '48px 40px',
        boxShadow: '0 20px 40px rgba(0,0,0,.4)',
      }}
    >
      <div style={{ fontSize: '64px', marginBottom: '24px' }}>✓</div>
      <h2 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 16px' }}>
        Account Created!
      </h2>
      <p style={{ color: '#9fb0c6', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
        Your trading account has been successfully created. A welcome email has been sent to
        your inbox. Please verify your email to continue.
      </p>
      <p style={{ color: '#9fb0c6', fontSize: '14px' }}>
        Redirecting to next step...
      </p>
    </div>
  );
}
