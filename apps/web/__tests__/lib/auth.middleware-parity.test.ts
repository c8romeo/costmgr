/**
 * apps/web/__tests__/lib/auth.middleware-parity.test.ts — routeGuard parity.
 *
 * Phase 3-1 — T8.3 (AC #3.1, #3.2, #3.3, #3.4, #3.6) — ~12 vitest cases.
 * Covers: dashbaord path regex, auth path regex, /api/v1/* bypass, 2FA gate,
 * ?redirect= preservation, locale strip.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { NextRequest, NextResponse } from "next/server";

vi.mock("@/lib/supabase/middleware", () => ({
  updateSupabaseSession: vi.fn(),
}));

import { updateSupabaseSession } from "@/lib/supabase/middleware";
import { routeGuard } from "@/lib/auth/middleware";

const mockUpdateSupabaseSession = updateSupabaseSession as unknown as ReturnType<typeof vi.fn>;

function makeRequest(pathname: string, search = ""): NextRequest {
  const url = new URL(`http://localhost:3000${pathname}${search}`);
  return new NextRequest(url);
}

function makeSupabaseResponse(userId: string | null, aal: string | null = null): NextResponse {
  const res = NextResponse.next({ request: makeRequest("/") });
  if (userId) res.headers.set("x-user-id", userId);
  if (aal) res.headers.set("x-user-aal", aal);
  return res;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUpdateSupabaseSession.mockImplementation(async (req: NextRequest) => {
    // Default: no session.
    return makeSupabaseResponse(null);
  });
});

describe("routeGuard (Phase 3-1 T4.2)", () => {
  it("bypasses /api/v1/* paths (backend owns Supabase JWT)", async () => {
    const req = makeRequest("/api/v1/onboarding/complete-signup");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("passes through /login (auth path, public)", async () => {
    const req = makeRequest("/ko-KR/login");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("passes through /signup (auth path, public)", async () => {
    const req = makeRequest("/ko-KR/signup");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("passes through /forgot-password (auth path, public)", async () => {
    const req = makeRequest("/ko-KR/forgot-password");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("passes through /reset-password (auth path, public)", async () => {
    const req = makeRequest("/ko-KR/reset-password");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("passes through /auth/2fa (auth path, public)", async () => {
    const req = makeRequest("/ko-KR/auth/2fa");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("redirects /dashboard (no session) → /login with ?redirect=", async () => {
    const req = makeRequest("/ko-KR/dashboard");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(307);
    const location = res.headers.get("location") || "";
    // Location header is a full URL — parse it.
    const parsed = new URL(location);
    expect(parsed.pathname).toBe("/ko-KR/login");
    expect(parsed.searchParams.get("redirect")).toBe("/ko-KR/dashboard");
  });

  it("preserves entire path + search in redirect target", async () => {
    const req = makeRequest("/ko-KR/dashboard/budget", "?period=2026-08");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(307);
    const location = res.headers.get("location") || "";
    const parsed = new URL(location);
    expect(parsed.searchParams.get("redirect")).toBe("/ko-KR/dashboard/budget?period=2026-08");
  });

  it("allows /dashboard with valid session (aal2)", async () => {
    mockUpdateSupabaseSession.mockResolvedValue(makeSupabaseResponse("user-abc", "aal2"));
    const req = makeRequest("/ko-KR/dashboard");
    const res = await routeGuard(req, makeSupabaseResponse("user-abc", "aal2"));
    expect(res.status).toBe(200);
  });

  it("redirects /dashboard (aal1) → /account/security?reason=2fa_required", async () => {
    mockUpdateSupabaseSession.mockResolvedValue(makeSupabaseResponse("user-abc", "aal1"));
    const req = makeRequest("/ko-KR/dashboard/budget");
    const res = await routeGuard(req, makeSupabaseResponse("user-abc", "aal1"));
    expect(res.status).toBe(307);
    const location = res.headers.get("location") || "";
    const parsed = new URL(location);
    expect(parsed.pathname).toBe("/ko-KR/account/security");
    expect(parsed.searchParams.get("reason")).toBe("2fa_required");
  });

  it("passes through locale-less root /", async () => {
    const req = makeRequest("/");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(200);
  });

  it("strips locale before constructing /login URL", async () => {
    const req = makeRequest("/en-US/dashboard");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    expect(res.status).toBe(307);
    const location = res.headers.get("location") || "";
    const parsed = new URL(location);
    expect(parsed.pathname).toBe("/en-US/login");
  });

  it("handles root dashboard /dashboard (no locale prefix)", async () => {
    const req = makeRequest("/dashboard");
    const res = await routeGuard(req, makeSupabaseResponse(null));
    // /dashboard alone (no locale) is also a dashboard path — redirect to /login.
    expect(res.status).toBe(307);
    const location = res.headers.get("location") || "";
    const parsed = new URL(location);
    expect(parsed.pathname).toBe("/login");
  });
});
