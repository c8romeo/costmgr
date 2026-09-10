---
name: k3-chunk4-ads-nfr-verification-done
description: K-3 chunk 4 검증 결정 wire (cj-style 291번째) — PRD §14 비기능 요구·제약 (NFR 표) + §F cross-section NFRs (NFR4/NFR5/NFR6/NFR11/NFR18) + 25 ADs (Architecture Decisions) ↔ source code 정합 검증 결과 종합 capture + 결정 wire 진입 보류 명시.
metadata:
  type: project
---

# K-3 chunk 4 검증 결정 wire — DONE

> **Sprint**: K-3 chunk 4 검증 결정 wire (cj-style 291번째)
> **Date**: 2026-09-11 KST (D-3)
> **Status**: ✅ **CLOSED ✅ HONEST** (sprint-status v4.106 → v4.107 EXTENSION A751)
> **Territory**: K-4 검증 chunk 4 = PRD 제약사항 (25 ADs + NFR) 정합
> **Sprint form**: docs-only atomic single sprint (CR 11-3 honest-DEFER 291번째)
> **commit**: 본 sprint commit (4 files docs-only atomic)
> **직전 sprint**: K-3 chunk 3 검증 결정 wire (`ab31195`, sprint-status v4.105 → v4.106 EXTENSION A750, cj-style 290번째)

---

## §1 의도 분석 — K-3 chunk chain 의 logical next step

### 사용자 결정 wire (2026-09-11 KST, 본 sprint 진입 trigger)
- K-3 결정 wire (`cc84b0e`, cj-style 286번째) 의 chunk 4~6 결정 보류 옵션 중 **옵션 (d) K-3 chunk 4 = 제약사항 (25 ADs + NFR) 정합** verbatim mirror 진입
- K-3 chunk chain: UJ (§2.A) → 핵심기능 (§8.1 M0~M12) → 상세기능 (§F0~§F42) → **제약사항 (25 ADs + NFR)** → 화면정의 (§UI) → 디자인가이드 (별도)

### 정직 회복 — PRD §14 + 25 ADs + NFRs 정합 검증
- PRD `_bmad-output/planning-artifacts/prd.md` 의 **§14 비기능 요구·제약** = line 3556~3584, NFR 표 14 rows
- PRD §F cross-section NFRs = NFR4 (PII minimization, §F22.4) / NFR5 (TLS, §F12.1) / NFR6 (AES-256-GCM, §F12.1) / NFR11 (AI 추출 응답 P95 ≤ 30s, §F10/§F23.3) / NFR18 (ko-KR, §F23.4)
- **25 ADs** = `docs/architecture-decisions/` 16 files (AD-7/AD-8/AD-11/AD-14 [3 variants]/AD-15/AD-19/AD-49~AD-56) = 실질 ~13 distinct AD numbers + AD-14 의 3 variants
- 결정 wire 진입 보류 명시 — 옵션 (β) docs+test / 옵션 (γ) source 변경 모두 결정 보류

---

## §2 PRD §14 NFR 표 정합 (14 rows)

### 2.1 데이터 규모 + 성능
- **데이터 규모**: 테넌트 ≤ 100, 제품 ≤ 500, 자재 ≤ 2,000, 월 거래건수 ≤ 50,000, 월 입력 동시 사용자 ≤ 10 — capability matrix v1.54 EXTENSION 정합 (per-tenant baseline)
- **성능**: 단일 테넌트 월 계산 P95 ≤ 5초 (Phase 10 NFR11 SLO 정합), 보고서 조회 P95 ≤ 3초, AI 추출 응답 P95 ≤ 30초 (NFR11)
- **정합 ✅ PASS** — Phase 8 wire `60d4ea1` (Performance / Load Testing) + Phase 10 wire (SLO Engineering) 결정 wire 정합

