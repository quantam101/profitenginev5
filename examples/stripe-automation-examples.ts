/**
 * STRIPE AUTOMATION - PRACTICAL EXAMPLES
 *
 * Real-world usage examples for common payment automation scenarios
 */

import {
  createOrUpdateCustomer,
  createSubscription,
  cancelSubscription,
  createPaymentIntent,
  recordRevenue,
  getRevenueReport,
  getMonthlyRecurringRevenue,
  getChurnRate,
  getCustomerLifetimeValue,
} from '@/lib/automation/stripe';

// ============================================================================
// EXAMPLE 1: Basic Customer Onboarding
// ============================================================================

export async function exampleCustomerOnboarding() {
  console.log('\n=== Customer Onboarding Example ===\n');

  try {
    // Create customer with metadata
    const customer = await createOrUpdateCustomer(
      'newuser@company.com',
      'Sarah Johnson',
      {
        source: 'organic_search',
        campaign: 'summer2024',
        tier: 'starter',
        region: 'US'
      }
    );

    console.log('✅ Customer created:');
    console.log(`   ID: ${customer.stripeCustomerId}`);
    console.log(`   Email: ${customer.email}`);
    console.log(`   Name: ${customer.name}`);
    console.log(`   Created: ${customer.createdAt}`);

    return customer;
  } catch (error) {
    console.error('❌ Customer onboarding failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 2: Freemium to Paid Conversion
// ============================================================================

export async function exampleFreemiumConversion(customerId: string) {
  console.log('\n=== Freemium to Paid Conversion Example ===\n');

  try {
    // Create monthly subscription
    const subscription = await createSubscription({
      stripeCustomerId: customerId,
      stripePriceId: 'price_monthly_pro', // Your actual Stripe price ID
      metadata: {
        plan: 'professional',
        previousTier: 'freemium',
        conversionDate: new Date().toISOString().split('T')[0],
        source: 'self_serve'
      }
    });

    console.log('✅ Subscription created:');
    console.log(`   Subscription ID: ${subscription.stripeSubscriptionId}`);
    console.log(`   Status: ${subscription.status}`);
    console.log(`   Amount: $${subscription.amount}/${subscription.interval}`);
    console.log(`   Period: ${subscription.currentPeriodStart} → ${subscription.currentPeriodEnd}`);

    // Record this as a revenue event
    await recordRevenue({
      id: `conversion-${Date.now()}`,
      stripeSubscriptionId: subscription.stripeSubscriptionId,
      type: 'subscription',
      amount: subscription.amount,
      currency: subscription.currency,
      status: 'pending',
      customerEmail: 'newuser@company.com',
      description: 'Freemium upgrade to Professional plan',
      metadata: {
        conversionType: 'freemium_paid',
        plan: 'professional'
      },
      createdAt: new Date().toISOString(),
      recordedAt: new Date().toISOString()
    });

    console.log('✅ Conversion revenue recorded');

    return subscription;
  } catch (error) {
    console.error('❌ Freemium conversion failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 3: Sponsored Content Payment Processing
// ============================================================================

export async function exampleSponsoredContentPayment() {
  console.log('\n=== Sponsored Content Payment Example ===\n');

  try {
    // Create sponsor customer
    const sponsor = await createOrUpdateCustomer(
      'sponsor@techcorp.com',
      'TechCorp Inc.',
      {
        type: 'sponsor',
        company: 'TechCorp',
        tier: 'platinum',
        industry: 'software'
      }
    );

    console.log('✅ Sponsor customer created:', sponsor.stripeCustomerId);

    // Create sponsorship payment
    const payment = await createPaymentIntent({
      stripeCustomerId: sponsor.stripeCustomerId,
      amount: 7500,
      currency: 'usd',
      type: 'sponsorship',
      description: 'Q2 2024 Newsletter Sponsorship - 4 weeks',
      metadata: {
        sponsor: 'TechCorp Inc.',
        sponsorshipType: 'exclusive',
        duration: '4_weeks',
        quarter: 'Q2-2024',
        expectedViews: '50000'
      },
      receiptEmail: sponsor.email
    });

    console.log('✅ Sponsorship payment intent created:');
    console.log(`   Payment ID: ${payment.stripePaymentIntentId}`);
    console.log(`   Amount: $${payment.amount}`);
    console.log(`   Status: ${payment.status}`);

    // Record sponsorship revenue
    await recordRevenue({
      id: `sponsorship-q2-${Date.now()}`,
      stripePaymentIntentId: payment.stripePaymentIntentId,
      type: 'sponsorship',
      amount: 7500,
      currency: 'usd',
      status: 'completed',
      customerEmail: sponsor.email,
      customerName: sponsor.name,
      description: 'Q2 2024 Exclusive Newsletter Sponsorship',
      metadata: {
        sponsor: 'TechCorp Inc.',
        quarter: 'Q2-2024',
        duration: '4_weeks'
      },
      createdAt: new Date().toISOString(),
      recordedAt: new Date().toISOString()
    });

    console.log('✅ Sponsorship revenue recorded');

    return payment;
  } catch (error) {
    console.error('❌ Sponsorship payment failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 4: Churn Management - Downgrade Instead of Cancel
// ============================================================================

export async function exampleChurnRecovery(subscriptionId: string) {
  console.log('\n=== Churn Recovery Example ===\n');

  try {
    // Instead of canceling, downgrade to cheaper tier
    const downgraded = await (
      await import('@/lib/automation/stripe')
    ).updateSubscription(subscriptionId, {
      stripePriceId: 'price_monthly_starter', // Cheaper tier
      metadata: {
        action: 'downgrade',
        reason: 'churn_recovery',
        downgradeDate: new Date().toISOString().split('T')[0]
      }
    });

    console.log('✅ Subscription downgraded to prevent churn:');
    console.log(`   Subscription ID: ${downgraded.stripeSubscriptionId}`);
    console.log(`   New amount: $${downgraded.amount}/${downgraded.interval}`);

    // Record the change
    await recordRevenue({
      id: `churn-recovery-${Date.now()}`,
      stripeSubscriptionId: downgraded.stripeSubscriptionId,
      type: 'subscription',
      amount: downgraded.amount,
      currency: downgraded.currency,
      status: 'completed',
      customerEmail: 'customer@example.com',
      description: 'Subscription downgrade (churn recovery)',
      metadata: {
        action: 'downgrade',
        amountChange: `was_pro_now_starter`,
        recovery: true
      },
      createdAt: new Date().toISOString(),
      recordedAt: new Date().toISOString()
    });

    return downgraded;
  } catch (error) {
    console.error('❌ Churn recovery failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 5: One-Time Payment with Add-ons
// ============================================================================

export async function exampleAddOnPurchase(customerId: string) {
  console.log('\n=== Add-On Purchase Example ===\n');

  try {
    // Create one-time payment for add-on
    const addOnPayment = await createPaymentIntent({
      stripeCustomerId: customerId,
      amount: 299.99,
      currency: 'usd',
      type: 'one_time',
      description: 'Advanced Analytics Module - Annual License',
      metadata: {
        addonName: 'advanced_analytics',
        licenseType: 'annual',
        validUntil: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
        features: ['custom_dashboards', 'api_access', 'priority_support']
      },
      receiptEmail: 'customer@example.com'
    });

    console.log('✅ Add-on payment created:');
    console.log(`   Payment ID: ${addOnPayment.stripePaymentIntentId}`);
    console.log(`   Amount: $${addOnPayment.amount}`);

    // Record as one-time revenue
    await recordRevenue({
      id: `addon-${Date.now()}`,
      stripePaymentIntentId: addOnPayment.stripePaymentIntentId,
      type: 'payment',
      amount: 299.99,
      currency: 'usd',
      status: 'pending',
      customerEmail: 'customer@example.com',
      description: 'Advanced Analytics Module - Annual',
      metadata: {
        addon: 'advanced_analytics',
        licenseType: 'annual'
      },
      createdAt: new Date().toISOString(),
      recordedAt: new Date().toISOString()
    });

    return addOnPayment;
  } catch (error) {
    console.error('❌ Add-on purchase failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 6: Daily Revenue Dashboard
// ============================================================================

export async function exampleDailyRevenueDashboard() {
  console.log('\n=== Daily Revenue Dashboard Example ===\n');

  try {
    // Get today's revenue breakdown
    const todayReport = await getRevenueReport();

    console.log('📊 Today\'s Revenue Report');
    console.log(`   Date: ${todayReport.date}`);
    console.log(`   Total Revenue: $${todayReport.total.toFixed(2)}`);
    console.log(`   Transaction Count: ${todayReport.count}`);
    console.log('\n   Revenue by Type:');

    for (const [type, amount] of Object.entries(todayReport.byType)) {
      const percentage = todayReport.total > 0
        ? ((amount / todayReport.total) * 100).toFixed(1)
        : '0.0';
      console.log(`     • ${type}: $${amount.toFixed(2)} (${percentage}%)`);
    }

    // Get MRR
    const mrr = await getMonthlyRecurringRevenue();
    console.log(`\n   Monthly Recurring Revenue (MRR): $${mrr.toFixed(2)}`);

    // Get churn
    const churnRate = await getChurnRate(30);
    console.log(`   30-Day Churn Rate: ${churnRate.toFixed(2)}%`);

    return { todayReport, mrr, churnRate };
  } catch (error) {
    console.error('❌ Dashboard failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 7: Customer Health Score Calculation
// ============================================================================

export async function exampleCustomerHealthScore(customerId: string) {
  console.log('\n=== Customer Health Score Example ===\n');

  try {
    // Get customer LTV
    const ltv = await getCustomerLifetimeValue(customerId);

    // Get churn rate
    const churnRate = await getChurnRate(30);

    // Calculate health score (0-100)
    let healthScore = 50; // Base score

    // LTV factor (max 30 points)
    if (ltv > 1000) healthScore += 30;
    else if (ltv > 500) healthScore += 20;
    else if (ltv > 100) healthScore += 10;

    // Churn factor (max 20 points penalty)
    healthScore -= (churnRate / 5); // Convert churn % to point deduction

    // Cap at 100
    healthScore = Math.min(100, Math.max(0, healthScore));

    console.log('💯 Customer Health Score:');
    console.log(`   Customer ID: ${customerId}`);
    console.log(`   Health Score: ${healthScore.toFixed(1)}/100`);
    console.log(`   Lifetime Value: $${ltv.toFixed(2)}`);
    console.log(`   30-Day Churn Rate: ${churnRate.toFixed(2)}%`);

    // Health status
    let status = 'At Risk';
    if (healthScore >= 75) status = 'Excellent';
    else if (healthScore >= 50) status = 'Good';
    else if (healthScore >= 25) status = 'Concerning';

    console.log(`   Status: ${status}`);

    // Recommendations
    console.log('\n   Recommendations:');
    if (ltv < 100) {
      console.log('   • Offer onboarding support to increase engagement');
    }
    if (churnRate > 5) {
      console.log('   • Launch churn recovery campaign');
    }
    if (healthScore < 50) {
      console.log('   • Schedule customer check-in');
    }

    return { healthScore, status, ltv, churnRate };
  } catch (error) {
    console.error('❌ Health score calculation failed:', error);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 8: Subscription Lifecycle Tracking
// ============================================================================

export async function exampleSubscriptionLifecycleTracking(
  customerId: string,
  startPriceId: string,
  upgradePriceId: string
) {
  console.log('\n=== Subscription Lifecycle Tracking Example ===\n');

  try {
    // 1. Create initial subscription
    console.log('📅 Step 1: Create initial subscription');
    const initial = await createSubscription({
      stripeCustomerId: customerId,
      stripePriceId: startPriceId,
      trialDays: 7,
      metadata: {
        lifecycle: 'created',
        phase: 'trial',
        createdAt: new Date().toISOString()
      }
    });
    console.log(`   Created: ${initial.stripeSubscriptionId}`);

    // Simulate trial period...
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 2. Trial converted to paid
    console.log('\n📅 Step 2: Trial converted to paid');
    const converted = await (
      await import('@/lib/automation/stripe')
    ).updateSubscription(initial.stripeSubscriptionId, {
      metadata: {
        lifecycle: 'trial_converted',
        phase: 'active',
        convertedAt: new Date().toISOString()
      }
    });
    console.log(`   Converted: ${converted.stripeSubscriptionId}`);

    // 3. Upgrade to higher tier
    console.log('\n📅 Step 3: Upgrade to higher tier');
    const upgraded = await (
      await import('@/lib/automation/stripe')
    ).updateSubscription(converted.stripeSubscriptionId, {
      stripePriceId: upgradePriceId,
      metadata: {
        lifecycle: 'upgraded',
        phase: 'premium',
        upgradedAt: new Date().toISOString(),
        previousAmount: converted.amount
      }
    });
    console.log(`   Upgraded: ${upgraded.stripeSubscriptionId}`);
    console.log(`   New amount: $${upgraded.amount}/${upgraded.interval}`);

    console.log('\n✅ Subscription lifecycle complete');

    return {
      initial,
      converted,
      upgraded
    };
  } catch (error) {
    console.error('❌ Lifecycle tracking failed:', error);
    throw error;
  }
}

// ============================================================================
// MAIN EXECUTION (when run directly)
// ============================================================================

if (require.main === module) {
  (async () => {
    try {
      console.log('🚀 Stripe Automation Examples');
      console.log('==============================\n');

      // Run examples
      await exampleCustomerOnboarding();
      // await exampleDailyRevenueDashboard();
      // await exampleSponsoredContentPayment();

      console.log('\n✅ Examples completed successfully');
    } catch (error) {
      console.error('\n❌ Examples failed:', error);
      process.exit(1);
    }
  })();
}

export default {
  exampleCustomerOnboarding,
  exampleFreemiumConversion,
  exampleSponsoredContentPayment,
  exampleChurnRecovery,
  exampleAddOnPurchase,
  exampleDailyRevenueDashboard,
  exampleCustomerHealthScore,
  exampleSubscriptionLifecycleTracking
};
