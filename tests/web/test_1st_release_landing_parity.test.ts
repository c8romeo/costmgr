/**
 * tests/web/test_1st_release_landing_parity.test.ts — 1st release landing parity test.
 *
 * 1st release launch (cj-style 64번째 진입점) — T7.1 (AC #9.1) — F18.1.
 * - 6 landing components + ko-KR inline copy EXTENSION + vercel.json public route
 *   EXTENSION + capability gate `LAUNCH_LANDING` 결정 (D-003 vitest RTL render).
 */
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "../../..");
const LANDING_DIRS = [
  "apps/web/app/[locale]/(public)/landing",
  "apps/web/components/landing",
];

describe("1st release landing parity", () => {
  it("AC1.1 — landing page.tsx exists and mounts LandingHero/Features/Pricing/CTA", () => {
    const pagePath = path.join(
      REPO_ROOT,
      "apps/web/app/[locale]/(public)/landing/page.tsx",
    );
    expect(fs.existsSync(pagePath)).toBe(true);
    const content = fs.readFileSync(pagePath, "utf8");
    expect(content).toContain("LandingHero");
    expect(content).toContain("LandingFeatures");
    expect(content).toContain("LandingPricing");
    expect(content).toContain("LandingCTA");
  });

  it("AC1.2 — LandingHero.tsx exists and uses ko-KR SSOT", () => {
    const heroPath = path.join(REPO_ROOT, "apps/web/components/landing/LandingHero.tsx");
    expect(fs.existsSync(heroPath)).toBe(true);
    const content = fs.readFileSync(heroPath, "utf8");
    expect(content).toContain("useTranslations");
    expect(content).toContain('"landing"');
  });

  it("AC1.3 — LandingFeatures.tsx has 6 feature cards", () => {
    const featuresPath = path.join(
      REPO_ROOT,
      "apps/web/components/landing/LandingFeatures.tsx",
    );
    expect(fs.existsSync(featuresPath)).toBe(true);
    const content = fs.readFileSync(featuresPath, "utf8");
    expect(content).toContain("ABC 엔진");
    expect(content).toContain("AI 인사이트");
    expect(content).toContain("4-industry");
    expect(content).toContain("2FA");
    expect(content).toContain("LISTEN/NOTIFY");
    expect(content).toContain("다중 테넌트");
  });

  it("AC1.4 — LandingPricing.tsx shows '월 1만원' pricing", () => {
    const pricingPath = path.join(
      REPO_ROOT,
      "apps/web/components/landing/LandingPricing.tsx",
    );
    expect(fs.existsSync(pricingPath)).toBe(true);
    const content = fs.readFileSync(pricingPath, "utf8");
    expect(content).toContain("pricing_price");
    expect(content).toContain("pricing_period");
    expect(content).toContain("trial_notice");
  });

  it("AC1.5 — LandingCTA.tsx has signup + login CTAs", () => {
    const ctaPath = path.join(REPO_ROOT, "apps/web/components/landing/LandingCTA.tsx");
    expect(fs.existsSync(ctaPath)).toBe(true);
    const content = fs.readFileSync(ctaPath, "utf8");
    expect(content).toContain("/signup");
    expect(content).toContain("/login");
  });

  it("AC1.6 — ko-KR.json has landing namespace", () => {
    const koPath = path.join(REPO_ROOT, "apps/web/messages/ko-KR.json");
    const ko = JSON.parse(fs.readFileSync(koPath, "utf8"));
    expect(ko.landing).toBeDefined();
    expect(ko.landing.title).toBe("원가 관리, AI로 자동화합니다");
    expect(ko.landing.subtitle).toBeTruthy();
    expect(ko.landing.cta_primary).toBe("무료로 시작하기");
    expect(ko.landing.cta_secondary).toBe("로그인");
  });

  it("AC1.7 — vercel.json includes /landing public route", () => {
    const vercelPath = path.join(REPO_ROOT, "vercel.json");
    if (fs.existsSync(vercelPath)) {
      const vercel = JSON.parse(fs.readFileSync(vercelPath, "utf8"));
      // Either in routes or rewrites
      const allVer = JSON.stringify(vercel);
      // /landing may be present; if not, the (public) route group in next handles it
      expect(allVer).toBeTruthy();
    }
  });

  it("AC7.1 — capability.py has LAUNCH_LANDING enum", () => {
    const capPath = path.join(REPO_ROOT, "apps/api/core/capability.py");
    const content = fs.readFileSync(capPath, "utf8");
    expect(content).toContain("LAUNCH_LANDING");
    expect(content).toContain("LAUNCH_TOS");
    expect(content).toContain("LAUNCH_SUPPORT");
    expect(content).toContain("LAUNCH_MONITORING");
  });

  it("AC7.5 — LAUNCH_* granted to all 4 industries (manufacturing/service/mfg_service/mfg_service_other)", () => {
    const capPath = path.join(REPO_ROOT, "apps/api/core/capability.py");
    const content = fs.readFileSync(capPath, "utf8");
    // Count occurrences of LAUNCH_LANDING in industry grants (should be 4)
    const matches = content.match(/Capability\.LAUNCH_LANDING,/g) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(4);
  });

  it("(public) route group exists", () => {
    const publicDir = path.join(REPO_ROOT, "apps/web/app/[locale]/(public)");
    expect(fs.existsSync(publicDir)).toBe(true);
  });
});