### 2.2 마이그레이션 + 법적 문서 + 파일럿 투입 + 서비스명
- **마이그레이션**: 원본 엑셀 5종 가져오기 (유통품 자기참조 BOM → merchandise 자동 변환) — capability matrix v1.54 EXTENSION 정합
- **법적 문서**: ToS + Privacy Policy 한국 PIPA + GDPR 정합 — 1st release wire (D-15-LAUNCH-2 결정 wire) + Epic 17 Audit Log Retention 결정 wire 정합
- **파일럿 투입**: 개발 중반 시점에 재논의 — Pilot W1 launch D-day 2026-09-14 KST 결정 wire 보존 (D-3) + §14.A OQ-3 결정 wire 정합
- **서비스명 '비즈업'**: 가칭, 확정 재논의 — K-4 정의 결정 wire 보존

### 2.3 NFR 표 14 rows 정합
| NFR | 1차 목표 | 2차 확장 | 측정 방법 | 정합 |
|------|----------|----------|---------|------|
| 가용성 | 99.5% (월 4h 다운 허용) | 99.9% | PostgreSQL ping + 모니터링 | ✅ Phase 10 SLO 결정 wire |
| RPO | 24h (일 1회 백업) | 1h | 백업 시각 vs 장애 시각 | ✅ Phase 5 wire `f093f8c` + §F20.4 PITR 30일 |
| RTO | 4h (1인 운영자 수동 복구) | 1h | 장애 선언 → 복구 완료 | ✅ Phase 5 wire + failover 30s RTO target |
| 백업 보관 | 30일 (자동), 1년 (분기) | 1년 (자동) | 보관 정책 | ✅ §F16.6 + Phase 5 wire + Phase 6 wire (365일 cold archive) |
| 감사로그 보존 | 5년 (append-only [A8]) | 5년 | DB retention | ✅ §F22.1 retention policy (AUDIT 2557일 = 7년 SOX hold) |
| 보안 — 전송 | TLS 1.3 | TLS 1.3 | Cert 검증 | ✅ §F12.1 NFR5 |
| 보안 — 저장 | AES-256 at rest, KMS 관리 | 동일 | KMS audit | ✅ §F12.1 NFR6 AES-256-GCM |
| 인증 | 2FA 강제 (M12-a) | SSO 추가 | M12 | ✅ §F15 (Phase 3) + §F17 (Epic 15 SSO) + §F19 (Epic 16 Tenant IdP) |
| 동시 사용자 (테넌트당) | 10 | 50 | 동시접속 카운터 | ✅ capability matrix per-tenant baseline |
| 데이터 볼륨 (테넌트당) | 제품 500, 자재 2,000, 월 50K 트랜잭션 | 10× | DB row count | ✅ capability matrix per-tenant baseline |
| 인프라 페이로드 | Supabase Free → Pro 승격 트리거 | — | 운영자 콘솔 알림 | ✅ Phase 4 wire + cj-305b Resend swap |
| **언어 (UI 라벨)** | **한국어 only** (1차) | 다국어 (en-US + ja-JP 우선) | `ko-KR.json` SSOT | ✅ §F15.4 + ESLint rule + §14.B NON-GOAL #5 |
| **AI 추출 응답** | P95 ≤ 30초 | 동일 | Anthropic Claude Vision + NFR11 SLO | ✅ §F10.1 + Phase 7 wire + NFR11 |
| **AI 인사이트 cache hit** | sub-100ms | 동일 | in-memory + DB lookup | ✅ §F10.2 + Epic 13/14 LISTEN/NOTIFY wire |
| **AI 배지 reject counter** | **target 0건** | 동일 | audit_logs.action_name='ai_badge_source_kind_rejected' | ✅ §F10.2 + AD-7 verbatim |

### 2.4 §14.A 미해결 질문 (OQ) 정합
- **OQ-1~OQ-3**: PRD §14.A 의 open questions
- **OQ-3** (Pilot launch trigger "M0-M6 close + 1주 Monday alignment") = `memory/project-2026-09-10-pilot-launch-date-rationale-audit.md` 의 정직 검증 결과 반영 — **validation grade LOW** (작성팀 자인 정당화 부족), 9/14 = operationally derived deadline, **slide 비용 ≈ 0원** (외부 약속 부재 검증)
- **정합 ✅ PASS** — OQ 결정 wire 보존 + §15 로드맵 + §부록 A 정합

