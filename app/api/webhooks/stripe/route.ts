import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createPayout } from '@/lib/payouts.server';
import { getJobById } from '@/lib/jobs.server';
import {
  getClientByStripeAccount,
  updateTransaction,
  getTransaction,
} from '@/lib/client-db';
import { randomUUID } from 'crypto';

function getStripe() {
  const stripeKey = process.env.STRIPE_SECRET_KEY || process.env.STRIPE_API_KEY || '';
  if (!stripeKey) {
    throw new Error('STRIPE_SECRET_KEY or STRIPE_API_KEY not configured');
  }
  return new Stripe(stripeKey);
}

function getWebhookSecret() {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET || '';
  if (!webhookSecret) {
    throw new Error('STRIPE_WEBHOOK_SECRET not configured');
  }
  return webhookSecret;
}

/**
 * Route client webhook to their configured URL
 */
async function routeToClientWebhook(
  clientId: string,
  webhookUrl: string | null,
  event: Stripe.Event,
  stripeAccount: string | undefined
): Promise<{ success: boolean; responseCode?: number }> {
  if (!webhookUrl) {
    return { success: false };
  }

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Stripe-Signature': `t=${Math.floor(Date.now() / 1000)},v1=mock_signature_for_client`,
        'X-Client-ID': clientId,
      },
      body: JSON.stringify({
        ...event,
        client_id: clientId,
        stripe_account: stripeAccount,
      }),
    });

    console.log(
      `📤 Webhook routed to client ${clientId}: ${webhookUrl} - Status ${response.status}`
    );

    return {
      success: response.ok,
      responseCode: response.status,
    };
  } catch (error) {
    console.error(
      `❌ Failed to route webhook to client ${clientId}:`,
      error
    );
    return { success: false };
  }
}

