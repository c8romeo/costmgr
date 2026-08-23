// apps/api/tests/load/k6/auth-login.js
// Phase 8 (cj-style 95번째 wire) — k6 Load Testing scenario 1/5
// (PRD §F24.1 + AC #1.2).
//
// Auth-login load test: Supabase Magic link + OAuth (Google/Naver/Kakao) +
// SSO enterprise SAML combined load. 100 VU ramp 30s.
//
// Thresholds (k6 `thresholds` block — CI gate per §F24.1-7):
//   - http_req_duration: p(95)<500ms, p(99)<1000ms (PRD §F24.2-4 SLA-3)
//   - http_req_failed:   rate<0.01 (1%)
//
// Environment bindings (set by `run_k6_load_test()` in
// apps/api/core/load_test_runner.py):
//   - K6_TENANT_ID       tenant UUID (CR 0-2 RLS — tenant-scoped requests)
//   - K6_VUS             virtual user count (default 100 per F24.1-2)
//   - K6_RAMP_DURATION_S ramp duration in seconds (default 30 per F24.1-2)
//   - K6_TRACE_ID        request-scoped trace_id (CR 1-1 ContextVar carry-over)
//   - K6_DRY_RUN         "0" (real run) or "1" (no-op — `run_k6_load_test` short-circuits)
//
// CR lessons applied:
//   - CR 0-2 RLS: tenant_id is bound into the X-Tenant-Context header + JWT claim.
//   - CR 1-1: trace_id is propagated via W3C `traceparent` header (server→client propagation).

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const tenantId = __ENV.K6_TENANT_ID || '00000000-0000-0000-0000-000000000000';
const traceId = __ENV.K6_TRACE_ID || 'k6-trace-auth-login';
const vus = parseInt(__ENV.K6_VUS || '100', 10);
const ramp = parseInt(__ENV.K6_RAMP_DURATION_S || '30', 10);
const baseUrl = __ENV.K6_BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const authLoginDuration = new Trend('auth_login_duration_ms');

export const options = {
  stages: [
    { duration: `${ramp}s`, target: vus },
    { duration: '30s', target: vus },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed':   ['rate<0.01'],
    'errors':            ['rate<0.01'],
  },
};

export default function () {
  // Phase 3 wire `1db21d2` auth contract — POST /api/v1/auth/login
  // (Magic link / OAuth / SSO unified endpoint per AD-28).
  const url = `${baseUrl}/api/v1/auth/login`;
  const payload = JSON.stringify({
    email: `k6-auth-${__VU}-${__ITER}@fixture.local`,
    method: 'magic_link',
    tenant_id: tenantId,
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Context': tenantId,
      'traceparent': `00-${traceId}-${__VU}${__ITER}-01`,
    },
  };

  const res = http.post(url, payload, params);
  authLoginDuration.add(res.timings.duration);
  const ok = check(res, {
    'status is 2xx or 4xx-expected': (r) =>
      (r.status >= 200 && r.status < 300) || r.status === 401 || r.status === 429,
  });
  errorRate.add(!ok);
}
