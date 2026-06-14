import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { MongoClient } from "mongodb";

// Lazy-initialized so build-time evaluation with empty env vars doesn't throw
let _stripe: Stripe | null = null;
function getStripe(): Stripe {
  if (!_stripe) {
    const key = process.env.STRIPE_SECRET_KEY ?? "";
    if (!key) throw new Error("STRIPE_SECRET_KEY not set");
    _stripe = new Stripe(key, { apiVersion: "2026-05-27.dahlia" });
  }
  return _stripe;
}

const WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET ?? "";
const MONGO_URI = process.env.MONGODB_URL ?? process.env.MONGO_URL ?? "";

function logStripe(
  level: "info" | "warn" | "error",
  message: string,
  details: Record<string, unknown> = {}
) {
  console[level](`[stripe-webhook] ${JSON.stringify({ message, ...details })}`);
}

// Singleton client for warm Lambda reuse
let _client: MongoClient | null = null;
async function getDb() {
  if (!_client) {
    _client = new MongoClient(MONGO_URI, { serverSelectionTimeoutMS: 5000 });
    await _client.connect();
  }
  return _client.db();
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature") ?? "";

  if (!WEBHOOK_SECRET) {
    logStripe("error", "missing_webhook_secret");
    return NextResponse.json({ error: "webhook secret not configured" }, { status: 500 });
  }

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(body, sig, WEBHOOK_SECRET);
  } catch (err) {
    logStripe("error", "signature_verification_failed", {
      error: err instanceof Error ? err.message : String(err),
    });
    return NextResponse.json(
      { error: `webhook error: ${err instanceof Error ? err.message : String(err)}` },
      { status: 400 }
    );
  }

  logStripe("info", "event_received", { eventType: event.type, eventId: event.id });

  try {
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutCompleted(session);
    }
    // Additional event types can be handled here.
  } catch (err) {
    // Log but still return 200 - Stripe must not retry verified events.
    logStripe("error", "handler_error", {
      eventType: event.type,
      eventId: event.id,
      error: err instanceof Error ? err.message : String(err),
    });
  }

  return NextResponse.json({ received: true, event_type: event.type });
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  if (!MONGO_URI) {
    logStripe("warn", "mongo_missing_skip_db_update");
    return;
  }

  const db = await getDb();
  const now = new Date().toISOString();
  const sessionId = session.id;
  const paymentStatus = session.payment_status; // "paid" | "unpaid" | "no_payment_required"
  const metadata = (session.metadata ?? {}) as Record<string, string>;

  // Update payment_transactions
  await db.collection("payment_transactions").updateOne(
    { session_id: sessionId },
    {
      $set: {
        status: session.status ?? "complete",
        payment_status: paymentStatus,
        updated_at: now,
      },
    }
  );

  // Store raw event for audit
  await db.collection("stripe_events").insertOne({
    event_type: "checkout.session.completed",
    session_id: sessionId,
    payment_status: paymentStatus,
    metadata,
    received_at: now,
  });

  if (paymentStatus !== "paid") return;

  // Idempotent subscription grant
  const existing = await db.collection("subscriptions").findOne({ session_id: sessionId });
  if (existing) return;

  const tx = await db.collection("payment_transactions").findOne({ session_id: sessionId });
  const email = metadata.email || (session.customer_details?.email ?? "");
  const tier = metadata.tier || tx?.tier || "studio";
  const cadence = metadata.cadence || tx?.cadence || "month";
  const amount = session.amount_total ? session.amount_total / 100 : tx?.amount ?? 0;

  await db.collection("subscriptions").insertOne({
    session_id: sessionId,
    email,
    tier,
    cadence,
    amount_paid: amount,
    referral_code: metadata.referral_code || tx?.referral_code || null,
    status: "active",
    created_at: now,
  });

  logStripe("info", "subscription_granted", { tier, email, amount });
}