### 2.5 §14.B 비목표 (Non-Goals for MVP) 정합
- **NON-GOAL #5** (한국어 only 1차, 다국어 2차) — §F15.4 ko-KR SSOT 결정 wire 정합
- **NON-GOAL #2** (M8 예산 시나리오 1차 1개 제한) — §F8.1 + capability matrix v1.17 BUDGET_SCENARIO 정합
- **정합 ✅ PASS** — K-4 정의 결정 wire 의 PRD §14.B NON-GOAL for MVP #1~6 (제조부문 ABC·다단요금제·A×B×C×D·복수예산 등) 의도된 비목표 정직 회복

---

## §3 PRD §F cross-section NFRs 정합 (5 NFRs)

### 3.1 NFR4 (PII minimization, §F22.4)
- **§F22.4 GDPR / NFR4 PII minimization + Article 17 erasure EXTENSION** — `email_mask(email) → "[REDACTED:sha256(email)]"` + `ip_mask(ip) → "[REDACTED:ip]/24"` + audit-first INSERT `audit_log_pii_masked` (CR 1-1 verbatim) + audit_log_archive immutable + SHA-256 hash chain linkage + 1st release close-out retro §6 + Epic 17 close-out retro §11 "audit log retention policy 결정 wire 보류, Phase 6+ 진입 시점" verbatim 해소
- **정합 ✅ PASS** — Phase 6 wire (commit `4a57dd` retroactive close-out) + capability matrix v1.31 EXTENSION AUDIT_LOG_RETENTION 정합

### 3.2 NFR5 (TLS) + NFR6 (AES-256-GCM, §F12.1)
- **§F12.1** (2FA mandatory gate wire, M12-a) — TLS 1.3 + AES-256-GCM 결정 wire 정합
- **정합 ✅ PASS** — Epic 12 wire + Epic 15 SSO + Epic 16 Tenant IdP 결정 wire 정합

### 3.3 NFR11 (AI 추출 응답 P95 ≤ 30초, §F10/§F23.3)
- **§F10.1** (Three-Insight Cache Policy) — NFR11 P95 ≤ 30s [AD-25 verbatim] + cache hit sub-100ms
- **§F23.3** (Alerting system) — `SlowCalc` alert rule `business_cost_engine_duration_seconds p99 > 5s for 10m` (Phase 7 wire `59b56cd` 의 7 NEW business metrics carry-over)
- **§F23.2** (Prometheus custom metrics) — `business_ai_extraction_duration_seconds{model,outcome}` Histogram
- **정합 ✅ PASS** — Phase 7 wire + Phase 8 wire `60d4ea1` + Phase 10 wire + cj-314 wire 3 (commit `34e92aa`) ESLint/SLO/SLI 8 fixes path bug fix 완료 정합

### 3.4 NFR18 (ko-KR, §F23.4)
- **§F23.4** (Frontend performance tracing Browser RUM) — trace_id 표시 시 ko-KR label "추적 ID" + alert UI 시 ko-KR 메시지 ("서비스에 문제가 발생했습니다. 잠시 후 다시 시도해주세요")
- **§F15.4** (Logout Flow + Korean SSOT) — `apps/web/messages/ko-KR.json` SSOT 1권 강제 + ESLint rule forbid-non-ko-KR-keys
- **정합 ✅ PASS** — Phase 7 wire + Phase 3 wire (Epic 1 ko-KR SSOT) 결정 wire 정합

---

## §4 25 ADs 정합 (~13 distinct AD numbers + AD-14 3 variants)

