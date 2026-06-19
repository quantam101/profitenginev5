/**
 * Conversion Tracking for Landing Page Generator
 * Tracks which sections drive signups and conversions
 *
 * Usage:
 *   trackConversion('hero', 'cta_click')
 *   trackConversion('social_proof', 'signup')
 *   trackConversion('pricing', 'tier_select', 'pro')
 *   trackConversion('faq', 'link_click', 'docs')
 */

interface ConversionEvent {
  timestamp: string;
  section: string;
  action: string;
  metadata?: Record<string, any>;
  sessionId?: string;
  userId?: string;
}

interface ConversionMetrics {
  section: string;
  clicks: number;
  signups: number;
  conversion_rate: number;
  revenue_attributed?: number;
}

/**
 * Track conversion event to analytics service
 */
export async function trackConversion(
  section: string,
  action: string,
  metadata?: Record<string, any>
): Promise<void> {
  try {
    // Get or create session ID
    let sessionId = sessionStorage.getItem('landing_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('landing_session_id', sessionId);
    }

    const event: ConversionEvent = {
      timestamp: new Date().toISOString(),
      section,
      action,
      sessionId,
      metadata,
    };

    // Send to analytics endpoint
    await fetch('/api/conversions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
      keepalive: true,
    }).catch(() => {
      // Fail silently - don't break user experience
    });

    // Also track in browser console for debugging
    console.log(`[conversion] ${section}::${action}`, metadata);
  } catch (err) {
    // Fail silently
    console.warn('Conversion tracking failed:', err);
  }
}

/**
 * Track CTA click with UTM params
 */
export function trackCtaClick(section: string, cta_text: string): void {
  trackConversion(section, 'cta_click', { cta_text });

  // Add UTM params to any links
  const utm = `?utm_source=landing&utm_medium=organic&utm_campaign=${section}&utm_content=${cta_text.replace(/\s/g, '_')}`;
  console.log(`[utm] ${utm}`);
}

/**
 * Track signup conversion
 */
export function trackSignup(source_section: string, email?: string): void {
  trackConversion(source_section, 'signup', {
    email: email ? 'provided' : 'not_provided',
  });
}

/**
 * Track pricing tier selection
 */
export function trackTierSelected(tier: string, price: number): void {
  trackConversion('pricing', 'tier_select', { tier, price });
}

/**
 * Track FAQ expansion (indicates interest)
 */
export function trackFaqOpen(question: string): void {
  trackConversion('faq', 'expand_question', { question });
}

/**
 * Track metric view (indicates engagement)
 */
export function trackMetricView(metric_name: string, metric_value: string): void {
  trackConversion('hero', 'metric_view', { metric_name, metric_value });
}

/**
 * Track social proof card interaction
 */
export function trackPerformerView(rank: number, tier: string): void {
  trackConversion('social_proof', 'performer_view', { rank, tier });
}

/**
 * Track performance chart interaction
 */
export function trackChartInteraction(chart_type: string, interaction: string): void {
  trackConversion('dashboard', 'chart_interaction', { chart_type, interaction });
}

/**
 * Track link click from FAQ or other sections
 */
export function trackLinkClick(section: string, link_text: string, url: string): void {
  trackConversion(section, 'link_click', { link_text, url });
}

/**
 * Track page scroll depth
 */
export function trackScrollDepth(percentage: number): void {
  if (percentage === 25 || percentage === 50 || percentage === 75 || percentage === 100) {
    trackConversion('page', 'scroll_depth', { percentage });
  }
}

/**
 * Get conversion analytics for a specific section
 */
export async function getConversionMetrics(section?: string): Promise<ConversionMetrics[]> {
  try {
    const url = section ? `/api/conversions/metrics?section=${section}` : '/api/conversions/metrics';
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    console.error('Failed to fetch conversion metrics:', err);
    return [];
  }
}

/**
 * Initialize page-level tracking
 */
export function initializeTracking(): void {
  // Track scroll depth
  let maxScroll = 0;

  window.addEventListener('scroll', () => {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.scrollY;

    const scrollPercent = Math.round((scrollTop + windowHeight) / documentHeight * 100);

    if (scrollPercent > maxScroll) {
      maxScroll = scrollPercent;
      trackScrollDepth(scrollPercent);
    }
  });

  // Track page visibility (when user switches tabs)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      trackConversion('page', 'tab_hidden');
    } else {
      trackConversion('page', 'tab_visible');
    }
  });

  // Track unload (when user leaves page)
  window.addEventListener('beforeunload', () => {
    trackConversion('page', 'unload', { time_spent_ms: performance.now() });
  });

  console.log('[tracking] Initialized page-level conversion tracking');
}

/**
 * Create UTM builder for links
 */
export class UTMBuilder {
  private params: Record<string, string> = {};

  constructor(
    utm_source: string,
    utm_medium: string,
    utm_campaign: string
  ) {
    this.params.utm_source = utm_source;
    this.params.utm_medium = utm_medium;
    this.params.utm_campaign = utm_campaign;
  }

  withContent(utm_content: string): this {
    this.params.utm_content = utm_content;
    return this;
  }

  withTerm(utm_term: string): this {
    this.params.utm_term = utm_term;
    return this;
  }

  build(base_url: string): string {
    const params = new URLSearchParams(this.params);
    const separator = base_url.includes('?') ? '&' : '?';
    return `${base_url}${separator}${params.toString()}`;
  }
}

/**
 * Analytics dashboard component helpers
 */
export interface SectionMetrics {
  section: string;
  total_views: number;
  total_clicks: number;
  total_conversions: number;
  click_through_rate: number;
  conversion_rate: number;
  conversion_value?: number;
}

export async function getSectionMetrics(): Promise<SectionMetrics[]> {
  try {
    const response = await fetch('/api/conversions/sections');

    if (!response.ok) {
      throw new Error(`Failed to fetch section metrics: ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    console.error('Failed to fetch section metrics:', err);
    return [];
  }
}

export default function ConversionTracker() {
  return {
    trackConversion,
    trackCtaClick,
    trackSignup,
    trackTierSelected,
    trackFaqOpen,
    trackMetricView,
    trackPerformerView,
    trackChartInteraction,
    trackLinkClick,
    trackScrollDepth,
    getConversionMetrics,
    getSectionMetrics,
    initializeTracking,
    UTMBuilder,
  };
}
