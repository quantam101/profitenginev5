'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface KYCFormData {
  firstName: string;
  lastName: string;
  age: number;
  tradingExperience: 'beginner' | 'intermediate' | 'advanced';
  riskTolerance: 'low' | 'moderate' | 'high';
  investmentGoals: string;
  agreeToTerms: boolean;
}

export default function KYCPage() {
  const router = useRouter();
  const [step, setStep] = useState<'intro' | 'form' | 'success'>('intro');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<KYCFormData>({
    firstName: '',
    lastName: '',
    age: 25,
    tradingExperience: 'beginner',
    riskTolerance: 'moderate',
    investmentGoals: '',
    agreeToTerms: false,
  });

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken');
    if (!token) {
      router.push('/trading-signup');
    }
  }, [router]);

  const handleFieldChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
      ...(name === 'age' && { age: parseInt(value) }),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validation
      if (!formData.firstName || !formData.lastName) {
        throw new Error('First and last name are required');
      }

      if (formData.age < 18) {
        throw new Error('You must be at least 18 years old');
      }

      if (!formData.investmentGoals.trim()) {
        throw new Error('Please describe your investment goals');
      }

      if (!formData.agreeToTerms) {
        throw new Error('You must agree to the terms');
      }

      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch('/api/kyc/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'KYC submission failed');
      }

      setStep('success');

      // Redirect after 3 seconds
      setTimeout(() => {
        router.push('/command-center');
      }, 3000);
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
      {step === 'intro' && <KYCIntroSection onNext={() => setStep('form')} />}
      {step === 'form' && (
        <KYCForm
          formData={formData}
          error={error}
          loading={loading}
          onFieldChange={handleFieldChange}
          onSubmit={handleSubmit}
          onBack={() => setStep('intro')}
        />
      )}
      {step === 'success' && <SuccessSection />}
    </main>
  );
}

function KYCIntroSection({ onNext }: { onNext: () => void }) {
  return (
    <div
      style={{
        maxWidth: '800px',
        margin: '0 auto',
        paddingTop: '60px',
        paddingBottom: '60px',
      }}
    >
      <div style={{ marginBottom: '60px', textAlign: 'center' }}>
        <h1
          style={{
            fontSize: '36px',
            fontWeight: 700,
            margin: '0 0 16px',
            letterSpacing: '-1px',
          }}
        >
          Complete Your Identity Verification
        </h1>
        <p style={{ fontSize: '16px', color: '#9fb0c6', margin: '0' }}>
          Know Your Customer (KYC) verification unlocks premium features
        </p>
      </div>

      <div
        style={{
          border: '1px solid #26364f',
          background: 'rgba(14,23,38,.6)',
          borderRadius: '12px',
          padding: '40px',
          marginBottom: '40px',
        }}
      >
        <h2 style={{ marginTop: 0 }}>Why We Need This Information</h2>
        <ul style={{ lineHeight: '1.8', color: '#9fb0c6' }}>
          <li>Regulatory compliance (SEC/FINRA requirements)</li>
          <li>Prevent fraud and money laundering</li>
          <li>Customize trading strategies to your profile</li>
          <li>Unlock live trading and higher limits</li>
          <li>Provide better customer support</li>
        </ul>
      </div>

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '40px' }}>
        <InfoCard
          number="1"
          title="Basic Info"
          description="Provide your name and age"
        />
        <InfoCard
          number="2"
          title="Experience"
          description="Tell us about your trading background"
        />
        <InfoCard
          number="3"
          title="Goals"
          description="Share your investment objectives"
        />
        <InfoCard
          number="4"
          title="Verification"
          description="We'll process in 5-10 minutes"
        />
      </div>

      <button
        onClick={onNext}
        style={{
          display: 'block',
          margin: '0 auto',
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
        Start KYC Verification
      </button>

      <p style={{ color: '#9fb0c6', fontSize: '14px', marginTop: '40px', textAlign: 'center' }}>
        Takes approximately 5-10 minutes • Information is encrypted and secure
      </p>
    </div>
  );
}

function InfoCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div
      style={{
        border: '1px solid #26364f',
        background: 'rgba(14,23,38,.4)',
        borderRadius: '8px',
        padding: '20px',
      }}
    >
      <div
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: '#5aa2ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          fontWeight: 700,
          marginBottom: '12px',
        }}
      >
        {number}
      </div>
      <h3 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: 600 }}>{title}</h3>
      <p style={{ margin: 0, fontSize: '13px', color: '#9fb0c6' }}>{description}</p>
    </div>
  );
}

function KYCForm({
  formData,
  error,
  loading,
  onFieldChange,
  onSubmit,
  onBack,
}: {
  formData: KYCFormData;
  error: string | null;
  loading: boolean;
  onFieldChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onBack: () => void;
}) {
  return (
    <div
      style={{
        maxWidth: '600px',
        margin: '60px auto',
        border: '1px solid #26364f',
        background: 'rgba(14,23,38,.95)',
        borderRadius: '12px',
        padding: '48px 40px',
        boxShadow: '0 20px 40px rgba(0,0,0,.4)',
      }}
    >
      <h2 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 24px', textAlign: 'center' }}>
        Identity Verification
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
        <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <label style={labelStyle}>First Name</label>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={onFieldChange}
              required
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Last Name</label>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={onFieldChange}
              required
              style={inputStyle}
            />
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <label style={labelStyle}>Age</label>
          <input
            type="number"
            name="age"
            value={formData.age}
            onChange={onFieldChange}
            min="18"
            max="120"
            required
            style={inputStyle}
          />
          <p style={{ color: '#9fb0c6', fontSize: '12px', margin: '6px 0 0' }}>
            Must be 18 or older
          </p>
        </div>

        <div style={{ marginTop: '20px' }}>
          <label style={labelStyle}>Trading Experience Level</label>
          <select name="tradingExperience" value={formData.tradingExperience} onChange={onFieldChange} style={inputStyle}>
            <option value="beginner">Beginner - Never traded before</option>
            <option value="intermediate">Intermediate - Less than 3 years</option>
            <option value="advanced">Advanced - 3+ years experience</option>
          </select>
        </div>

        <div style={{ marginTop: '20px' }}>
          <label style={labelStyle}>Risk Tolerance</label>
          <select name="riskTolerance" value={formData.riskTolerance} onChange={onFieldChange} style={inputStyle}>
            <option value="low">Low - Prefer steady, safe returns</option>
            <option value="moderate">Moderate - Balance growth and safety</option>
            <option value="high">High - Seek maximum growth</option>
          </select>
        </div>

        <div style={{ marginTop: '20px' }}>
          <label style={labelStyle}>Investment Goals</label>
          <textarea
            name="investmentGoals"
            value={formData.investmentGoals}
            onChange={onFieldChange}
            placeholder="e.g., Generate passive income, learn trading strategies, test algorithms..."
            required
            rows={4}
            style={{
              ...inputStyle,
              resize: 'vertical',
              fontFamily: 'inherit',
            } as React.CSSProperties}
          />
        </div>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          <input
            type="checkbox"
            name="agreeToTerms"
            checked={formData.agreeToTerms}
            onChange={onFieldChange}
            required
            style={{ marginTop: '2px' }}
          />
          <label style={{ fontSize: '13px', color: '#9fb0c6', lineHeight: '1.6' }}>
            I confirm that all information provided is accurate and complete. I understand
            that providing false information may result in account termination.
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
            marginTop: '24px',
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
          {loading ? 'Processing...' : 'Submit Verification'}
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
        Verification Submitted!
      </h2>
      <p style={{ color: '#9fb0c6', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
        Your KYC information has been received. We&apos;ll review your submission within 24 hours.
      </p>
      <p style={{ color: '#9fb0c6', fontSize: '14px', marginBottom: '24px' }}>
        Check your email for status updates and next steps.
      </p>
      <p style={{ color: '#9fb0c6', fontSize: '14px' }}>
        Redirecting to your dashboard...
      </p>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '14px',
  fontWeight: 600,
  marginBottom: '8px',
  color: '#eef5ff',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 16px',
  background: 'rgba(5, 9, 20, 0.5)',
  border: '1px solid #26364f',
  borderRadius: '8px',
  color: '#eef5ff',
  fontSize: '14px',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
};
