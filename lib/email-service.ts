import nodemailer from 'nodemailer';
import { renderWelcomeEmail } from './emails/welcome';

interface EmailOptions {
  email: string;
  username: string;
  capitalAmount: number;
  riskPreference: string;
}

/**
 * Initialize email transporter
 * Uses SMTP credentials from environment variables
 */
function getTransporter() {
  if (process.env.SMTP_HOST && process.env.SMTP_PORT) {
    // Use custom SMTP server
    return nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: parseInt(process.env.SMTP_PORT),
      secure: process.env.SMTP_SECURE === 'true',
      auth: process.env.SMTP_USER && process.env.SMTP_PASSWORD ? {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASSWORD,
      } : undefined,
    });
  }

  if (process.env.SENDGRID_API_KEY) {
    // Use SendGrid
    return nodemailer.createTransport({
      host: 'smtp.sendgrid.net',
      port: 587,
      auth: {
        user: 'apikey',
        pass: process.env.SENDGRID_API_KEY,
      },
    });
  }

  if (process.env.GMAIL_APP_PASSWORD && process.env.GMAIL_USER) {
    // Use Gmail
    return nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.GMAIL_USER,
        pass: process.env.GMAIL_APP_PASSWORD,
      },
    });
  }

  // Development/test mode - return a mock transporter
  return nodemailer.createTransport({
    host: 'smtp.ethereal.email',
    port: 587,
    auth: {
      user: process.env.ETHEREAL_USER || 'test@ethereal.email',
      pass: process.env.ETHEREAL_PASSWORD || 'test-password',
    },
  });
}

/**
 * Send welcome email to new signup
 */
export async function sendWelcomeEmail(options: EmailOptions): Promise<void> {
  const transporter = getTransporter();

  const html = renderWelcomeEmail(options);

  const mailOptions = {
    from: process.env.EMAIL_FROM || 'noreply@profitengine.alreadyherellc.com',
    to: options.email,
    subject: 'Welcome to ProfitEngine - Your Trading Account is Ready',
    html,
    replyTo: process.env.EMAIL_REPLY_TO || 'support@alreadyherellc.com',
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('Welcome email sent:', info.messageId);
  } catch (error) {
    console.error('Failed to send welcome email:', error);
    throw new Error(`Failed to send welcome email: ${error}`);
  }
}

/**
 * Send KYC verification email
 */
export async function sendKYCVerificationEmail(
  email: string,
  verificationLink: string
): Promise<void> {
  const transporter = getTransporter();

  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #5aa2ff;">Complete Your Identity Verification</h1>
      <p>Hi there,</p>
      <p>To upgrade from paper trading and access additional features, we need to verify your identity.</p>
      <p style="margin: 30px 0;">
        <a href="${verificationLink}" style="background-color: #5aa2ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
          Complete KYC Verification
        </a>
      </p>
      <p>This link expires in 24 hours.</p>
      <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
      <p style="color: #666; font-size: 12px;">ProfitEngine Trading System</p>
    </div>
  `;

  const mailOptions = {
    from: process.env.EMAIL_FROM || 'noreply@profitengine.alreadyherellc.com',
    to: email,
    subject: 'Complete Your Identity Verification - ProfitEngine',
    html,
    replyTo: process.env.EMAIL_REPLY_TO || 'support@alreadyherellc.com',
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('KYC verification email sent:', info.messageId);
  } catch (error) {
    console.error('Failed to send KYC verification email:', error);
    throw new Error(`Failed to send KYC email: ${error}`);
  }
}

/**
 * Send account verification email
 */
export async function sendEmailVerification(
  email: string,
  verificationLink: string
): Promise<void> {
  const transporter = getTransporter();

  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #5aa2ff;">Verify Your Email Address</h1>
      <p>Hi there,</p>
      <p>Thank you for signing up! Please verify your email address to activate your trading account.</p>
      <p style="margin: 30px 0;">
        <a href="${verificationLink}" style="background-color: #5aa2ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
          Verify Email Address
        </a>
      </p>
      <p>This link expires in 24 hours.</p>
      <p style="color: #666; font-size: 12px;">If you didn't sign up for this account, please ignore this email.</p>
      <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
      <p style="color: #666; font-size: 12px;">ProfitEngine Trading System</p>
    </div>
  `;

  const mailOptions = {
    from: process.env.EMAIL_FROM || 'noreply@profitengine.alreadyherellc.com',
    to: email,
    subject: 'Verify Your Email - ProfitEngine',
    html,
    replyTo: process.env.EMAIL_REPLY_TO || 'support@alreadyherellc.com',
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('Email verification sent:', info.messageId);
  } catch (error) {
    console.error('Failed to send email verification:', error);
    throw new Error(`Failed to send verification email: ${error}`);
  }
}

/**
 * Send trading started notification email
 */
export async function sendTradingStartedEmail(email: string, username: string): Promise<void> {
  const transporter = getTransporter();

  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #5aa2ff;">Your Paper Trading Has Started!</h1>
      <p>Hi ${username},</p>
      <p>Great news! Your paper trading account is now active and your strategies have begun executing.</p>
      <h2 style="color: #333;">What's Next?</h2>
      <ul style="line-height: 1.8;">
        <li>Monitor your trades in the Dashboard</li>
        <li>Review strategy performance daily</li>
        <li>Adjust risk settings if needed</li>
        <li>Reach out if you have questions</li>
      </ul>
      <p style="margin: 30px 0;">
        <a href="https://app.profitengine.alreadyherellc.com/command-center" style="background-color: #5aa2ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
          View Your Dashboard
        </a>
      </p>
      <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
      <p style="color: #666; font-size: 12px;">ProfitEngine Trading System</p>
    </div>
  `;

  const mailOptions = {
    from: process.env.EMAIL_FROM || 'noreply@profitengine.alreadyherellc.com',
    to: email,
    subject: 'Paper Trading Started - ProfitEngine',
    html,
    replyTo: process.env.EMAIL_REPLY_TO || 'support@alreadyherellc.com',
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('Trading started email sent:', info.messageId);
  } catch (error) {
    console.error('Failed to send trading started email:', error);
    throw new Error(`Failed to send trading started email: ${error}`);
  }
}
