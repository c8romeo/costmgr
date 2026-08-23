// apps/api/tests/load/k6/onboarding-flow.js
// Phase 8 (cj-style 95번째 wire) — k6 Load Testing scenario 3/5
// (PRD §F24.1 + AC #1.4).
//
// Onboarding flow load test: Epic 1 onboarding/industry + Phase 3 wire
// `1db21d2` auth contract combined load. 30 VU.
//
// Thresholds (k6 `thresholds` block — CI gate per §F24.1-7):
//   - http_req_duration: p(95)<1000ms, p(99)<3000ms
//   - http_req_failed:   rate<0.01 (1%)
//
// Environment bindings: see apps/api/tests/load/k6/auth-login.js header.

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const tenantId = __ENV.K6_TENANT_ID || '00000000-0000-0000-0000-000000000000';
const traceId = __ENV.K6_TRACE_ID || 'k6-trace-onboarding';
const vus = parseInt(__ENV.K6_VUS || '30', 10);
const ramp = parseInt(__ENV.K6_RAMP_DURATION_S || '60', 10);
const baseUrl = __ENV.K6_BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const onboardingDuration = new Trend('onboarding_duration_ms');

export const options = {
  stages: [
    { duration: `${ramp}s`, target: vus },
    { duration: '60s', target: vus },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<3000'],
    'http_req_failed':   ['rate<0.01'],
    'errors':            ['rate<0.01'],
  },
};

export default function () {
  // Epic 1 onboarding/industry + Phase 3 wire `1db21d2` auth contract.
  // POST /api/v1/onboarding/industry-select — first-time industry selection
  // (PRD §F1.1 + AD-26 + A65~A69 결정 wire).
  const url = `${baseUrl}/api/v1/onboarding/industry-select`;
  const payload = JSON.stringify({
    tenant_id: tenantId,
    industry: 'manufacturing',
    fiscal_year_start: '2026-01-01',
    currency: 'KRW',
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Context': tenantId,
      'traceparent': `00-${traceId}-${__VU}${__ITER}-01`,
    },
  };

  const res = http.post(url, payload, params);
  onboardingDuration.add(res.timings.duration);
  const ok = check(res, {
    'status is 2xx or 4xx-expected': (r) =>
      (r.status >= 200 && r.status < 300) || r.status === 409 || r.status === 422,
  });
  errorRate.add(!ok);
}