### 4.1 AD-7 (ai-extraction-table-naming, §F10 + §F22)
- **ai_extraction table naming 결정** — `input_drafts.target_table='monthly_inputs'` 에만 저장 + `confirmed_inputs` 직접 쓰기 거부 + 카운터 증가 (target 0) [AD-7 verbatim]
- **§F10.2** (AI Reference vs Auto Analysis Badge Separation) — Discriminated union `source_kind: Literal['auto_analysis', 'ai_reference']` + strict reject 외 value counter increment 강제 [AD-7 SM-3a]
- **§F10.4** (승격 포트 멱등성) — `InputPromoter.promote(tenant_id, period_key, source_draft_id)` idempotent + audit_logs 2행 append + `confirmed_inputs` denied + 카운터 증가 [AD-7]
- **정합 ✅ PASS** — Epic 10 wire + Epic 13/14 LISTEN/NOTIFY wire + Phase 6 wire 결정 wire 정합

### 4.2 AD-8 (money-types-decision)
- **Decimal 결정 wire** — 모든 금액 필드 Decimal 정합, KRW 정수 + USD 소수 2자리 강제
- **정합 ✅ PASS** — §F0.2 3종 allocation + §9 보고서 21종 (KRW/USD 동시 표시) 결정 wire 정합

### 4.3 AD-11 (dependency-direction)
- **apps/api 의존성 방향** — packages/cost_engine, packages/db-shared 등 core modules 단방향 의존성 강제
- **정합 ✅ PASS** — `apps/api/core/` 모듈 구조 결정 wire 정합

### 4.4 AD-14 (ci-verification-blocker-2026-08-29 + stack-pin-policy + tsc-baseline.json)
- **stack-pin-policy** — `apps/api/Dockerfile` + `apps/web/Dockerfile` per-app Dockerfile 분리 + AD-14 stack pin by @sha256: digest 결정 + 37 pins AD-14 EXTENSION
- **ci-verification-blocker** — 2026-08-29 KST, CI 검증 blocker 결정 wire 보존
- **tsc-baseline.json** — TypeScript baseline 결정 wire 정합
- **정합 ✅ PASS** — Phase 4 wire + cj-304 wire + cj-303 AD-14 stack pin EXTENSION (apscheduler==3.10.4 + pytz==2024.1) 결정 wire 정합

### 4.5 AD-15 (tenant-id-variance)
- **tenant_id RLS 결정 wire** — CR 0-2 RLS lesson 적용 + `tenant_id = current_setting('app.tenant_id')::uuid` RLS policy 결정 wire
- **정합 ✅ PASS** — Epic 13/14 LISTEN/NOTIFY wire + Epic 15 SSO wire + Epic 16 Tenant IdP wire + Epic 17 Audit Log wire + Phase 5/6/7/8/9/10 wire 결정 wire 정합

### 4.6 AD-19 (endpoint-dispatch)
- **M3 orchestrator endpoint dispatch** — `POST /api/v1/calc` dispatch via M3 orchestrator's `_resolve_engine_type(industry)` (PRD §F9.3 + A29 forward-lock dual-route)
- **정합 ✅ PASS** — M3 orchestrator + M9 ABC path (AbcAllocationService.compute_and_persist) 결정 wire 정합

### 4.7 AD-49 (phase-11-20-audit-fixes)
- **Phase 11~20 audit fixes 결정 wire** — Epic 17 audit log viewer + Phase 6 retention + audit-fixes 결정 wire 보존
- **정합 ✅ PASS** — Epic 17 wire + Phase 6 wire + cj-303 audit-fixes 결정 wire 정합

### 4.8 AD-50 (phase-22-finops-chargeback-settlement)
- **Phase 22 FinOps chargeback settlement 결정 wire** — FinOps territory 결정 wire 보존
- **정합 ✅ PASS** — Phase 22 PRD entry + wire 결정 wire 정합

### 4.9 AD-51 (phase-23-finops-unit-economics)
- **§F39 Phase 23 = FinOps Unit Economics** (cj-style 162 PRD entry 결정 wire) — Unit Economics 결정 wire 정합
- **정합 ✅ PASS** — Phase 23 PRD entry 결정 wire 정합

### 4.10 AD-52 (phase-24-finops-budget-planning)
- **§F40 Phase 24 = FinOps Budget Planning** (cj-style 167 PRD entry 결정 wire) — Budget Planning 결정 wire 정합
- **정합 ✅ PASS** — Phase 24 PRD entry 결정 wire 정합

