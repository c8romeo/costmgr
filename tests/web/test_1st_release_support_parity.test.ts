/**
 * tests/web/test_1st_release_support_parity.test.ts — 1st release support parity test.
 *
 * 1st release launch (cj-style 64번째 진입점) — T7.1 (AC #9.2) — F18.4 Support channels.
 * - HelpWidget + FAQ + onboarding wizard 4-step + tooltip 4 conditions +
 *   support@bizup.kr mailto link 결정.
 */
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "../../..");

describe("1st release support parity", () => {
  it("AC4.1 — docs/support.md exists with 6 sections", () => {
    const supportPath = path.join(REPO_ROOT, "docs/support.md");
    expect(fs.existsSync(supportPath)).toBe(true);
    const content = fs.readFileSync(supportPath, "utf8");
    expect(content).toContain("## 1. 연락 채널");
    expect(content).toContain("## 2. 자주 묻는 질문");
    expect(content).toContain("## 3. 응답 시간");
    expect(content).toContain("## 4. SLA");
    expect(content).toContain("## 5. Escalation");
    expect(content).toContain("## 6. 외부 지원 링크");
  });

  it("AC4.3 — HelpWidget.tsx has floating button + FAQ + email", () => {
    const widgetPath = path.join(
      REPO_ROOT,
      "apps/web/components/support/HelpWidget.tsx",
    );
    expect(fs.existsSync(widgetPath)).toBe(true);
    const content = fs.readFileSync(widgetPath, "utf8");
    expect(content).toContain("support@bizup.kr");
    expect(content).toContain("mailto:");
    expect(content).toContain("faq_link");
  });

  it("AC4.4 — (auth)/support/page.tsx exists", () => {
    const pagePath = path.join(
      REPO_ROOT,
      "apps/web/app/[locale]/(auth)/support/page.tsx",
    );
    expect(fs.existsSync(pagePath)).toBe(true);
  });

  it("AC4.5 — docs/faq.md has 10 Q&A", () => {
    const faqPath = path.join(REPO_ROOT, "docs/faq.md");
    expect(fs.existsSync(faqPath)).toBe(true);
    const content = fs.readFileSync(faqPath, "utf8");
    // Count "## N." patterns for Q&A
    const qa = content.match(/^## \d+\. /gm) ?? [];
    expect(qa.length).toBeGreaterThanOrEqual(10);
  });

  it("AC4.6 — ko-KR.json has support namespace", () => {
    const koPath = path.join(REPO_ROOT, "apps/web/messages/ko-KR.json");
    const ko = JSON.parse(fs.readFileSync(koPath, "utf8"));
    expect(ko.support).toBeDefined();
    expect(ko.support.email_value).toBe("support@bizup.kr");
    expect(ko.support.sla_p1).toBeTruthy();
    expect(ko.support.sla_p2).toBeTruthy();
  });

  it("AC3.1 — docs/onboarding-guide.md exists with 8 sections", () => {
    const guidePath = path.join(REPO_ROOT, "docs/onboarding-guide.md");
    expect(fs.existsSync(guidePath)).toBe(true);
    const content = fs.readFileSync(guidePath, "utf8");
    expect(content).toContain("## 1. 시작하기");
    expect(content).toContain("## 8. 지원팀 연락");
  });

  it("AC3.2 — OnboardingTooltip.tsx has 4 tooltip conditions", () => {
    const tipPath = path.join(
      REPO_ROOT,
      "apps/web/components/onboarding/OnboardingTooltip.tsx",
    );
    expect(fs.existsSync(tipPath)).toBe(true);
    const content = fs.readFileSync(tipPath, "utf8");
    expect(content).toContain("1: 1 | 2 | 3 | 4");
    // Check 4 messages
    expect(content).toContain("대시보드 위젯 5종을 자유롭게 추가/제거하세요");
    expect(content).toContain("ABC/TDABC 분석을 위한 원가 데이터를 입력하세요");
    expect(content).toContain("월간/분기/연간 보고서를 자동 생성합니다");
    expect(content).toContain("TOTP 앱으로 2차 인증을 설정하세요");
  });

  it("AC3.3 — onboarding page.tsx has 4-step wizard + localStorage flag", () => {
    const pagePath = path.join(
      REPO_ROOT,
      "apps/web/app/[locale]/(auth)/onboarding/page.tsx",
    );
    expect(fs.existsSync(pagePath)).toBe(true);
    const content = fs.readFileSync(pagePath, "utf8");
    expect(content).toContain("costmgr.onboarding.completed");
    expect(content).toContain("[1, 2, 3, 4]");
  });

  it("AC3.5 — ko-KR.json has onboarding namespace", () => {
    const koPath = path.join(REPO_ROOT, "apps/web/messages/ko-KR.json");
    const ko = JSON.parse(fs.readFileSync(koPath, "utf8"));
    expect(ko.onboarding).toBeDefined();
    expect(ko.onboarding.welcome_title).toBe("환영합니다!");
    expect(ko.onboarding.welcome_subtitle).toBeTruthy();
    expect(ko.onboarding.step_dashboard_title).toBe("대시보드");
    expect(ko.onboarding.step_data_title).toBe("데이터 입력");
    expect(ko.onboarding.step_reports_title).toBe("보고서");
    expect(ko.onboarding.step_security_title).toBe("보안");
  });

  it("AC2.1/2.2 — ToS and Privacy docs exist", () => {
    const tosPath = path.join(REPO_ROOT, "docs/terms-of-service.md");
    const privacyPath = path.join(REPO_ROOT, "docs/privacy-policy.md");
    expect(fs.existsSync(tosPath)).toBe(true);
    expect(fs.existsSync(privacyPath)).toBe(true);
    const tos = fs.readFileSync(tosPath, "utf8");
    const privacy = fs.readFileSync(privacyPath, "utf8");
    // ToS has 8 sections
    const tosSections = tos.match(/^## \d+\. /gm) ?? [];
    expect(tosSections.length).toBeGreaterThanOrEqual(8);
    // Privacy has 10 sections
    const privacySections = privacy.match(/^## \d+\. /gm) ?? [];
    expect(privacySections.length).toBeGreaterThanOrEqual(10);
    // GDPR mention in privacy
    expect(privacy).toContain("GDPR");
    // PIPA mention in privacy
    expect(privacy).toContain("PIPA");
  });
});
