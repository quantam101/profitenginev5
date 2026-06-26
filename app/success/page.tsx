'use client';

export default function SuccessPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui', padding: '40px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', maxWidth: '600px' }}>
        <div style={{ fontSize: '60px', marginBottom: '24px' }}>✅</div>
        <h1 style={{ fontSize: '36px', marginBottom: '16px' }}>Payment Successful!</h1>
        <p style={{ fontSize: '18px', color: '#9fb0c6', marginBottom: '32px' }}>
          Thank you for your purchase. Your tool is now ready to use.
        </p>
        <div style={{ padding: '24px', background: 'rgba(31, 41, 55, 0.5)', borderRadius: '8px', marginBottom: '32px', textAlign: 'left' }}>
          <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#9fb0c6' }}>Order Details:</p>
          <p style={{ margin: '0', fontSize: '16px', fontWeight: 700 }}>Check your email for access details</p>
        </div>
        <a
          href="/marketing"
          style={{
            display: 'inline-block',
            padding: '14px 32px',
            background: '#00ff00',
            color: '#000',
            textDecoration: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '16px',
          }}
        >
          Back to Tools
        </a>
      </div>
    </div>
  );
}
