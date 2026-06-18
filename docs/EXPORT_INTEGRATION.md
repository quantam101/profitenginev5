# Export System Integration Guide

Complete guide for integrating the export system into ProfitEngine workflows.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Customer Browser                         │
├─────────────────────────────────────────────────────────────┤
│  /trading/export                                             │
│  ├─ Format selector (CSV, PDF, Tax CSV)                     │
│  ├─ Date range picker                                        │
│  └─ Download button → POST /api/trading/export              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│             Next.js API Layer (Next-Auth)                    │
├─────────────────────────────────────────────────────────────┤
│  /api/trading/export (POST)                                 │
│  ├─ Authenticate user via NextAuth                          │
│  ├─ Validate request parameters                             │
│  └─ Route to report generator                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
    ┌─────────────┐            ┌──────────────────┐
    │ CSV Export  │            │ PDF Report (HTML)│
    ├─────────────┤            ├──────────────────┤
    │ Generate CSV│            │ Generate HTML    │
    │ stream      │            │ with charts/data │
    └──────┬──────┘            └────────┬─────────┘
           │                           │
           └──────────────┬───────────┘
                          │
         ┌────────────────┴─────────────────┐
         │                                  │
         ▼                                  ▼
    ┌──────────────────────────────────────────────┐
    │   Report Generator Library                    │
    ├──────────────────────────────────────────────┤
    │  - trading-report.ts (HTML/CSV generation)   │
    │  - trade-analytics.ts (metrics calculation)  │
    │  - pdf-generator.ts (PDF conversion)         │
    └────────────────┬─────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
         ▼                        ▼
    ┌─────────────────┐    ┌──────────────────┐
    │  Runtime API    │    │  Clients DB      │
    │  (Trade data)   │    │  (User metadata) │
    └─────────────────┘    └──────────────────┘
```

## Data Flow

### 1. User Initiates Export
```typescript
// User fills form and clicks export
const response = await fetch('/api/trading/export', {
  method: 'POST',
  body: JSON.stringify({
    format: 'csv|pdf|tax-csv',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    dataType: 'all|summary|trades|tax'
  })
});
```

### 2. Authentication & Validation
```typescript
// route.ts - GET user from session
const session = await getServerSession(authOptions);
const userId = session.user.id; // NOT from user input

// Validate parameters
if (!['csv', 'pdf', 'tax-csv'].includes(format)) {
  throw new Error('Invalid format');
}

// Validate date range
if (new Date(startDate) > new Date(endDate)) {
  throw new Error('Invalid date range');
}
```

### 3. Fetch Data
```typescript
// Fetch from runtime API with authentication
const trades = await fetchUserTrades(userId, startDate, endDate);
const dailyTrades = await fetchDailyTrades(userId, 365);
```

### 4. Generate Report
```typescript
// Calculate analytics
const taxData = calculateTaxData(trades);
const summary = calculateSummary(trades);
const monthly = calculateMonthlyPerformance(dailyTrades);

// Create report config
const config: ReportConfig = {
  userId,
  trades,
  taxData,
  summary,
  monthlyPerformance: monthly,
  // ...
};

// Generate output
if (format === 'csv') {
  return generateCSVExport(trades, config);
}
if (format === 'pdf') {
  return generateTradingReportHTML(config);
}
```

### 5. Return to User
```typescript
// Set headers for download
return new NextResponse(fileContent, {
  headers: {
    'Content-Type': 'text/csv',
    'Content-Disposition': `attachment; filename="trading-export-*.csv"`
  }
});
```

## Integration Points

### 1. Authentication
Uses existing NextAuth configuration:
```typescript
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

const session = await getServerSession(authOptions);
```

### 2. Runtime API
Connects to runtime service for trade data:
```typescript
// Environment variable
const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

// API call with authentication
const res = await fetch(`${RUNTIME}/api/clients/trades`, {
  headers: {
    Authorization: `Bearer ${process.env.CLIENT_API_KEY}`
  }
});
```

### 3. Database Access
Uses existing ClientsDB for user metadata:
```typescript
import { ClientsDB } from '@/lib/clients-db';