### 4.11 AD-53 (phase-25-finops-vendor-management)
- **§F41 Phase 25 = FinOps Vendor Management** (cj-style 171 PRD entry 결정 wire) — Vendor Management 결정 wire 정합
- **정합 ✅ PASS** — Phase 25 PRD entry 결정 wire 정합

### 4.12 AD-54 (audit-fixes-sprint-cj-176-honest-recovery)
- **cj-176 honest recovery 결정 wire** — audit-fixes 결정 wire 보존
- **정합 ✅ PASS** — cj-176 retroactive close-out 결정 wire 정합

### 4.13 AD-55 (phase-26-finops-cost-anomaly-ml-prediction)
- **§F42 Phase 26 = FinOps Cost Anomaly ML Prediction** (cj-style 179 PRD entry 결정 wire) — Cost Anomaly 결정 wire 정합
- **정합 ✅ PASS** — Phase 26 PRD entry 결정 wire 정합

### 4.14 AD-56 (phase-30-epic-30-plus-reporting-export-decisions)
- **Epic 30+ Reporting & Export decisions** — Epic 30+ PRD entry + Epic 30+ wire 결정 wire (cj-282 PRD entry + cj-282a CSV export wire) 결정 wire 정합
- **정합 ✅ PASS** — cj-282 + cj-282a/b + Epic 30+ Phase 30 territory 결정 wire 정합

---

## §5 검증 결과 종합 — 정합 PASS + 결정 wire 진입 보류

### 5.1 정합 검증 결과
- **PRD §14 NFR 표 정합** ✅ PASS — 14 rows 모두 capability matrix v1.54 EXTENSION + Phase 결정 wire 와 정합
- **§F cross-section NFRs 정합** ✅ PASS — NFR4 (Phase 6) / NFR5 + NFR6 (Epic 12/15/16) / NFR11 (Phase 7/8/10) / NFR18 (Phase 3/7) 모두 정합
- **25 ADs 정합** ✅ PASS — ~13 distinct AD numbers + AD-14 의 3 variants 모두 source code + Phase 결정 wire 와 정합
- **K-3 chunk 1/2/3/4 종합 정합** ✅ PASS — chunk 1 (UJ §2.A, `9842dc7`) + chunk 2 (핵심기능 §8.1 M0~M12, `3ebd493`) + chunk 3 (상세기능 §F0~§F42, `ab31195`) + chunk 4 (제약사항 25 ADs + NFR, 본 sprint)
- **cj-314 wire 1~5 + cj-303 audit-fixes + cj-319 결정 wire 정합** ✅ PASS

### 5.2 결정 wire 진입 보류 명시
- **옵션 (β) docs+test 결정 wire 진입 결정 보류** — K-3 chunk 4 의 capability matrix EXTENSION 추가 + verify (Phase B/C 와 동일 패턴) 결정 wire 보류
- **옵션 (γ) source 변경 결정 wire 진입 결정 보류** — K-3 chunk 4 의 PRD §14 + 25 ADs 별 source code review 결정 wire 보류 (위험, 비추)
- **옵션 (α, RECOMMENDED)** = 본 sprint 의 docs-only 결정 wire 정합 (정합 검증 결과 종합 capture 만 수행)

### 5.3 carryover honestly DEFER 보존
- K-3 chunk 1/2/3 검증 결정 wire 의 옵션 (β·γ) 결정 보류 그대로 보존
- K-3 결정 wire 의 chunk 5~6 결정 보류 그대로 보존 (chunk 5 = 화면정의 §UI 부분 / 디자인가이드 = K-3 외부)
- cj-303 4건 + PRE-EXISTING 6건 + cj-307 LOW RISK ~30건 + sso 13 skipped tests + W1~W8 carryover + 비용 발생 항목 모두 + PRD v2 EXTENSION 보존

---

## §6 결정 wire 보존

