/**
 * RATE LIMITER UTILITY
 *
 * Provides rate limiting utilities for API calls to prevent throttling
 */

/**
 * Sleep for specified milliseconds
 */
export async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Exponential backoff sleep with jitter
 */
export async function exponentialBackoff(
  attempt: number,
  baseDelayMs = 1000,
  maxDelayMs = 32000
): Promise<void> {
  const delay = Math.min(Math.pow(2, attempt) * baseDelayMs, maxDelayMs);
  const jitter = Math.random() * delay * 0.1; // 10% jitter
  return sleep(delay + jitter);
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelayMs = 1000
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < maxAttempts - 1) {
        await exponentialBackoff(attempt, baseDelayMs);
      }
    }
  }

  throw lastError || new Error('Max retry attempts exceeded');
}

/**
 * Token bucket rate limiter
 */
export class TokenBucket {
  private tokens: number;
  private readonly maxTokens: number;
  private readonly refillRate: number;
  private lastRefillTime: number;

  /**
   * @param maxTokens Maximum tokens in the bucket
   * @param refillRate Tokens per millisecond
   */
  constructor(maxTokens: number, refillRate: number) {
    this.maxTokens = maxTokens;
    this.tokens = maxTokens;
    this.refillRate = refillRate;
    this.lastRefillTime = Date.now();
  }

  /**
   * Refill tokens based on elapsed time
   */
  private refill(): void {
    const now = Date.now();
    const timePassed = now - this.lastRefillTime;
    const tokensToAdd = timePassed * this.refillRate;

    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefillTime = now;
  }

  /**
   * Consume tokens, waiting if necessary
   */
  async consume(tokens = 1): Promise<void> {
    this.refill();

    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return;
    }

    // Wait for tokens to be available
    const tokensNeeded = tokens - this.tokens;
    const waitTime = (tokensNeeded / this.refillRate) * 1000;

    await sleep(waitTime);
    this.refill();
    this.tokens -= tokens;
  }

  /**
   * Check if tokens are available without consuming
   */
  hasTokens(tokens = 1): boolean {
    this.refill();
    return this.tokens >= tokens;
  }
}

/**
 * Sliding window rate limiter
 */
export class SlidingWindowLimiter {
  private requests: number[] = [];
  private readonly maxRequests: number;
  private readonly windowMs: number;

  /**
   * @param maxRequests Maximum requests allowed
   * @param windowMs Time window in milliseconds
   */
  constructor(maxRequests: number, windowMs: number) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  /**
   * Wait if rate limit would be exceeded
   */
  async waitIfNeeded(): Promise<void> {
    const now = Date.now();

    // Remove old requests outside the window
    this.requests = this.requests.filter((time) => now - time < this.windowMs);

    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (now - oldestRequest) + 10;

      if (waitTime > 0) {
        await sleep(waitTime);
        await this.waitIfNeeded();
      }
    }

    this.requests.push(now);
  }

  /**
   * Reset the limiter
   */
  reset(): void {
    this.requests = [];
  }

  /**
   * Get current request count in window
   */
  getCurrentCount(): number {
    const now = Date.now();
    this.requests = this.requests.filter((time) => now - time < this.windowMs);
    return this.requests.length;
  }
}

/**
 * Concurrency limiter (queue-based)
 */
export class ConcurrencyLimiter {
  private running = 0;
  private queue: (() => Promise<void>)[] = [];
  private readonly maxConcurrent: number;

  constructor(maxConcurrent: number) {
    this.maxConcurrent = maxConcurrent;
  }

  /**
   * Run function with concurrency limit
   */
  async run<T>(fn: () => Promise<T>): Promise<T> {
    while (this.running >= this.maxConcurrent) {
      await sleep(10);
    }

    this.running++;

    try {
      return await fn();
    } finally {
      this.running--;
      this.processQueue();
    }
  }

  /**
   * Queue function to run when slot becomes available
   */
  async queueTask<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      const task = async () => {
        try {
          const result = await this.run(fn);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      };

      this.queue.push(task);
      this.processQueue();
    });
  }

  /**
   * Process queued tasks
   */
  private processQueue(): void {
    while (this.running < this.maxConcurrent && this.queue.length > 0) {
      const queued = this.queue.shift();
      if (queued) {
        queued().catch(console.error);
      }
    }
  }

  /**
   * Get current stats
   */
  getStats(): { running: number; queued: number; maxConcurrent: number } {
    return {
      running: this.running,
      queued: this.queue.length,
      maxConcurrent: this.maxConcurrent,
    };
  }
}

/**
 * Circuit breaker pattern for API calls
 */
export class CircuitBreaker {
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private readonly failureThreshold: number;
  private readonly successThreshold: number;
  private readonly timeoutMs: number;

  constructor(failureThreshold = 5, successThreshold = 2, timeoutMs = 60000) {
    this.failureThreshold = failureThreshold;
    this.successThreshold = successThreshold;
    this.timeoutMs = timeoutMs;
  }

  /**
   * Execute function with circuit breaker protection
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.timeoutMs) {
        this.state = 'half-open';
        this.successCount = 0;
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();

      if (this.state === 'half-open') {
        this.successCount++;
        if (this.successCount >= this.successThreshold) {
          this.state = 'closed';
          this.failureCount = 0;
          this.successCount = 0;
        }
      } else {
        this.failureCount = 0;
      }

      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();

      if (this.failureCount >= this.failureThreshold) {
        this.state = 'open';
      }

      throw error;
    }
  }

  /**
   * Get circuit breaker state
   */
  getState(): { state: 'closed' | 'open' | 'half-open'; failures: number } {
    return {
      state: this.state,
      failures: this.failureCount,
    };
  }

  /**
   * Reset the circuit breaker
   */
  reset(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.successCount = 0;
  }
}
