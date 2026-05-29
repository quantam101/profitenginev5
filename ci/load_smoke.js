// k6 smoke load test — runs in CI Stage 4.
// Targets: < 500ms p95, < 1% errors, 30s ramp 0 → 20 VUs.
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
  stages: [
    { duration: "10s", target: 5 },
    { duration: "20s", target: 20 },
    { duration: "10s", target: 0 },
  ],
};

const BASE = __ENV.BASE_URL || "http://localhost:8001";

export default function () {
  for (const path of ["/api/health", "/api/agents/fleet-stats", "/api/distillation/status"]) {
    const r = http.get(`${BASE}${path}`);
    check(r, { [`${path} 200`]: (x) => x.status === 200 });
    sleep(0.1);
  }
}