const db = new ClientsDB();
const user = db.getUser(userId);
```

## Extending the System

### Add New Export Format

1. Add format to validation list:
```typescript
const validFormats = ['csv', 'pdf', 'tax-csv', 'json']; // Add 'json'
```

2. Add generation function in `trading-report.ts`:
```typescript
export function generateJSONExport(trades: TradeRecord[]): string {
  return JSON.stringify({
    metadata: { /* ... */ },
    trades: trades,
    summary: { /* ... */ }
  }, null, 2);
}
```

3. Add handler in route.ts:
```typescript
if (format === 'json') {
  const json = generateJSONExport(trades as any);
  return new NextResponse(json, {
    headers: {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="trades.json"`
    }
  });
}
```

### Add Custom Metrics

1. Create new analytics function in `trade-analytics.ts`:
```typescript
export function analyzeCustomMetric(trades: TradeRecord[]): MetricData {
  // Custom analysis logic
  return { /* metrics */ };
}
```

2. Call from API and pass to report generator:
```typescript
const customMetrics = analyzeCustomMetric(trades);

const config: ReportConfig = {
  // ... existing fields
  customMetrics,
};
```

3. Display in report template:
```typescript
<div>
  <h3>${customMetrics.title}</h3>
  <p>${customMetrics.value}</p>
</div>
```

### Add Email Delivery

1. Create email service integration:
```typescript
import { sendEmail } from '@/lib/email-service';

// After generation
await sendEmail({
  to: user.email,
  subject: `Your Trading Export - ${new Date().toDateString()}`,
  attachments: [{
    filename: `trading-export-${Date.now()}.csv`,
    content: csvContent
  }]
});
```

2. Add email preference toggle to export form

## Monitoring & Analytics

### Track Export Usage
```typescript
// Log export requests for analytics
const logExport = async (userId: number, format: string) => {
  await db.query(
    'INSERT INTO export_logs (user_id, format, timestamp) VALUES (?, ?, ?)',
    [userId, format, new Date().toISOString()]
  );
};
```

### Performance Monitoring
```typescript
const startTime = Date.now();

// ... generate export ...

const duration = Date.now() - startTime;
console.log(`Export generated in ${duration}ms`);

// Alert if slow
if (duration > 5000) {
  console.warn(`Slow export detected: ${duration}ms`);
}
```

### Error Tracking
```typescript
try {
  // ... export logic ...
} catch (error) {
  // Log to error tracking service
  console.error('Export failed:', {
    userId,
    format,
    error: error.message,
    timestamp: new Date().toISOString()
  });

  // Return to user
  return NextResponse.json(
    { error: 'Export failed' },
    { status: 500 }
  );
}
```

## Security Checklist

- [x] User authentication required (NextAuth)
- [x] User ID from session (not request parameter)
- [x] HTTPS/TLS for downloads
- [x] No sensitive data in logs
- [x] Rate limiting recommended
- [x] Input validation on all parameters
- [x] Parameterized queries to runtime API
- [x] No persistent export storage
- [x] Temporary files cleaned up
- [x] CORS configured if needed

### Adding Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(5, '1 h'), // 5 exports per hour
});

export async function POST(request: NextRequest) {
  const { success } = await ratelimit.limit(userId);
  
  if (!success) {
    return NextResponse.json(
      { error: 'Too many exports. Try again later.' },
      { status: 429 }
    );
  }
  
  // ... continue with export
}
```

## Testing Strategy

### Unit Tests
- CSV generation with edge cases
- Tax calculations (short/long term, wash sales)
- Strategy analysis metrics
- Date range validation

```bash
npm run test:export
```

### Integration Tests
- End-to-end export flow
- Authentication validation
- Runtime API integration
- Database connectivity

### Performance Tests
- Large dataset exports (10,000+ trades)
- Concurrent export requests
- Memory usage monitoring

## Deployment Considerations

### Environment Variables Required
```env
RUNTIME_API_URL=http://runtime:8080
CLIENT_API_KEY=your-api-key
NEXTAUTH_URL=https://profitengine.example.com
NEXTAUTH_SECRET=your-secret
```

### Resource Requirements
- **CPU**: Minimal for small exports, scales with data size
- **Memory**: ~100MB for typical exports, 500MB+ for 10K+ trades
- **Disk**: Temporary storage for reports (auto-cleanup)
- **Network**: Runtime API connectivity required

### Scaling Recommendations
- Use streaming responses for very large exports
- Implement job queue for background processing
- Cache monthly aggregates if computation expensive
- Use CDN for common file deliveries

## Troubleshooting Integration

### Export Hangs
- Check runtime API availability
- Verify database connections
- Review server logs for timeouts
- Consider implementing async processing

### Missing Data
- Verify runtime API is returning correct data
- Check user authentication
- Ensure trades are recorded in system
- Review data in trading dashboard

### Performance Issues
- Profile with large datasets
- Optimize data fetching (pagination)
- Cache expensive calculations
- Use database indexes

## Future Integration Plans

- [ ] Scheduled exports (daily/weekly)
- [ ] Email delivery of exports
- [ ] Cloud storage integration (S3, GCS)
- [ ] QuickBooks/Xero API integration
- [ ] Real-time streaming exports
- [ ] Custom report templates
- [ ] Webhook notifications

## Support Resources

- Documentation: `/docs/EXPORT_SYSTEM.md`
- API Reference: `/docs/EXPORT_SYSTEM.md#api-reference`
- Test Suite: `/tests/export-system.test.mjs`
- Example Implementations: `/app/components/ExportButton.tsx`

---

**Last Updated**: 2024-06-18  
**Maintained By**: ProfitEngine Team
