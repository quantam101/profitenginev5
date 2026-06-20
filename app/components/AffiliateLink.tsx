'use client';

import { ReactNode, useEffect, useState } from 'react';

export interface AffiliateLinkProps {
  /** Partner name (e.g., 'interactive_brokers', 'tastytrade', 'amazon') */
  partner: string;

  /** The affiliate URL to redirect to */
  href: string;

  /** Link text displayed to user */
  children: ReactNode;

  /** Optional CSS class */
  className?: string;

  /** Show FTC disclosure badge? (default: true) */
  showBadge?: boolean;

  /** Badge position: inline or title (default: inline) */
  badgePosition?: 'inline' | 'tooltip' | 'hidden';

  /** Enable click tracking (default: true) */
  trackClick?: boolean;

  /** Optional tracking parameters (e.g., 'blog-post-iron-condor') */
  trackingSource?: string;

  /** Open in new tab? (default: true) */
  target?: '_blank' | '_self';

  /** Link style variant */
  variant?: 'inline' | 'button' | 'card';

  /** Button-specific properties */
  buttonProps?: {
    size?: 'sm' | 'md' | 'lg';
    color?: 'primary' | 'secondary' | 'success';
  };
}

/**
 * AffiliateLink Component
 *
 * Wraps affiliate URLs with:
 * - FTC disclosure badge
 * - Click tracking (partner, source, timestamp)
 * - Tooltip explanation
 * - UTM parameter injection
 * - Accessibility helpers
 *
 * Usage:
 * <AffiliateLink
 *   partner="interactive_brokers"
 *   href="https://www.interactivebrokers.com/..."
 *   trackingSource="blog-post-advanced-options"
 * >
 *   Open Interactive Brokers
 * </AffiliateLink>
 */
