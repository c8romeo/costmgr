/**
 * apps/web/__tests__/i18n/observability-i18n-ssot.test.ts — Phase 7 ko-KR SSOT drift detector.
 *
 * Phase 7 (cj-style 91번째 wire) — T7b frontend vitest tests.
 * PRD §F23.4 + AC #4 + AD-34 (d) verbatim + CR 11-4 D-002 + P-015.
 *
 * Verifies:
 * 1. ko-KR.json has observability namespace.
 * 2. All required keys present (16 keys min).
 * 3. Verbatim label invariants: page_title='관측성 대시보드'.
 */
import { describe, it, expect } from 'vitest';
import koKR from '../../messages/ko-KR.json';

describe('Phase 7 observability i18n SSOT drift', () => {
  it('ko-KR.json has observability namespace', () => {
    expect(koKR.observability).toBeDefined();
  });

  it('observability namespace has minimum 16 keys', () => {
    const obs = koKR.observability as Record<string, string>;
    const keys = Object.keys(obs);
    expect(keys.length).toBeGreaterThanOrEqual(16);
  });

  it('page_title is verbatim invariant "관측성 대시보드"', () => {
    const obs = koKR.observability as Record<string, string>;
    expect(obs.page_title).toBe('관측성 대시보드');
  });

  it('pagerduty_forbidden_notice mentions owner role (NFR18 ko-KR)', () => {
    const obs = koKR.observability as Record<string, string>;
    expect(obs.pagerduty_forbidden_notice).toContain('owner');
  });

  it('all observability keys are non-empty strings', () => {
    const obs = koKR.observability as Record<string, string>;
    for (const [key, value] of Object.entries(obs)) {
      expect(typeof value).toBe('string');
      expect(value.length).toBeGreaterThan(0);
    }
  });
});