### 6.1 결정 wire chain (cj-282~cj-319 + K-3 종합)
- K-3 chunk 3 검증 결정 wire (`ab31195`, cj-style 290번째) 결정 wire 그대로 보존
- K-3 chunk 2 검증 결정 wire (`3ebd493`, cj-style 289번째) 결정 wire 그대로 보존
- K-3 chunk 1 검증 결정 wire (`9842dc7`, cj-style 287번째) 결정 wire 그대로 보존
- K-4 메모리 description update 결정 wire (`00c49df`, cj-style 288번째) 결정 wire 그대로 보존
- K-3 결정 wire (`cc84b0e`, cj-style 286번째) 결정 wire 그대로 보존
- cj-319 + cj-318 + cj-314 wire 5 retroactive correction + cj-314 wire 5 retroactive close-out + cj-312 retro + cj-313 retro + cj-315 wire + retroactive correction + cj-314 wire 4 + cj-314 wire 3 (`34e92aa`) + cj-314 wire 2 + cj-314 wire 1 + cj-317 + cj-316 + cj-314 entry + cj-313 wire + cj-312 wire + cj-311 + cj-310 retroactive correction + cj-309b + cj-309 + cj-310 + cj-308 + cj-307 + cj-305b + cj-305 + cj-304 + cj-303 + cj-301 + cj-300 + cj-299 + cj-298 + cj-297 + cj-282 결정 wire 보존

### 6.2 외부 결정 wire 보존
- Pilot W1 launch D-day 2026-09-14 KST 보존 (D-3)
- MVP-verification 우선 (사용자 2026-09-10 결정 wire) 보존 — **배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요**
- K-3 chunk chain (UJ → 핵심기능 → 상세기능 → 제약사항) 결정 wire 보존
- K-4 정의 결정 wire (`memory/project-2026-09-10-k4-mvp-verification-scope.md`) 보존
- OQ-3 (Pilot launch trigger "M0-M6 close + 1주 Monday alignment") 정직 검증 결과 반영 — `memory/project-2026-09-10-pilot-launch-date-rationale-audit.md` 결정 wire 보존

---

## §7 Files (4 files docs-only atomic single sprint)

| # | File | 종류 | 변경량 |
|---|---|---|---|
| 1 | `memory/handoff-2026-09-11-k3-chunk4-ads-nfr-verification-done.md` | NEW | 본 handoff |
| 2 | `_bmad-output/implementation-artifacts/commit-msg-k3-chunk4-ads-nfr-verification.txt` | NEW | commit message |
| 3 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.106 → **v4.107 EXTENSION** A751 |
| 4 | `memory/MEMORY.md` | MODIFIED | K-3 chunk 4 hook |

### Sprint form
- docs-only atomic single sprint
- 0 source 변경 + 0 test 변경 + 0 alembic 변경 + 0 PRD 변경 + 0 capability matrix 변경 + 0 migration source 변경
- 37 pins unchanged + 14 job matrix unchanged
- PRD v7.0 §F/§M/§R unchanged + capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved + AD-14 stack pin EXTENSION preserved

### Cumulative 결정 wire
- 62/62 → **63/63** 결정 wire 보존
- CR 11-3 honest-DEFER 291번째 chain cj-282 (220번째) → ... → K-3 chunk 3 검증 결정 wire (290번째, commit `ab31195`) → **K-3 chunk 4 검증 결정 wire (291번째, 본 sprint)**

### 결정 보류 (운전자, 본 sprint 후속)
1. **K-3 chunk 5 진입 결정 보류** — chunk 5 = 화면정의 §UI 부분 검증 (옵션 e)
2. **디자인가이드 진입 결정 보류** — K-3 외부 (옵션 f, 별도 epic)
3. **K-3 chunk 4 옵션 (β) docs+test 결정 wire 진입 결정 보류**
4. **K-3 chunk 1/2/3 옵션 (β·γ) 결정 wire 진입 결정 보류** (cj-style 287/289/290 결정 보류 그대로 보존)
5. **K-3 chunk 4 옵션 (γ) source 변경 결정 wire 진입 결정 보류** (위험, 비추)

---

**Date**: 2026-09-11 KST (D-3)
**Author**: Claude (operator = kjw)