export default function AffiliateLink({
  partner,
  href,
  children,
  className = '',
  showBadge = true,
  badgePosition = 'inline',
  trackClick = true,
  trackingSource = 'unknown',
  target = '_blank',
  variant = 'inline',
  buttonProps,
}: AffiliateLinkProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [clicked, setClicked] = useState(false);

  // Add UTM parameters to the affiliate link
  const urlWithUtm = new URL(href);
  if (!urlWithUtm.searchParams.has('utm_source')) {
    urlWithUtm.searchParams.set('utm_source', `profitengine-${partner}`);
  }
  if (!urlWithUtm.searchParams.has('utm_medium')) {
    urlWithUtm.searchParams.set('utm_medium', 'affiliate');
  }
  if (!urlWithUtm.searchParams.set('utm_campaign', trackingSource)) {
    urlWithUtm.searchParams.set('utm_campaign', trackingSource);
  }

  // Track click event
  const handleClick = async (e: React.MouseEvent<HTMLAnchorElement | HTMLButtonElement>) => {
    if (trackClick) {
      setClicked(true);

      // Send tracking event (non-blocking)
      try {
        await fetch('/api/affiliate/track', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            partner,
            source: trackingSource,
            timestamp: new Date().toISOString(),
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
          }),
          // Non-blocking — don't await
        }).catch(() => {
          // Silently fail; don't block navigation
        });
      } catch (err) {
        // Network error — continue normally
      }
    }
  };

  // Disclosure tooltip text
  const disclosureText =
    'This is an affiliate link. If you make a purchase or sign up, I may earn a commission at no extra cost to you.';

  // Render badge component
  const BadgeComponent = () => (
    <span
      className="affiliate-disclosure-badge"
      title={disclosureText}
      aria-label="Affiliate Link Disclosure"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        background: '#f0f4f8',
        border: '1px solid #cbd5e0',
        padding: '2px 6px',
        borderRadius: '3px',
        fontSize: '11px',
        color: '#4a5568',
        fontWeight: 500,
        marginLeft: '4px',
        cursor: 'help',
      }}
    >
      <span style={{ fontSize: '10px' }}>🔗</span>
      <span>Affiliate</span>
    </span>
  );

  // Variant: inline link with optional badge
  if (variant === 'inline') {
    return (
      <span
        style={{ display: 'inline' }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <a
          href={urlWithUtm.toString()}
          target={target}
          rel={target === '_blank' ? 'noopener noreferrer' : undefined}
          onClick={handleClick}
          className={`affiliate-link ${className}`}
          title={disclosureText}
          style={{
            color: '#0066cc',
            textDecoration: isHovered || clicked ? 'underline' : 'none',
            cursor: 'pointer',
            transition: 'text-decoration 0.2s',
            ...getInlineStyles(clicked),
          }}
          aria-describedby={`affiliate-disclosure-${partner}`}
        >
          {children}
        </a>
        {showBadge && badgePosition === 'inline' && <BadgeComponent />}
        {showBadge && badgePosition === 'tooltip' && isHovered && (
          <div
            id={`affiliate-disclosure-${partner}`}
            role="tooltip"
            style={{
              position: 'absolute',
              background: '#2d3748',
              color: 'white',
              padding: '8px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              marginTop: '4px',
              zIndex: 1000,
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            {disclosureText}
          </div>
        )}
      </span>
    );
  }

  // Variant: button style
  if (variant === 'button') {
    const size = buttonProps?.size || 'md';
    const color = buttonProps?.color || 'primary';

    const sizeStyles = {
      sm: { padding: '6px 12px', fontSize: '12px' },
      md: { padding: '10px 20px', fontSize: '14px' },
      lg: { padding: '14px 28px', fontSize: '16px' },
    };

    const colorStyles = {
      primary: { background: '#667eea', color: 'white' },
      secondary: { background: '#e2e8f0', color: '#2d3748' },
      success: { background: '#48bb78', color: 'white' },
    };

    return (
      <a
        href={urlWithUtm.toString()}
        target={target}
        rel={target === '_blank' ? 'noopener noreferrer' : undefined}
        onClick={handleClick}
        className={`affiliate-button ${className}`}
        title={disclosureText}
        style={{
          display: 'inline-block',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'opacity 0.2s, box-shadow 0.2s',
          textDecoration: 'none',
          ...sizeStyles[size],
          ...colorStyles[color],
          ...(isHovered && { opacity: 0.9, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }),
        }}
        aria-describedby={`affiliate-disclosure-${partner}`}
      >
        {children}
        {showBadge && badgePosition === 'inline' && (
          <span
            style={{
              marginLeft: '8px',
              fontSize: '12px',
            }}
          >
            🔗
          </span>
        )}
      </a>
    );
  }

  // Variant: card style (e.g., for resource pages)
  if (variant === 'card') {
    return (
      <div
        className={`affiliate-card ${className}`}
        style={{
          border: '1px solid #cbd5e0',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '12px',
          background: '#f9fafb',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          ...(isHovered && {
            borderColor: '#667eea',
            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.1)',
          }),
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <a
              href={urlWithUtm.toString()}
              target={target}
              rel={target === '_blank' ? 'noopener noreferrer' : undefined}
              onClick={handleClick}
              style={{
                color: '#0066cc',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '16px',
              }}
              title={disclosureText}
            >
              {children}
            </a>
            {showBadge && (
              <div style={{ marginTop: '8px' }}>
                <BadgeComponent />
              </div>
            )}
          </div>
          <a
            href={urlWithUtm.toString()}
            target={target}
            rel={target === '_blank' ? 'noopener noreferrer' : undefined}
            onClick={handleClick}
            style={{
              marginLeft: '12px',
              padding: '8px 16px',
              background: '#667eea',
              color: 'white',
              borderRadius: '4px',
              textDecoration: 'none',
              fontSize: '14px',
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}
          >
            Learn More →
          </a>
        </div>
      </div>
    );
  }

  return null;
}

/**
 * Helper function to get inline styles based on click state
 */
function getInlineStyles(clicked: boolean) {
  return {
    opacity: clicked ? 0.6 : 1,
  };
}

/**
 * Pre-configured affiliate link components for common partners
 */

export const InteractiveBrokersLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="interactive_brokers"
    href="https://www.interactivebrokers.com/en/trading/affiliates?source=quantam101"
    {...props}
  />
);

export const TastytradeLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="tastytrade"
    href="https://tastytrade.go2cloud.org/?sid=alreadyhere-llc"
    {...props}
  />
);

export const ThinkorSwimLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="thinkorswim"
    href="https://www.tdameritrade.com/home.page?source=quantam101"
    {...props}
  />
);

export const AlpacaLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="alpaca"
    href="https://alpaca.markets/?affiliate_id=profitenginev5"
    {...props}
  />
);

export const PolygonLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="polygon_io"
    href="https://polygon.io?utm_source=quantam101&utm_campaign=affiliate"
    {...props}
  />
);

export const TradingViewLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="tradingview"
    href="https://tradingview.onelink.me/?ids=iOS,Android,Web&pid=profitengine&c=affiliate"
    {...props}
  />
);

export const UdemyLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="udemy"
    href="https://www.udemy.com/?utm_source=profitengine"
    {...props}
  />
);

export const GumroadLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="gumroad"
    href="https://gumroad.com/alreadyhere"
    {...props}
  />
);

export const AmazonLink = (props: Omit<AffiliateLinkProps, 'partner' | 'href'>) => (
  <AffiliateLink
    partner="amazon"
    href={props.href} // User must provide custom search link
    {...props}
  />
);