export async function POST(request: NextRequest) {
  const stripe = getStripe();
  const webhookSecret = getWebhookSecret();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json(
      { error: 'Missing stripe-signature header' },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    const rawBody = await request.text();
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    console.error('Webhook signature verification failed:', error);
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 401 }
    );
  }

  // Handle different event types
  switch (event.type) {
    case 'charge.succeeded': {
      const charge = event.data.object as Stripe.Charge;
      const stripeAccount = (event as any).account; // Connected account ID

      console.log(`✅ Charge succeeded: ${charge.id}`);

      // ROUTE 1: Check if this is a multi-tenant client charge
      if (stripeAccount) {
        const client = await getClientByStripeAccount(stripeAccount);
        if (client) {
          console.log(
            `🎯 Routed charge to client ${client.id} (account: ${stripeAccount})`
          );

          // Calculate commission (YOUR revenue = 2.5% of charge)
          const yourCommission = Math.round(charge.amount * 0.025);
          console.log(
            `💰 Commission earned: $${(yourCommission / 100).toFixed(2)} (2.5% of $${(charge.amount / 100).toFixed(2)})`
          );

          // ROUTE 2: Send event to client's webhook
          if (client.webhook_url) {
            const webhookResult = await routeToClientWebhook(
              client.id,
              client.webhook_url,
              event,
              stripeAccount
            );

            // ROUTE 3: Update transaction with webhook result
            const metadata = charge.metadata || {};
            const transactionId = metadata.transaction_id || randomUUID();

            const updated = await updateTransaction(client.id, transactionId, {
              webhook_event_id: event.id,
              webhook_delivered: webhookResult.success,
              webhook_response_code: webhookResult.responseCode || null,
            });

            console.log(
              `📋 Transaction logged for client ${client.id}: ${transactionId}`
            );
          }

          return NextResponse.json(
            {
              ok: true,
              message: 'Charge routed to client',
              client_id: client.id,
              amount: charge.amount / 100,
            },
            { status: 200 }
          );
        }
      }

      // ROUTE 1 (legacy): Handle direct ProfitEngine job payments
      const jobId = charge.metadata?.jobId;
      const contractorId = charge.metadata?.contractorId;
      const contractorEmail = charge.metadata?.customerEmail;

      try {
        if (jobId) {
          const job = await getJobById(jobId);
          if (job && contractorId && contractorEmail) {
            const payoutAmount = job.pay * 0.7;
            await createPayout({
              jobId,
              contractorId,
              contractorEmail,
              contractorName: job.title,
              amount: payoutAmount,
            });
            console.log(`💳 Payout created: $${payoutAmount} to contractor ${contractorId}`);
          }
        }
      } catch (payoutError) {
        console.error('Failed to create payout:', payoutError);
      }

      return NextResponse.json(
        {
          ok: true,
          message: 'Charge succeeded',
          jobId: charge.metadata?.jobId,
          amount: charge.amount / 100,
        },
        { status: 200 }
      );
    }

    case 'charge.failed': {
      const charge = event.data.object as Stripe.Charge;
      const stripeAccount = (event as any).account;

      console.log(`❌ Charge failed: ${charge.id}`);

      // Route to client webhook if applicable
      if (stripeAccount) {
        const client = await getClientByStripeAccount(stripeAccount);
        if (client) {
          await routeToClientWebhook(client.id, client.webhook_url, event, stripeAccount);
        }
      }

      return NextResponse.json(
        {
          ok: true,
          message: 'Charge failed logged',
        },
        { status: 200 }
      );
    }

    case 'charge.refunded': {
      const charge = event.data.object as Stripe.Charge;
      const stripeAccount = (event as any).account;

      console.log(`↩️ Charge refunded: ${charge.id}`);

      // Route to client webhook if applicable
      if (stripeAccount) {
        const client = await getClientByStripeAccount(stripeAccount);
        if (client) {
          await routeToClientWebhook(client.id, client.webhook_url, event, stripeAccount);
        }
      }

      return NextResponse.json(
        {
          ok: true,
          message: 'Refund processed',
        },
        { status: 200 }
      );
    }

    case 'payment_intent.succeeded': {
      const paymentIntent = event.data.object as Stripe.PaymentIntent;
      console.log(`✅ Payment intent succeeded: ${paymentIntent.id}`);

      const jobId = paymentIntent.metadata?.jobId;
      const contractorId = paymentIntent.metadata?.contractorId;
      const contractorEmail = paymentIntent.metadata?.customerEmail;

      try {
        if (jobId) {
          const job = await getJobById(jobId);
          if (job && contractorId && contractorEmail) {
            const payoutAmount = job.pay * 0.7;
            await createPayout({
              jobId,
              contractorId,
              contractorEmail,
              contractorName: job.title,
              amount: payoutAmount,
            });
            console.log(`💳 Payout created: $${payoutAmount} to contractor ${contractorId}`);
          }
        }
      } catch (payoutError) {
        console.error('Failed to create payout:', payoutError);
      }

      return NextResponse.json(
        {
          ok: true,
          message: 'Payment succeeded',
          jobId: paymentIntent.metadata?.jobId,
          amount: paymentIntent.amount / 100,
        },
        { status: 200 }
      );
    }

    case 'payment_intent.payment_failed': {
      const paymentIntent = event.data.object as Stripe.PaymentIntent;
      console.log(`❌ Payment failed: ${paymentIntent.id}`);

      return NextResponse.json(
        {
          ok: true,
          message: 'Payment failed notification logged',
          jobId: paymentIntent.metadata?.jobId,
        },
        { status: 200 }
      );
    }

    case 'invoice.payment_succeeded': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log(`✅ Invoice paid: ${invoice.id}`);

      return NextResponse.json(
        {
          ok: true,
          message: 'Invoice payment succeeded',
        },
        { status: 200 }
      );
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log(`❌ Invoice payment failed: ${invoice.id}`);

      return NextResponse.json(
        {
          ok: true,
          message: 'Invoice payment failed logged',
        },
        { status: 200 }
      );
    }

    default:
      return NextResponse.json(
        { ok: true, message: `Unhandled event type: ${event.type}` },
        { status: 200 }
      );
  }
}
