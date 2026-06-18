/**
 * Welcome email template for new ProfitEngine users
 */

interface WelcomeEmailProps {
  email: string;
  username: string;
  capitalAmount: number;
  riskPreference: string;
}

export function renderWelcomeEmail(props: WelcomeEmailProps): string {
  const riskLevelText = {
    conservative: 'Conservative (1-2% per trade)',
    moderate: 'Moderate (2-4% per trade)',
    aggressive: 'Aggressive (4-6% per trade)',
  }[props.riskPreference] || props.riskPreference;

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://app.profitengine.alreadyherellc.com';
  const dashboardUrl = `${baseUrl}/command-center`;

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body {
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          }
          .header {
            background: linear-gradient(135deg, #5aa2ff 0%, #4a8edb 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
          }
          .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 700;
          }
          .header p {
            margin: 8px 0 0;
            opacity: 0.9;
            font-size: 14px;
          }
          .content {
            padding: 40px 30px;
          }
          .greeting {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
          }
          .section {
            margin: 30px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #5aa2ff;
            border-radius: 4px;
          }
          .section h2 {
            margin: 0 0 12px;
            font-size: 16px;
            color: #333;
          }
          .section p {
            margin: 6px 0;
            color: #666;
            font-size: 14px;
          }
          .account-details {
            background-color: #f0f7ff;
            border: 1px solid #5aa2ff;
            border-radius: 6px;
            padding: 20px;
            margin: 30px 0;
          }
          .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(90, 162, 255, 0.2);
          }
          .detail-row:last-child {
            border-bottom: none;
          }
          .detail-label {
            font-weight: 600;
            color: #333;
          }
          .detail-value {
            color: #5aa2ff;
            font-weight: 600;
          }
          .cta-button {
            display: inline-block;
            background-color: #5aa2ff;
            color: white;
            padding: 14px 32px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
            text-align: center;
          }
          .cta-button:hover {
            background-color: #4a8edb;
          }
          .features {
            list-style: none;
            padding: 0;
            margin: 15px 0;
          }
          .features li {
            padding: 10px 0;
            color: #666;
            font-size: 14px;
          }
          .features li:before {
            content: "✓ ";
            color: #5aa2ff;
            font-weight: bold;
            margin-right: 8px;
          }
          .footer {
            background-color: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
          }
          .footer p {
            margin: 6px 0;
          }
          .divider {
            height: 1px;
            background-color: #eee;
            margin: 30px 0;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Welcome to PROFITENGINE</h1>
            <p>Your Paper Trading Journey Starts Now</p>
          </div>

          <div class="content">
            <div class="greeting">Hello ${props.username},</div>

            <p>
              Thank you for signing up for ProfitEngine! Your trading account has been successfully created
              and is now ready to deploy our AI-powered trading strategies.
            </p>

            <div class="account-details">
              <div class="detail-row">
                <span class="detail-label">Email:</span>
                <span class="detail-value">${props.email}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Starting Capital:</span>
                <span class="detail-value">$${props.capitalAmount.toLocaleString()}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Risk Preference:</span>
                <span class="detail-value">${riskLevelText}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Account Type:</span>
                <span class="detail-value">Paper Trading</span>
              </div>
            </div>

            <div class="section">
              <h2>What You Can Do Right Now</h2>
              <ul class="features">
                <li>Access 11 AI-powered trading strategies</li>
                <li>Monitor real-time trades and P&L in your dashboard</li>
                <li>Adjust risk settings and strategy allocation</li>
                <li>View detailed performance analytics</li>
                <li>Receive daily strategy performance reports</li>
              </ul>
            </div>

            <div style="text-align: center;">
              <a href="${dashboardUrl}" class="cta-button">
                Access Your Trading Dashboard
              </a>
            </div>

            <div class="section">
              <h2>Next Steps</h2>
              <p><strong>1. Verify Your Email</strong><br>
              Check your inbox for a verification email. Click the link to confirm your account.</p>
              <p><strong>2. Complete KYC (Optional)</strong><br>
              To unlock premium features and live trading, complete our quick identity verification process.</p>
              <p><strong>3. Monitor Your Strategies</strong><br>
              Log in to your dashboard to watch your algorithms trade in real-time with simulated capital.</p>
            </div>

            <div class="section">
              <h2>Important Notes</h2>
              <p>
                This is <strong>paper trading</strong> - no real money is invested. You're trading with simulated capital
                on real market data, allowing you to test strategies risk-free.
              </p>
              <p>
                You have full access for <strong>30 days</strong>. After that, you can upgrade to our premium plan
                to continue trading or transition to live trading (subject to verification).
              </p>
            </div>

            <div class="divider"></div>

            <p style="color: #666; font-size: 13px;">
              <strong>Questions or Need Help?</strong><br>
              Contact our support team at <a href="mailto:support@alreadyherellc.com" style="color: #5aa2ff;">support@alreadyherellc.com</a>
              or visit our <a href="https://profitengine.alreadyherellc.com" style="color: #5aa2ff;">help center</a>.
            </p>
          </div>

          <div class="footer">
            <p>
              <strong>ProfitEngine v5</strong><br>
              Advanced AI Trading System
            </p>
            <p>
              <a href="https://profitengine.alreadyherellc.com/terms" style="color: #5aa2ff;">Terms of Service</a> |
              <a href="https://profitengine.alreadyherellc.com/privacy" style="color: #5aa2ff;">Privacy Policy</a> |
              <a href="https://profitengine.alreadyherellc.com/disclaimer" style="color: #5aa2ff;">Disclaimer</a>
            </p>
            <p>
              This email was sent to ${props.email}. You can manage your email preferences in your account settings.
            </p>
            <p style="margin-top: 20px; color: #999;">
              Already Here LLC | ops@alreadyherellc.com<br>
              All rights reserved. ${new Date().getFullYear()}
            </p>
          </div>
        </div>
      </body>
    </html>
  `;
}
